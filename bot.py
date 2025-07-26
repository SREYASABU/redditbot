import os
import praw
import google.generativeai as genai
import time
import sqlite3
from datetime import datetime
import random
from dotenv import load_dotenv
import configparser


load_dotenv()


config = configparser.ConfigParser()
config.read('config.ini')
try:
    KEYWORDS = [kw.strip().lower() for kw in config['REDDIT']['keywords'].split(',') if kw.strip()]
    SUBREDDITS = [sr.strip() for sr in config['REDDIT']['subreddits'].split(',') if sr.strip()]
    DELAY_BETWEEN_REPLIES = max(60, int(config['REDDIT'].get('delay_between_replies', '3600')))
    MAX_RESPONSE_LENGTH = min(200, max(50, int(config['BOT'].get('max_response_length', '150'))))
    TEMPERATURE = min(1.0, max(0.1, float(config['BOT'].get('temperature', '0.7'))))
    MAX_POST_AGE_HOURS = int(config['REDDIT'].get('max_post_age_hours', '4'))
except Exception as e:
    print(f"Configuration error: {e}")


try:
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT'),
        username=os.getenv('REDDIT_USERNAME'),
        password=os.getenv('REDDIT_PASSWORD')
    )
    print(f"Logged in as: {reddit.user.me()}")
except Exception as e:
    print(f"Reddit authentication failed: {e}")
    exit(1)


try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Gemini initialized successfully")
except Exception as e:
    print(f"Gemini initialization failed: {e}")
    exit(1)


def init_db():
    try:
        conn = sqlite3.connect('reddit_bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE,
                post_title TEXT,
                response TEXT,
                timestamp DATETIME,
                keyword_matched TEXT,
                subreddit TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                error_message TEXT
            )
        ''')
        conn.commit()
        return conn
    except Exception as e:
        print(f"Database initialization failed: {e}")
        exit(1)

conn = init_db()

def generate_response(prompt):
    try:
        response = model.generate_content(
            f"You're a helpful Reddit assistant. Reply concisely to this post (1-2 sentences max). "
            f"Use tricks like small typos to make it look more humanlike\n\n"
            f"Post: {prompt}",
            generation_config={
                "max_output_tokens": MAX_RESPONSE_LENGTH,
                "temperature": TEMPERATURE
            },
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        )
        return response.text if response and hasattr(response, 'text') else None
    except Exception as e:
        print(f"Error generating response: {e}")
        return None

def should_reply(post):
    try:

        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM interactions WHERE post_id = ?', (post.id,))
        if cursor.fetchone():
            return False
        
        content = f"{post.title.lower()} {post.selftext.lower()}"
        matched_keywords = [kw for kw in KEYWORDS if kw in content]
        return matched_keywords if matched_keywords else False
    except Exception as e:
        print(f"Error in should_reply: {e}")
        return False

def log_interaction(post, response, keywords, subreddit):
    """Log interaction to database"""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO interactions 
            (post_id, post_title, response, timestamp, keyword_matched, subreddit)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (post.id, post.title, response, datetime.now(), ', '.join(keywords), subreddit))
        conn.commit()
    except Exception as e:
        print(f"Error logging interaction: {e}")

def process_post(post, subreddit_name):
    try:
        keywords = should_reply(post)
        print(keywords)
        if not keywords:
            return False
            
        print(f"Found relevant post: {post.title}")
        
        # Generate response
        prompt = f"Title: {post.title}\nContent: {post.selftext[:500]}"
        response = generate_response(prompt)
        
        if not response:
            return False
            
        try:
    
            # post.reply(response)
            print(f"Reply: {response}")
            log_interaction(post, response, keywords, subreddit_name)
            return True

        except Exception as e:
            print(f"Error replying to post: {e}")
            return False
    except Exception as e:
        print(f"Error processing post: {e}")
        return False

def run_bot():
    try:
        while True:
            print(f"\n{datetime.now().isoformat()} - Starting bot cycle...")
            
            for subreddit_name in SUBREDDITS:
                print(f"Checking r/{subreddit_name} for new posts...")
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    for post in subreddit.new(limit=5):
                        print(post.title)
                        process_post(post, subreddit_name)
                except Exception as e:
                    print(f"Subreddit error: {e}")
            
            # the bot will run every hour with a random variation of 5 minutes
            base_interval = 3600  
            random_variation = random.randint(-300, 300)
            next_run = base_interval + random_variation
            time.sleep(next_run)
            
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    print("Starting Reddit bot with Gemini...")
    print(f"Tracking keywords: {', '.join(KEYWORDS)}")
    print(f"Monitoring subreddits: {', '.join(SUBREDDITS)}")
    run_bot()