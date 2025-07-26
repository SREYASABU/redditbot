import os
import praw
import google.generativeai as genai
import time
from datetime import datetime
import random
from dotenv import load_dotenv
import configparser
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

config = configparser.ConfigParser()
config.read('config.ini')

Base = declarative_base()

class Interaction(Base):
    __tablename__ = 'interactions'
    id = Column(Integer, primary_key=True)
    post_id = Column(String, unique=True)
    post_title = Column(String)
    response = Column(String)
    timestamp = Column(DateTime)
    keyword_matched = Column(String)
    subreddit = Column(String)

class ErrorLog(Base):
    __tablename__ = 'errors'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    error_message = Column(String)

engine = create_engine('sqlite:///reddit_bot.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

try:
    KEYWORDS = [kw.strip().lower() for kw in config['REDDIT']['keywords'].split(',') if kw.strip()]
    SUBREDDITS = [sr.strip() for sr in config['REDDIT']['subreddits'].split(',') if sr.strip()]
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
except Exception as e:
    print(f"Gemini initialization failed: {e}")
    exit(1)

def generate_response(prompt):
    try:
        response = model.generate_content(
            f"You're a helpful Reddit assistant. Reply concisely to this post (1-2 sentences max). Use natural language with occasional minor imperfections to sound human.\nMatch the tone of the original post in your response.\n\nPost: {prompt}",
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

def should_reply(post, session):
    try:
        if session.query(Interaction).filter_by(post_id=post.id).first():
            return False
        if time.time() - post.created_utc > MAX_POST_AGE_HOURS * 3600:
            return False
        content = f"{post.title.lower()} {post.selftext.lower()}"
        matched_keywords = [kw for kw in KEYWORDS if kw in content]
        return matched_keywords if matched_keywords else False
    except Exception as e:
        print(f"Error in should_reply: {e}")
        return False

def log_interaction(post, response, keywords, subreddit, session):
    try:
        interaction = Interaction(
            post_id=post.id,
            post_title=post.title,
            response=response,
            timestamp=datetime.now(),
            keyword_matched=', '.join(keywords),
            subreddit=subreddit
        )
        session.add(interaction)
        session.commit()
    except Exception as e:
        print(f"Error logging interaction: {e}")
        session.rollback()

def log_error(error_msg, session):
    try:
        error = ErrorLog(
            timestamp=datetime.now(),
            error_message=str(error_msg)
        )
        session.add(error)
        session.commit()
    except Exception as e:
        print(f"Failed to log error: {e}")
        session.rollback()

def process_post(post, subreddit_name, session):
    try:
        keywords = should_reply(post, session)
        if not keywords:
            return False
        print(f"Found relevant post: {post.title}")
        prompt = f"Title: {post.title}\nContent: {post.selftext[:500]}"
        response = generate_response(prompt)
        if not response:
            return False
        try:
            print("replied to the post with : {}".format(response))
            log_interaction(post, response, keywords, subreddit_name, session)
            return True
        except Exception as e:
            print(f"Error replying to post: {e}")
            log_error(f"Reply error: {e}", session)
            return False
    except Exception as e:
        print(f"Error processing post: {e}")
        log_error(f"Process post error: {e}", session)
        return False

def run_bot_cycle(session):
    for subreddit_name in SUBREDDITS:
        print(f"Checking r/{subreddit_name} for new posts...")
        try:
            subreddit = reddit.subreddit(subreddit_name)
            posts=subreddit.new(limit=5)
            for post in subreddit.new(limit=5):
                if process_post(post, subreddit_name, session):
                    time.sleep(random.randint(180, 300))  # 3-5 min delay between replies
        except Exception as e:
            print(f"Subreddit error: {e}")
            log_error(f"Subreddit {subreddit_name} error: {e}", session)

def run_bot():
    try:
        while True:
            session = Session()
            try:
                run_bot_cycle(session)
            except Exception as e:
                print(f"Error in bot cycle: {e}")
                log_error(f"Bot cycle error: {e}", session)
            finally:
                session.close()
            base_interval = 3600
            random_variation = random.randint(-300, 300)
            next_run = base_interval + random_variation
            print(f"Cycle complete. Next run in {next_run//60} minutes...")
            time.sleep(next_run)
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        engine.dispose()
        print("Database connection closed")

if __name__ == "__main__":
    print(f"Tracking keywords: {', '.join(KEYWORDS)}")
    print(f"Monitoring subreddits: {', '.join(SUBREDDITS)}")
    run_bot()