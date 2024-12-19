import discord
import tweepy
import requests
import os
import asyncio
import io
from flask import Flask
from dotenv import load_dotenv

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

async def fetch_images_from_user(username, count=5, discord_channel=None):
    try:
        # Get user details
        user = client.get_user(username=username)
        if not user.data:
            await discord_channel.send(f"Could not find user @{username}")
            return
            
        user_id = user.data.id
        print(f"Found user ID: {user_id}")

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

        print(f"Found {len(tweets.data)} tweets")
        
        media_mapping = {}
        if tweets.includes and "media" in tweets.includes:
            media_mapping = {media["media_key"]: media for media in tweets.includes["media"]}

        image_count = 0

        # Process each tweet
        for tweet in tweets.data:
            # Check if tweet contains the hashtag #DBLegends
            if "#DBLegends" in tweet.text:
                print(f"Found tweet with #DBLegends: {tweet.text}")

                # Send the tweet text directly to Discord
                await discord_channel.send(f"Tweet Content:\n{tweet.text}")

                # If tweet has images
                if hasattr(tweet, 'attachments') and tweet.attachments and "media_keys" in tweet.attachments:
                    for media_key in tweet.attachments["media_keys"]:
                        media = media_mapping.get(media_key)
                        if media and media["type"] == "photo":
                            image_url = media["url"]
                            print(f"Downloading image: {image_url}")

                            # Download and send image directly to Discord
                            response = requests.get(image_url)
                            if response.status_code == 200:
                                image_data = io.BytesIO(response.content)
                                discord_file = discord.File(
                                    fp=image_data,
                                    filename=f"{username}_{tweet.id}_{image_count}.jpg"
                                )
                                await discord_channel.send(file=discord_file)
                                image_count += 1
                                print(f"Sent image {image_count} to Discord")

                await asyncio.sleep(1)  # Small delay between tweets

        print(f"Processed {image_count} images for tweets with #DBLegends")
        await discord_channel.send(f"Found and processed {image_count} images from tweets with #DBLegends.")

    except tweepy.TooManyRequests:
        await discord_channel.send("Rate limit exceeded. Please try again later.")
        print("Rate limit exceeded")
        
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(error_message)
        await discord_channel.send(error_message)

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

# Add Flask routes
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