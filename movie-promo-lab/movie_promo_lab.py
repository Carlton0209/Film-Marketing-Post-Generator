from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sqlite3
import statistics
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


USER_AGENT = "MoviePromoLab/standalone (+local research tool)"
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'_/-]*|#[A-Za-z0-9_]+|@[\w_]+|[\u4e00-\u9fff]+")
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")

CTA_PATTERNS = {
    "ticket_push": ["tickets", "get tickets", "book now", "on sale", "reserve"],
    "watch_now": ["watch", "stream", "now playing", "starts streaming", "only on"],
    "trailer_focus": ["trailer", "teaser", "official trailer", "new trailer"],
    "release_window": ["in theaters", "this friday", "tomorrow", "coming soon", "premieres", "opens"],
    "fandom_signal": ["fans", "universe", "chapter", "returns", "exclusive", "behind the scenes"],
    "social_proof": ["winner", "nominated", "critics", "review", "audiences", "award"],
}


@dataclass(frozen=True)
class Post:
    company: str
    platform: str
    source_type: str
    text: str
    url: str = ""
    title: str = ""
    published_at: str = ""
    campaign: str = ""


SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    platform TEXT NOT NULL,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    published_at TEXT NOT NULL DEFAULT '',
    campaign TEXT NOT NULL DEFAULT '',
    text_hash TEXT NOT NULL,
    inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company, platform, url, text_hash)
);
CREATE INDEX IF NOT EXISTS idx_posts_company ON posts(company);
CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
"""


STARTER_SOURCES = [
    ("Walt Disney Animation Studios", "YouTube", "youtube_channel", "https://www.youtube.com/@disneyanimation"),
    ("Walt Disney Studios", "Instagram", "manual_export", "https://www.instagram.com/disneystudios/"),
    ("Pixar", "YouTube", "youtube_channel", "https://www.youtube.com/@pixar"),
    ("Marvel Studios", "YouTube", "youtube_channel", "https://www.youtube.com/@marvel"),
    ("20th Century Studios", "YouTube", "youtube_channel", "https://www.youtube.com/@20thCenturyStudios"),
    ("Searchlight Pictures", "YouTube", "youtube_channel", "https://www.youtube.com/@SearchlightPictures"),
    ("Warner Bros. Pictures", "YouTube", "youtube_channel", "https://www.youtube.com/user/WarnerBrosPictures"),
    ("Universal Pictures", "YouTube", "youtube_channel", "https://www.youtube.com/@UniversalPictures"),
    ("Focus Features", "YouTube", "youtube_channel", "https://www.youtube.com/@FocusFeatures"),
    ("DreamWorks Animation", "YouTube", "youtube_channel", "https://www.youtube.com/@dreamworks"),
    ("Illumination", "YouTube", "youtube_channel", "https://www.youtube.com/@illumination"),
    ("Paramount Pictures", "YouTube", "youtube_channel", "https://www.youtube.com/@paramountpictures"),
    ("Sony Pictures", "YouTube", "youtube_channel", "https://www.youtube.com/@sonypictures"),
    ("Sony Pictures Animation", "YouTube", "youtube_channel", "https://www.youtube.com/@SonyAnimation"),
    ("Lionsgate", "YouTube", "youtube_channel", "https://www.youtube.com/@LionsgateMovies"),
    ("A24", "YouTube", "youtube_channel", "https://www.youtube.com/@A24"),
    ("NEON", "YouTube", "youtube_channel", "https://www.youtube.com/@neonrated"),
    ("Netflix Film", "YouTube", "youtube_channel", "https://www.youtube.com/@Netflix"),
    ("Amazon MGM Studios", "Instagram", "manual_export", "https://www.instagram.com/amazonmgmstudios/"),
    ("Apple Original Films", "Instagram", "manual_export", "https://www.instagram.com/applefilms/"),
    ("Blumhouse", "YouTube", "youtube_channel", "https://www.youtube.com/@Blumhouse"),
    ("MUBI", "Instagram", "manual_export", "https://www.instagram.com/mubi/"),
    ("STUDIOCANAL", "YouTube", "youtube_channel", "https://www.youtube.com/@studiocanal"),
]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = TAG_RE.sub(" ", value)
    return SPACE_RE.sub(" ", value).strip()


def connect(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def fetch_url(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            encoding = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(encoding, errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc.reason}") from exc


def resolve_youtube_feed(url: str) -> str:
    if "feeds/videos.xml" in url:
        return url
    page = fetch_url(url)
    rss_match = re.search(r'"rssUrl":"(https://www\.youtube\.com/feeds/videos\.xml\?channel_id=[^"]+)"', page)
    if rss_match:
        return rss_match.group(1)
    ext_match = re.search(r'"externalId":"(UC[^"]+)"', page)
    if ext_match:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={ext_match.group(1)}"
    channel_match = re.search(r'"channelId":"(UC[^"]+)"', page)
    if channel_match:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_match.group(1)}"
    raise RuntimeError(f"Could not resolve YouTube RSS feed for {url}")


def collect_rss(url: str, company: str, platform: str, source_type: str) -> list[Post]:
    root = ET.fromstring(fetch_url(url))
    ns = {"atom": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/"}
    posts: list[Post] = []
    for entry in root.findall(".//atom:entry", ns):
        title = child_text(entry, "atom:title", ns)
        summary = child_text(entry, "atom:summary", ns)
        media_description = child_text(entry, "media:group/media:description", ns)
        link_node = entry.find("atom:link[@rel='alternate']", ns) or entry.find("atom:link", ns)
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        posts.append(Post(company, platform, source_type, media_description or summary or title, link, title, child_text(entry, "atom:updated", ns)))
    for item in root.findall(".//item"):
        title = child_text(item, "title")
        description = child_text(item, "description")
        posts.append(Post(company, platform, source_type, description or title, child_text(item, "link"), title, child_text(item, "pubDate")))
    return [post for post in posts if clean_text(post.text)]


def child_text(node: ET.Element, path: str, ns: dict[str, str] | None = None) -> str:
    child = node.find(path, ns or {})
    return child.text if child is not None and child.text else ""


def insert_posts(conn: sqlite3.Connection, posts: list[Post]) -> int:
    inserted = 0
    for post in posts:
        text = clean_text(post.text)
        if not text:
            continue
        before = conn.total_changes
        conn.execute(
            """
            INSERT OR IGNORE INTO posts
                (company, platform, source_type, title, text, url, published_at, campaign, text_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post.company,
                post.platform,
                post.source_type,
                clean_text(post.title),
                text,
                post.url,
                post.published_at,
                post.campaign,
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
            ),
        )
        inserted += 1 if conn.total_changes > before else 0
    conn.commit()
    return inserted


def cmd_init_sources(args: argparse.Namespace) -> int:
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 1,
        "sources": [
            {"company": c, "platform": p, "source_type": t, "url": u, "enabled": True}
            for c, p, t, u in STARTER_SOURCES
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path}")
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    with open(args.sources, "r", encoding="utf-8") as handle:
        sources = json.load(handle)["sources"]
    conn = connect(args.db)
    total = 0
    for index, source in enumerate(sources, 1):
        if not source.get("enabled", True):
            continue
        label = f"{source['company']} / {source['platform']} / {source['source_type']}"
        try:
            if source["source_type"] == "youtube_channel":
                posts = collect_rss(resolve_youtube_feed(source["url"]), source["company"], source["platform"], source["source_type"])
                inserted = insert_posts(conn, posts)
                total += inserted
                print(f"[{index}] {label}: {inserted} new")
            elif source["source_type"] == "rss":
                posts = collect_rss(source["url"], source["company"], source["platform"], source["source_type"])
                inserted = insert_posts(conn, posts)
                total += inserted
                print(f"[{index}] {label}: {inserted} new")
            else:
                print(f"[{index}] {label}: import exported posts with import-csv")
        except Exception as exc:
            print(f"[{index}] {label}: skipped - {exc}")
    conn.close()
    print(f"Done. Inserted {total} new posts.")
    return 0


def cmd_import_csv(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    posts: list[Post] = []
    with open(args.csv, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            posts.append(Post(row.get("company", ""), row.get("platform", ""), row.get("source_type", "csv_import"), row.get("text", ""), row.get("url", ""), row.get("title", ""), row.get("published_at", ""), row.get("campaign", "")))
    print(f"Imported {insert_posts(conn, posts)} new posts.")
    conn.close()
    return 0


def analyze_rows(rows: list[sqlite3.Row]) -> str:
    texts = [row["text"] for row in rows]
    companies = Counter(row["company"] for row in rows)
    platforms = Counter(row["platform"] for row in rows)
    lengths = [len(text) for text in texts]
    cta_hits = {key: 0 for key in CTA_PATTERNS}
    terms: Counter[str] = Counter()
    for text in texts:
        lowered = text.lower()
        for name, phrases in CTA_PATTERNS.items():
            if any(phrase in lowered for phrase in phrases):
                cta_hits[name] += 1
        terms.update(token.lower() for token in TOKEN_RE.findall(text) if len(token) > 2 and not token.startswith("@"))
    lines = [
        "# Movie Promo Style Playbook",
        "",
        f"- Posts analyzed: {len(texts)}",
        f"- Companies: {len(companies)}",
        f"- Platforms: {len(platforms)}",
        f"- Average length: {statistics.mean(lengths):.0f} characters" if lengths else "- Average length: 0 characters",
        "",
        "## Strong Patterns",
        "",
        "- Anchor posts around a clear release moment or viewing action.",
        "- Treat trailers as events and make the reveal easy to share.",
        "- Use review, festival, or audience signals as compact credibility.",
        "- Keep generated copy original; borrow structure, not wording.",
        "",
        "## CTA Signals",
        "",
    ]
    for name, count in sorted(cta_hits.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"- {name.replace('_', ' ').title()}: {count}")
    lines.extend(["", "## Top Terms", "", ", ".join(f"{term} ({count})" for term, count in terms.most_common(25)) or "No terms yet."])
    return "\n".join(lines) + "\n"


def cmd_analyze(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    rows = list(conn.execute("SELECT * FROM posts ORDER BY id DESC"))
    conn.close()
    report = analyze_rows(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"Wrote {out} ({len(rows)} posts analyzed).")
    return 0


def cmd_draft(args: argparse.Namespace) -> int:
    when = args.release_window or "即将上映"
    title = args.title
    genre = args.genre or "电影"
    audience = args.audience or "观众"
    logline = args.logline
    drafts = [
        f"{title}把{audience}带进一个{genre}的高压时刻：{logline}。{when}，准备入场。",
        f"有些秘密不该被放上银幕。{title}，{when}。看完预告，再决定你敢不敢坐到最后一排。",
        f"{logline}\n\n{title}，{when}。把这条发给那个总说自己猜得到结局的人。",
        f"灯暗下来，答案开始反噬每一个人。{title}以{genre}的方式打开一个无法回头的夜晚。{when}。",
    ]
    output = "\n\n".join(f"Option {i + 1}\n{draft}" for i, draft in enumerate(drafts[: args.count]))
    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(output)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    conn.close()
    print(f"Python: {sys.version.split()[0]}")
    print(f"Database: {args.db}")
    print(f"Posts: {count}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standalone local movie promotion research tool.")
    sub = parser.add_subparsers(required=True)
    init_sources = sub.add_parser("init-sources")
    init_sources.add_argument("--out", default="data/sources.starter.json")
    init_sources.set_defaults(func=cmd_init_sources)
    collect = sub.add_parser("collect")
    collect.add_argument("--sources", default="data/sources.starter.json")
    collect.add_argument("--db", default="data/promo.sqlite")
    collect.set_defaults(func=cmd_collect)
    import_csv_cmd = sub.add_parser("import-csv")
    import_csv_cmd.add_argument("--csv", required=True)
    import_csv_cmd.add_argument("--db", default="data/promo.sqlite")
    import_csv_cmd.set_defaults(func=cmd_import_csv)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--db", default="data/promo.sqlite")
    analyze.add_argument("--out", default="reports/style_playbook.md")
    analyze.set_defaults(func=cmd_analyze)
    draft = sub.add_parser("draft")
    draft.add_argument("--title", required=True)
    draft.add_argument("--logline", required=True)
    draft.add_argument("--genre", default="")
    draft.add_argument("--audience", default="")
    draft.add_argument("--release-window", default="")
    draft.add_argument("--count", type=int, default=4)
    draft.add_argument("--out", default="")
    draft.set_defaults(func=cmd_draft)
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--db", default="data/promo.sqlite")
    doctor.set_defaults(func=cmd_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
