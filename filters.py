from utils import get_jsonpath_result, change_twitter_date_format
import datetime

class TweetFilter:
    @staticmethod
    def remove_replies(tweets: list[dict]) -> list[dict]:
        return list(filter(lambda tweet: not get_jsonpath_result(tweet, "$.legacy.in_reply_to_status_id_str"), tweets))
    
    @staticmethod
    def remove_retweets(tweets: list[dict]) -> list[dict]:
        return list(filter(lambda tweet: not get_jsonpath_result(tweet, "$.legacy.retweeted_status_result"), tweets))
    
    @staticmethod
    def remove_quotes(tweets: list[dict]) -> list[dict]:
        return list(filter(lambda tweet: not get_jsonpath_result(tweet, "$.legacy.quoted_status_id_str"), tweets))
    
    @staticmethod
    def filter_by_user_handle(tweets: list[dict], handle: str) -> list[dict]:
        return list(filter(lambda tweet: not get_jsonpath_result(tweet, "$.legacy.in_reply_to_status_id_str"), tweets))

    @staticmethod
    def filter_by_date(tweets: list[dict], start_date: datetime, end_date: datetime) -> list[dict]:
        return list(filter(lambda tweet: start_date <= change_twitter_date_format(get_jsonpath_result(tweet, "$.legacy.created_at")[0]) <= end_date, tweets))
    
    @staticmethod
    def filter_by_count(tweets: list[dict], count: int) -> list[dict]:
        return tweets[:count]