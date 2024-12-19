import discord
import tweepy
import requests
import os
import asyncio
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

# Keep your existing fetch_images_from_user function
async def fetch_images_from_user(username, count=10, output_folder="images", discord_channel=None):
    # Your existing function code here...
    pass

@discord_client.event
async def on_ready():
    print(f'We have logged in as {discord_client.user}')

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    if message.content.startswith('!scrapeTweets'):
        username = message.content.split(' ')[1]
        await message.channel.send(f"Scraping tweets for @{username}...")
        await fetch_images_from_user(username, discord_channel=message.channel)
        await message.channel.send(f"Scraping completed for @{username}.")

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