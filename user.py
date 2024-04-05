from utils import get_jsonpath_result

class User:
    user_dict: dict = None

    id: str = None
    created_at: str = None
    screen_name: str = None
    name: str = None
    description: str = None
    location: str = None

    # Statistics
    favourites_count: int = None
    followers_count: int = None
    friends_count: int = None
    listed_count: int = None
    statuses_count: int = None

    #TODO: MAsih banyak yg harus ditambah cokk

    def __init__(self, user: dict):
        self.user_dict = user
        self.parse_user_from_dict(user)

    def parse_user_from_dict(self, user: dict):
        self.id = user.get("rest_id") or None
        self.created_at = user.get("legacy").get("created_at") or None
        self.screen_name = user.get("legacy").get("screen_name") or None
        self.name = user.get("legacy").get("name") or None
        self.description = user.get("legacy").get("description") or None
        self.location = user.get("legacy").get("location") or None

        self.favourites_count = user.get("legacy").get("favourites_count") or 0
        self.followers_count = user.get("legacy").get("normal_followers_count") or 0
        self.friends_count = user.get("legacy").get("friends_count") or 0
        self.listed_count = user.get("legacy").get("listed_count") or 0
        self.statuses_count = user.get("legacy").get("statuses_count") or 0

    #     self.id = get_jsonpath_result(user, "$.rest_id")[0] or None
    #     self.created_at = get_jsonpath_result(user, "$.legacy.created_at")[0] or None
    #     self.screen_name = get_jsonpath_result(user, "$.legacy.screen_name")[0] or None
    #     self.name = get_jsonpath_result(user, "$.legacy.name")[0] or None
    #     self.description = get_jsonpath_result(user, "$.legacy.description")[0] or None
    #     self.location = get_jsonpath_result(user, "$.legacy.location")[0] or None

    #     self.favourites_count = get_jsonpath_result(user, "$.legacy.favourites_count")[0] or 0
    #     self.followers_count = get_jsonpath_result(user, "$.legacy.normal_followers_count")[0] or 0
    #     self.friends_count = get_jsonpath_result(user, "$.legacy.friends_count")[0] or 0
    #     self.listed_count = get_jsonpath_result(user, "$.legacy.listed_count")[0] or 0
    #     self.statuses_count = get_jsonpath_result(user, "$.legacy.statuses_count")[0] or 0

    def __repr__(self) -> str:
        base = "User("

        base += "id=" + self.id + ","
        base += "created_at=" + self.created_at + ","
        base += "screen_name=" + self.screen_name + ","
        base += "name=" + self.name + ","
        base += "description=" + ' '.join(self.description.split("\n")) + ","
        base += "location=" + self.location + ","

        base += "favourites_count=" + str(self.favourites_count) + ","
        base += "followers_count=" + str(self.followers_count) + ","
        base += "friends_count=" + str(self.friends_count) + ","
        base += "listed_count=" + str(self.listed_count) + ","
        base += "statuses_count=" + str(self.statuses_count) + ")"
        return base