# Reddit Bot with Gemini AI

A Reddit bot that uses Google's Gemini AI to generate human-like responses to posts in specified subreddits.

## Features
- Monitors specified subreddits for new posts
- Uses Gemini AI to generate context-aware responses
- Implements rate limiting and safety measures
- Logs all interactions to a local database

## Setup
1. Install requirements:
   ```
   pip install -r requirements.txt
   ```
2. Create a `.env` file with your credentials:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USERNAME=your_username
   REDDIT_PASSWORD=your_password
   GEMINI_API_KEY=your_gemini_api_key
   ```

## Usage
Run the bot:
```
python bot.py
```

The bot will automatically monitor the subreddits specified in the configuration and respond to relevant posts.

## Configuration
Edit `config.ini` to customize:
- Subreddits to monitor
- Keywords to track
- Response behavior
- Safety settings