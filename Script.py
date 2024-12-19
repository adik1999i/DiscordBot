import discord
import tweepy
import requests
import os
import asyncio
import io
from dotenv import load_dotenv
from flask import Flask

load_dotenv()
# Load secrets from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
PORT = int(os.getenv("PORT", 8080))

# Initialize Flask app
app = Flask(__name__)

# Twitter authentication
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Initialize Discord Client
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# Updated function to handle files in memory
async def fetch_images_from_user(username, count=10, discord_channel=None):
    try:
        # Get user details
        user = client.get_user(username=username)
        if not user.data:
            await discord_channel.send(f"Could not find user @{username}")
            return
            
        user_id = user.data.id
        
        # Fetch recent tweets
        tweets = client.get_users_tweets(
            id=user_id,
            tweet_fields=["attachments", "entities", "text"],
            expansions=["attachments.media_keys"],
            media_fields=["url"],
            max_results=count,
        )

        if not tweets.data:
            await discord_channel.send(f"No tweets found for user @{username}")
            return

        media_mapping = {}
        if tweets.includes and "media" in tweets.includes:
            media_mapping = {media["media_key"]: media for media in tweets.includes["media"]}

        image_count = 0

        # Process each tweet
        for tweet in tweets.data:
            try:
                # Check if tweet contains the hashtag #DBLegends
                if "#DBLegends" in tweet.text:
                    print(f"Found tweet with #DBLegends: {tweet.text}")
                    
                    # Send the tweet text directly to Discord
                    await discord_channel.send(f"Tweet from @{username}:\n{tweet.text}")

                    # If tweet has images
                    if hasattr(tweet, 'attachments') and tweet.attachments and "media_keys" in tweet.attachments:
                        for media_key in tweet.attachments["media_keys"]:
                            media = media_mapping.get(media_key)
                            if media and media["type"] == "photo":
                                image_url = media["url"]
                                print(f"Downloading image: {image_url}")

                                # Download image
                                response = requests.get(image_url)
                                if response.status_code == 200:
                                    # Create file-like object in memory
                                    image_data = io.BytesIO(response.content)
                                    # Send directly to Discord
                                    discord_file = discord.File(
                                        fp=image_data,
                                        filename=f"{username}_{tweet.id}_{image_count}.jpg"
                                    )
                                    await discord_channel.send(file=discord_file)
                                    image_count += 1

                    await asyncio.sleep(1)  # Add small delay between processing tweets
                    
            except Exception as tweet_error:
                print(f"Error processing tweet: {tweet_error}")
                continue

        await discord_channel.send(f"Found and processed {image_count} images from tweets with #DBLegends.")

    except tweepy.TooManyRequests:
        await discord_channel.send("Rate limit exceeded. Please try again later.")
        
    except Exception as e:
        print(f"Error: {e}")
        await discord_channel.send(f"An error occurred while fetching tweets: {str(e)}")

@discord_client.event
async def on_ready():
    print(f'We have logged in as {discord_client.user}')

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    if message.content.startswith('!scrapeTweets'):
        try:
            username = message.content.split(' ')[1]
            await message.channel.send(f"Scraping tweets for @{username}...")
            await fetch_images_from_user(username, discord_channel=message.channel)
        except Exception as e:
            await message.channel.send(f"An error occurred: {str(e)}")

# Add Flask routes to keep the service alive
@app.route('/')
def home():
    return 'Discord Bot is running!'

@app.route('/health')
def health():
    return 'OK', 200

def run_discord_bot():
    discord_client.run(DISCORD_TOKEN)

if __name__ == '__main__':
    # Run Discord bot in a separate thread
    import threading
    bot_thread = threading.Thread(target=run_discord_bot)
    bot_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=PORT)