#  Film Marketing Post Generator

**AI-Powered Social Media Content Assistant for Movie Promotions**

[Live Demo](YOUR_DEPLOYMENT_URL_HERE) | [GitHub Repository](YOUR_GITHUB_URL_HERE)

---

##  Product Brief

**Problem:** Film marketers need to create engaging social media content across multiple platforms quickly and consistently. Each platform has different character limits, tone expectations, and audience behaviors. Creating unique, platform-optimized posts for every movie campaign is time-consuming and requires careful attention to brand voice and platform best practices.

**Target User:** Film marketing professionals, social media managers in entertainment industry, indie filmmakers, and content creators promoting films across social platforms.

**Solution:** This AI-powered tool generates platform-specific social media posts tailored to your film's unique characteristics. Users input basic information (movie title, description, tone) and receive ready-to-post content optimized for Instagram, Twitter/X, Facebook, LinkedIn, or TikTok. The tool understands platform nuances from Instagram's hashtag culture to Twitter's character limits to LinkedIn's professional tone.

**Effectiveness:** By automating the initial content creation process, marketers save 70-80% of the time typically spent drafting posts. The AI generates multiple variations quickly, allowing teams to A/B test different approaches. Platform-specific optimization ensures content follows best practices for engagement, increasing the likelihood of shares, comments, and conversions.

---

##  How to Use

**Basic Usage:**
1. **Enter Movie Title** - Input the name of your film
2. **Describe Your Film** - Provide a brief description, key themes, or marketing angles
3. **Select Platform** - Choose from Instagram, Twitter/X, Facebook, LinkedIn, or TikTok
4. **Choose Tone** - Select the desired emotional tone (exciting, mysterious, emotional, professional, or humorous)
5. **Add Context (Optional)** - Include release dates, cast names, awards, or special events
6. **Generate** - Click "Generate Post" and wait 2-3 seconds
7. **Copy & Use** - Review the generated post and copy it to your clipboard with one click

**Tips for Best Results:**
- Be specific in your film description and mention genre, key themes, or unique selling points
- Include release dates and notable cast/crew in the additional context field
- Try different tones to see what resonates best with your target audience
- Regenerate multiple times to get variations and choose the best one

---

##  Tech Stack

**AI API:**
- **OpenAI GPT-4o-mini**
- *Why GPT-4o-mini?* Cost-effective ($0.15 per 1M input tokens), fast response times, excellent creative writing capabilities, and optimized for chat-based applications

**Alternative:** Anthropic Claude API (code supports both - just change the `API_PROVIDER` variable)

**AI Coding Assistant:**
- **Claude AI** (claude.ai)
- Used for generating initial HTML structure, styling, API integration code, and documentation

**Frontend Technologies:**
- HTML5 - Semantic structure
- CSS3 - Responsive design with flexbox/grid, modern gradients and animations
- Vanilla JavaScript - Form handling, API calls, DOM manipulation

**Deployment:**
- **GitHub Pages** (recommended)
- Alternatives: Vercel, Netlify

**Development Tools:**
- Visual Studio Code / Cursor
- Git for version control
- GitHub for repository hosting

---

##  Reflection

**What Worked Well:**

Using AI assistance dramatically accelerated development. Claude generated a clean, responsive HTML/CSS structure in minutes that would have taken hours to build from scratch. The API integration code was particularly helpful - it handled error states, loading animations, and user feedback automatically. The AI also suggested UX improvements I hadn't considered, like the copy-to-clipboard button and platform-specific prompt engineering. The gradient color scheme and animations gave the tool a professional, polished appearance without deep CSS knowledge.

**What Was Challenging:**

The most challenging aspect was ensuring API key security. AI initially hardcoded the key directly in the HTML, which is a security risk. I had to research proper practices and understand that for a client-side application, some exposure is inevitable - proper production apps need backend servers. Understanding how to structure prompts for consistent, high-quality output across different film types took iteration. The AI sometimes generated overly verbose code that needed simplification. Testing across different platforms revealed edge cases (like very long movie titles) that needed CSS adjustments.

**Version 2.0 Improvements:**

- **Backend Integration:** Move API calls to a secure server-side function to protect API keys
- **Multiple Variations:** Generate 3-5 post options simultaneously so users can choose the best
- **Save & Export:** Allow users to save favorite posts and export to CSV for campaign planning
- **Analytics Integration:** Track which generated posts perform best when posted
- **Template Library:** Pre-built templates for common film genres (horror, comedy, drama, etc.)
- **Image Suggestions:** Recommend image types or compositions to pair with generated text
- **Scheduling Integration:** Direct integration with Buffer, Hootsuite, or Meta Business Suite
- **Multi-language Support:** Generate posts in different languages for international campaigns
- **Character Counter:** Real-time character count with platform limits displayed
- **Emoji Suggestions:** Smart emoji recommendations based on tone and platform

---

##  Important Notes

**API Key Security:**
- Never commit your API key to a public repository
- Add `index.html` to `.gitignore` if it contains your key
- For production use, implement a backend server to secure API calls
- Consider environment variables or serverless functions (Vercel, Netlify Functions)

**API Costs:**
- OpenAI GPT-4o-mini: ~$0.001-0.002 per post generation
- Free tier credits: New accounts get $5 in free credits
- Each post generation uses approximately 500-800 tokens

**Browser Compatibility:**
- Works in all modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled
- Internet connection required for API calls

---

##  License

This project is open source and available for educational purposes.

---

##  Author

**Carlton Shi**  
Web Designer | Film Marketing Specialist

*Created for Advanced Web Design course - Syracuse University*

---

##  Acknowledgments

- Built with assistance from Claude AI (Anthropic)
- Powered by OpenAI API
- Design inspiration from modern SaaS applications
- Thanks to the film marketing community for feature suggestions
