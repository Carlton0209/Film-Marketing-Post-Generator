# Movie Promo Lab

Standalone local toolkit for film promotion research.

It collects public movie-studio promo text from compliant sources such as RSS and public YouTube channel feeds, imports official platform/API CSV exports, analyzes reusable marketing patterns, and drafts original promotional copy without copying studio slogans.

## Quick Start

```powershell
python movie_promo_lab.py init-sources
python movie_promo_lab.py collect --sources data\sources.starter.json --db data\promo.sqlite
python movie_promo_lab.py analyze --db data\promo.sqlite --out reports\style_playbook.md
python movie_promo_lab.py draft --title "午夜放映" --genre "悬疑惊悚" --logline "一名放映员发现每卷胶片都在预告现实中的下一起失踪案。" --audience "年轻类型片观众"
```

## Data Notes

- Instagram, TikTok, X, and Facebook are listed as manual/API export sources because stable collection usually requires official platform access.
- The tool stores local data in SQLite and keeps generated reports local by default.
- Use it to learn structure and tactics, not to reproduce copyrighted captions or brand-specific wording.

## Included

- `movie_promo_lab.py`: single-file runnable version.
- Built-in starter source list covering major studios, mini-majors, streamers, and specialty labels.
- Commands for source initialization, collection, CSV import, analysis, and drafting.
