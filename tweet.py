from utils import get_jsonpath_result
from user import User

class Tweet:
    tweet_dict: dict = None

    typename: str = None

    id: str = None
    user: User = None
    full_text: str = None
    created_at: str = None
    in_reply_to_status_id: str = None
    quoted_status_id: str = None
    retweet_status_id: str = None

    # Stats
    favorite_count: int = None
    bookmark_count: int = None
    quote_count: int = None
    reply_count: int = None
    retweet_count: int = None
    view_count: int = None

    # Entities
    entity_medias: list[str] = None
    entity_hastags: list[str] = None
    entity_urls: list[str] = None
    entity_user_mentions: list[str] = None

    def __init__(self, tweet: dict):
        self.tweet_dict = tweet

        self.typename = tweet.get("__typename")
        if self.typename == "Tweet":
            self.parse_tweet_from_dict(tweet)

    def parse_tweet_from_dict(self, tweet: dict):
        self.user = User(tweet.get("core").get("user_results").get("result"))
        self.id = tweet.get("legacy").get("id_str") or None
        self.full_text = tweet.get("legacy").get("full_text") or None
        self.created_at = tweet.get("legacy").get("created_at") or None
        self.in_reply_to_status_id = tweet.get("legacy").get("in_reply_to_status_id_str") or None
        self.quoted_status_id = tweet.get("legacy").get("quoted_status_id_str") or None
        self.retweet_status_id = tweet.get("legacy").get("retweet_status_id_str") or None

        self.favorite_count = tweet.get("legacy").get("favorite_count") or None
        self.bookmark_count = tweet.get("legacy").get("bookmark_count") or None
        self.quote_count = tweet.get("legacy").get("quote_count") or None
        self.reply_count = tweet.get("legacy").get("reply_count") or None
        self.retweet_count = tweet.get("legacy").get("retweet_count") or None
        self.view_count = tweet.get("views").get("count") or None    

        self.entity_medias = [media.get("media_url_https") for media in tweet.get("legacy").get("entities").get("media") or []]
        self.entity_hastags = [hastag.get("text") for hastag in tweet.get("legacy").get("entities").get("hashtags") or []]
        self.entity_urls = [url.get("expanded_url") for url in tweet.get("legacy").get("entities").get("urls") or []]
        self.entity_user_mentions = [user_mention.get("screen_name") for user_mention in tweet.get("legacy").get("entities").get("user_mentions") or []]

    def __repr__(self):
        base = "Tweet("

        base += "id=" + str(self.id) + ","
        base += "user=" + str(self.user) + ","
        base += "created_at=" + str(self.created_at) + ","
        base += "full_text=" + ' '.join(self.full_text.split("\n")) + ","
        base += "in_reply_to_status_id=" + str(self.in_reply_to_status_id) + ","
        base += "quoted_status_id=" + str(self.quoted_status_id) + ","
        base += "retweet_status_id=" + str(self.retweet_status_id) + ","

        base += "favorite_count=" + str(self.favorite_count) + ","
        base += "bookmark_count=" + str(self.bookmark_count) + ","
        base += "quote_count=" + str(self.quote_count) + ","
        base += "reply_count=" + str(self.reply_count) + ","
        base += "retweet_count=" + str(self.retweet_count) + ","
        base += "view_count=" + str(self.view_count) + ","
        
        base += "entity_medias=" + str(self.entity_medias) + ","
        base += "entity_hastags=" + str(self.entity_hastags) + ","
        base += "entity_urls=" + str(self.entity_urls) + ","
        base += "entity_user_mentions=" + str(self.entity_user_mentions)

        base += ")"
        return base