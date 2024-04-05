from playwright.async_api import async_playwright, Playwright, BrowserContext, Page, Response, expect
import logging
from datetime import datetime
import urllib.parse
import random
import asyncio
from utils import change_twitter_date_format, get_jsonpath_result
import time
from filters import TweetFilter
import mpu.io

class TwitterApi:

    # Playwright objects
    playwright: Playwright
    context: BrowserContext
    page: Page

    # Twitter API objects
    __x_rate_limit_limit = 0
    __x_rate_limit_remaining = 0
    __x_rate_limit_reset = 0

    # Settings
    delay: tuple[int, int] = (7, 10)
    responses_wait_count: int = 10
    responses_wait_sec: int = 60
    rate_limit_stop = 5

    __halt_session: bool = False

    def __init__(self, logging_level: int = logging.WARN, logger_name: str = None):
        """
        Create a TwitterApi object.

        Args:
            logging_level (int): The logging level you want to use.
            logger_name (str): The name of the logger you want to use.
        """

        if logger_name is None:
            logger_name = __name__
        self.__create_logger(logger_name, logging_level)
        
    def __create_logger(self, name: str, level: int = logging.DEBUG):
        """Create a logger for the class."""
        self.logger: logging.Logger = logging.getLogger("asyncio")
        self.logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    async def create_client(
        self, 
        auth_token: str, 
        ct0: str,
        headless: bool = False,
    ):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context()
        await self.context.add_cookies([
            {"name": "auth_token", "value": auth_token, "domain": "twitter.com", "path": "/"},
            {"name": "ct0", "value": ct0, "domain": "twitter.com", "path": "/"}])
        self.logger.info("Created Twitter API Client")

    async def __create_page(self):
        if getattr(self, "page", None) is not None:
            await self.page.close()
        self.page = await self.context.new_page()
            
    def set_default_timeout(self, timeout = 3000):
        self.context.set_default_timeout(timeout)

    def set_delay(self, delay: tuple[int, int]):
        self.delay = delay

    async def __create_interceptor_function(self, type: str, responses: list[Response]):
        async def interceptor(response: Response):
            if response.request.resource_type == "xhr" and type in response.url:
                self.__x_rate_limit_remaining = int(response.headers.get("x-rate-limit-remaining"))
                self.__x_rate_limit_reset = int(response.headers.get("x-rate-limit-reset"))
                self.__x_rate_limit_limit = int(response.headers.get("x-rate-limit-limit"))
                if response.ok:
                    self.logger.debug(f"Rate limit remaining: {self.__x_rate_limit_remaining}; Rate limit limit: {self.__x_rate_limit_limit}; Next refresh: {datetime.fromtimestamp(self.__x_rate_limit_reset).strftime('%H:%M:%S')}")
                    if (self.__x_rate_limit_limit - self.__x_rate_limit_remaining > 0 
                    and (self.__x_rate_limit_limit - self.__x_rate_limit_remaining) % self.responses_wait_count == 0):
                        self.logger.info(f"Rate limit remaining: {self.__x_rate_limit_remaining}, waiting for {self.responses_wait_sec} seconds")
                        self.__halt_session = True
                        time.sleep(self.responses_wait_sec)
                        self.__halt_session = False
                    if self.__x_rate_limit_remaining <= self.rate_limit_stop:
                        strtime = datetime.fromtimestamp(self.__x_rate_limit_reset + 30).strftime('%H:%M:%S')
                        self.logger.warning(f"Rate limit reached! Waiting for reset... (ETA: {strtime})")
                        self.__halt_session = True
                        time.sleep(self.__x_rate_limit_reset - time.time() + 30)
                        self.__halt_session = False

                    responses.append(response)
                    self.logger.debug(f"Caught a response! Response now is {len(responses)}")
                    # print(responses)
            return response
        return interceptor

    async def __scroll(
        self,
    ):
        await self.page.evaluate_handle("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        await asyncio.sleep(random.randint(self.delay[0], self.delay[1]))

    async def __wait_for_spinners(self):
        locator = self.page.get_by_role("progressbar")
        spinner_cnt = await locator.count()
        if spinner_cnt > 0:
            self.logger.debug(f"Found {spinner_cnt} spinners. Waiting for spinners to not be present")
        await expect(locator).to_have_count(0, timeout=120_000)

    async def __click_show_replies(self):
        while True:
            show_replies_button = self.page.get_by_role("button", name="Show replies")
            if await show_replies_button.count() == 0: return
            for button in await show_replies_button.all(): 
                await button.click()
            await asyncio.sleep(5)
            await self.__wait_for_spinners()

    async def __click_show_additional_replies(self):
        while True:
            show_additional_replies_button = self.page.get_by_role("button", name="Show")
            if await show_additional_replies_button.count() == 0: return
            for button in await show_additional_replies_button.all(): 
                await button.click()
            await asyncio.sleep(5)
            await self.__wait_for_spinners()

    async def __infinite_scroll(
        self,
        responses = list[Response],
        **kwargs,
    ):
        prevScrollHeight = 0
        currScrollHeight = await self.page.evaluate("document.body.scrollHeight")
        while True:
            if self.__halt_session:
                continue

            if kwargs.get("click_replies"): # Press all pressable show replies buttons
                await self.__click_show_replies()

            if kwargs.get("click_additional_replies"): # Press all pressable show buttons
                await self.__click_show_additional_replies()

            await self.__wait_for_spinners() # Wait for spinners to not be present

            # Termination by date
            if kwargs.get("start_date") and kwargs.get("end_date"):
                tweet_dates = [change_twitter_date_format(date) for date in get_jsonpath_result(await responses[-1].json(), "$..entries..itemContent.tweet_results.result.legacy.created_at")]
                if all([x < kwargs.get("start_date") for x in tweet_dates]):
                    self.logger.info("Scrolling terminated because date range is reached!")
                    break
            # Termination by pages
            if kwargs.get("pages") and len(responses) >= kwargs.get("pages"):
                self.logger.info("Scrolling terminated because page limit is reached!")
                break
            # Termination by being unable to scroll
            if currScrollHeight == prevScrollHeight:
                self.logger.info("Scrolling terminated because scrolling is not possible!")
                break
            await self.__scroll()
            prevScrollHeight = currScrollHeight
            currScrollHeight = await self.page.evaluate("document.body.scrollHeight")


    async def __get_user_tweets_responses(
        self,
        url: str,
        **kwargs,
    ):
        user_tweets_responses: list[Response] = []
        
        await self.__create_page()
        self.page.on("response", await self.__create_interceptor_function("UserTweets", user_tweets_responses))
        await self.page.goto(url)
        await self.page.wait_for_selector("[data-testid='tweet']")
        await self.__infinite_scroll(user_tweets_responses, delay=kwargs.get("delay"), 
                            start_date=kwargs.get("start_date"), end_date=kwargs.get("end_date"), 
                            pages=kwargs.get("pages"))
        return user_tweets_responses

    async def get_user_tweets(
        self,
        handle: str,
        pages: int = None,
        count: int = None,
    ) -> list[dict]:
        url = f"https://twitter.com/{handle}"
        self.logger.info("Start getting user tweets from Twitter")
        responses = await self.__get_user_tweets_responses(url, pages=pages)
        tweets: list[dict] = []
        for response in responses:
            tweets.extend(get_jsonpath_result( await response.json(), "$..entries..itemContent.tweet_results.result" ))
        tweets = TweetFilter.remove_replies(tweets)
        if count: TweetFilter.filter_by_count(tweets, count)

        self.logger.info(f"Finish getting user tweets. Got {len(tweets)} tweets")
        return tweets        


    async def __get_search_timeline_responses(
        self,
        url: str,
        **kwargs,
    ) -> list[Response]: 
        search_timeline_responses: list[Response] = []
        
        await self.__create_page()
        self.page.on("response", await self.__create_interceptor_function("SearchTimeline", search_timeline_responses))
        await self.page.goto(url)
        await self.page.wait_for_selector("[data-testid='tweet']")
        await self.__infinite_scroll(search_timeline_responses, pages=kwargs.get("pages"))
        return search_timeline_responses

    async def get_search_timeline(
        self,
        query: str = "",
        from_username: str = None,
        until: datetime = None,
        since: datetime = None,
        replies: bool = True,
        pages: int = None,
    ) -> list[dict]:
        url = f"https://twitter.com/search?q={query} "
        if from_username: url += f"(from:{from_username}) "
        if until: url += f"until:{until.strftime('%Y-%m-%d')} "
        if since: url += f"since:{since.strftime('%Y-%m-%d')} "
        if not replies: url += f"-filter:replies "
        url += ")"

        self.logger.info(f"Start getting search timeline tweets from Twitter: {url}")

        tweets: list[dict] = []
        responses = await self.__get_search_timeline_responses(url, pages=pages)
        for response in responses:
            tweets.extend(get_jsonpath_result( await response.json(), "$..entries..itemContent.tweet_results.result" ))

        self.logger.info(f"Finish getting search timeline tweets. Got {len(tweets)} tweets")

        return tweets


    async def __get_tweet_detail_responses(
        self,
        url: str,
        **kwargs
    ) -> list[Response]:
        tweet_detail: list[Response] = []

        await self.__create_page()
        self.page.on("response", await self.__create_interceptor_function("TweetDetail", tweet_detail))
        await self.page.goto(url)
        await self.page.wait_for_selector("[data-testid='tweet']")
        if kwargs.get("scroll"):
            await self.__infinite_scroll(tweet_detail, **kwargs)
        return tweet_detail

    async def get_tweet_detail(
        self, 
        url: str = None, 
        tweetid: str = None
    ) -> dict:
        if not url:
            url = f"https://twitter.com/a/status/{tweetid}"

        self.logger.info("Start getting tweet detail from Twitter")

        tweets: list[dict] = []
        responses = await self.__get_tweet_detail_responses(url)
        for response in responses:
            tweets.extend(get_jsonpath_result( await response.json(), "$..entries..itemContent.tweet_results.result" ))

        self.logger.info(f"Finish getting tweet detail")

        return tweets[0]
        
    async def get_tweet_replies(
        self,
        url: str = None,
        tweetid: str = None,
        pages: int = None,
        count: int = None,
        click_replies: bool = False,
        click_additional_replies: bool = False
    ) -> list[dict]:
        if not url:
            url = f"https://twitter.com/a/status/{tweetid}"

        self.logger.info(f"Start getting tweet replies from Twitter: {url}")

        tweets: list[dict] = []
        responses = await self.__get_tweet_detail_responses(url, scroll=True, pages=pages, click_replies=click_replies, click_additional_replies=click_additional_replies)

        for response in responses:
            tweets.extend(get_jsonpath_result( await response.json(), "$..entries..content" ))

        mpu.io.write(f"res/test/{tweetid}_replies_response.json", tweets)
        # Remove non-tweet responses
        tweets = list(filter(lambda x: not bool(get_jsonpath_result(x, "$.clientEventInfo.component")), tweets)) 
        # Remove ads
        tweets = list(filter(lambda x: not bool(get_jsonpath_result(x, "$..promotedMetadata")), tweets))
        
        tweets = get_jsonpath_result(tweets, "$..itemContent.tweet_results.result")

        if click_replies:
            for response in responses:
                tweets.extend(get_jsonpath_result( await response.json(), "$..moduleItems..itemContent.tweet_results.result" ))
        
        tweets = tweets[1:] # Remove first tweet because it's the original tweet
        if count: tweets = TweetFilter().filter_by_count(tweets, count)
        self.logger.info(f"Finish getting tweet replies")

        return tweets


    async def __get_user_by_screen_name(
        self, 
        url, 
        **kwargs
    ) -> list[Response]:
        user_by_screen_name: Response = []

        await self.__create_page()
        self.page.on("response", await self.__create_interceptor_function("UserByScreenName", user_by_screen_name))
        await self.page.goto(url)
        await self.page.wait_for_selector("[data-testid='UserName']")
        return user_by_screen_name

    async def get_user_by_screen_name(
        self,
        screen_name: str
    ):
        url = f"https://twitter.com/{screen_name}"

        response = await self.__get_user_by_screen_name(url)
        try:
            user = get_jsonpath_result(await response[0].json(), "$.data.user.result")[0]
        except IndexError:
            print("User not found")
            user = None

        return user


    async def close_client(self):
        await self.browser.close()
        await self.playwright.stop()
        self.logger.info("Closed Twitter API Client")

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close_client()