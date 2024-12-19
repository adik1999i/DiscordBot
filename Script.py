import discord
import tweepy
import requests
import os
import time
import asyncio

# Discord Bot Token
DISCORD_TOKEN = 'MTMxMTIzODE2NjY1NjcxMjcyNQ.GQzr4k.mMdUcTUmgnTiLD7DQLjOkb5KxA2mBEHSXas9OQ'

# Replace with your Twitter API credentials
API_KEY = "JjAzcqm1mMJV2kdrgorJhCwtb"
API_SECRET = "gXRLIRBPED3e7ONApiHNrMmea36Bixsb4vMkz2q1oqBTVvqF3m"
ACCESS_TOKEN = "1461713880711716872-ngF43CEXSTPVvjNQTIPSEIpL5auKiZ"
ACCESS_TOKEN_SECRET = "GGnB3lJOg2KiI7htPYolUBfajjx9eAzogU5cISGz79z7U"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAADGGxgEAAAAAWwXZV9y2sevn%2BWlZZR%2FF1qbOXKg%3D6ydfz929thJn4A8rRN8z59cXtdMahz1d2Ynk3CAVSl9hSS3xlX"

# Authenticate with Tweepy
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)  # Enable automatic rate limit handling
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Initialize Discord Client with Privileged Intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent (required for reading messages)

# Initialize the Discord bot client with the specified intents
discord_client = discord.Client(intents=intents)

# Step 2: Function to fetch tweets, images, and text
async def fetch_images_from_user(username, count=10, output_folder="images", discord_channel=None):
    try:
        # Get user details
        user = client.get_user(username=username)
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
            print(f"No tweets found for user {username}.")
            return

        # Ensure the output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        media_mapping = {media["media_key"]: media for media in tweets.includes["media"]}

        image_count = 0

        # Process each tweet
        for tweet in tweets.data:
            # Check if tweet contains the hashtag #DBLegends
            if "#DBLegends" in tweet.text:
                print(f"Found tweet with #DBLegends: {tweet.text}")

                # Save the tweet text to a file
                text_file_path = os.path.join(output_folder, f"{username}_{tweet.id}_text.txt")
                with open(text_file_path, "w") as text_file:
                    text_file.write(f"Tweet: {tweet.text}\n")
                    print(f"Saved tweet text to {text_file_path}")

                # Send the tweet text to the Discord channel
                if discord_channel:
                    with open(text_file_path, "r") as text_file:
                        text_content = text_file.read()
                        await discord_channel.send(f"Tweet Content:\n{text_content}")

                # If tweet has images
                if "attachments" in tweet and "media_keys" in tweet.attachments:
                    for media_key in tweet.attachments["media_keys"]:
                        media = media_mapping.get(media_key)
                        if media and media["type"] == "photo":
                            image_url = media["url"]
                            print(f"Downloading image: {image_url}")

                            # Save the image
                            response = requests.get(image_url)
                            if response.status_code == 200:
                                image_path = os.path.join(output_folder, f"{username}_{tweet.id}_{image_count}.jpg")
                                with open(image_path, "wb") as f:
                                    f.write(response.content)
                                    print(f"Saved image to {image_path}")
                                    image_count += 1

                                # Send the image to the Discord channel
                                if discord_channel:
                                    with open(image_path, "rb") as image_file:
                                        await discord_channel.send(file=discord.File(image_file))

        print(f"Downloaded {image_count} images and sent them to Discord channel for @{username} containing #DBLegends.")

    except tweepy.TooManyRequests as e:
        # Handle the rate limit error
        print("Rate limit exceeded. Waiting for 15 minutes before retrying...")
        await asyncio.sleep(15 * 60)  # Wait for 15 minutes (rate limit reset time)
        await fetch_images_from_user(username, count, output_folder, discord_channel)  # Retry fetching after delay

    except Exception as e:
        print(f"Error: {e}")


# Step 3: Handle Discord Commands
@discord_client.event
async def on_ready():
    print(f'We have logged in as {discord_client.user}')

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    if message.content.startswith('!scrapeTweets'):
        username = message.content.split(' ')[1]  # Get the username from the message
        await message.channel.send(f"Scraping tweets for @{username}...")

        # Run the tweet scraping function asynchronously
        await fetch_images_from_user(username, discord_channel=message.channel)

        await message.channel.send(f"Scraping completed for @{username}.")

# Run the Discord bot
discord_client.run(DISCORD_TOKEN)
