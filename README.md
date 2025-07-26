# Reddit Bot with Gemini AI

A Reddit bot that uses Google's Gemini AI to generate human-like responses to posts in specified subreddits based on configured keywords.

## ✨ Features
- Monitors specified subreddits for new posts
- Uses Gemini AI to generate natural, context-aware responses
- Configurable keyword-based post filtering
- SQLite database for interaction logging
- Rate limiting and safety measures
- Randomized delay between cycles to appear more natural

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/redditbot.git
   cd redditbot
   ```

2. **Set up a virtual environment (recommended)**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your environment**
   - Copy `.env_example` to `.env`
   - Fill in your Reddit and Gemini API credentials
   - Adjust `config.ini` to set your preferred subreddits and keywords

5. **Run the bot**
   ```bash
   python bot.py
   ```
## 📊 Database
- The bot uses SQLite for storing interaction history
- Database file: `reddit_bot.db`
- Tables:
  - `interactions`: Logs all bot interactions
  - `errors`: Tracks any errors that occur

## ⚠️ Notes
- The bot includes rate limiting to comply with Reddit's API rules
- Monitor the bot's activity, especially when first deploying
- Be respectful of subreddit rules and Reddit's terms of service

## 🤝 Contributing
Feel free to submit issues and enhancement requests. Pull requests are welcome!