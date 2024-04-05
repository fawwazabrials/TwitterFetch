from twitter import TwitterApi
from tweet import Tweet
import pandas as pd
import datetime
import logging
import asyncio
import mpu.io
import json
import os

AUTH_TOKEN = "XXXXXXXX" # Get from cookies
CT0 = "XXXXXXXX"        # Get from cookies

# Just change these values for another project
TWITTER_HANDLE = "elonmusk"
S_YEAR, S_MONTH, S_DAY = 2023, 1 , 1
E_YEAR, E_MONTH, E_DAY = 2023, 12, 31
JKT_TIMEZONE = datetime.timezone(datetime.timedelta(hours=7))
INTERVAL = 10

# DONT CHANGE!
START_DATE = datetime.datetime(S_YEAR, S_MONTH, S_DAY, tzinfo=JKT_TIMEZONE)
END_DATE = datetime.datetime(E_YEAR, E_MONTH, E_DAY, tzinfo=JKT_TIMEZONE)

async def get_user_tweets_in_range(twitter: TwitterApi):
    range = (END_DATE - START_DATE).days
    since = START_DATE
    all_tweets = []
    while range > 0:
        until = since.__add__(datetime.timedelta(days=INTERVAL if range > INTERVAL else range))
        print("\n-----", since, until, range)
        tweets = await twitter.get_search_timeline(from_username=TWITTER_HANDLE, since=since, until=until, replies=False)
        all_tweets.extend(tweets)
        since = until
        range -= INTERVAL    
    return tweets

async def main():
    async with TwitterApi(logging_level=logging.DEBUG) as twitter:
        await twitter.create_client(auth_token=AUTH_TOKEN, ct0=CT0, headless=False)
        twitter.set_default_timeout(0)
        twitter.responses_wait_count = 50

        raw_tweets = await get_user_tweets_in_range(twitter)

if __name__ == "__main__":
    asyncio.run(main())