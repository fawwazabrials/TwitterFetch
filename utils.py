from jsonpath_ng.ext import parse
import datetime

def change_twitter_date_format(date: str, tz_offset: int) -> datetime:
    return datetime.datetime.strptime(date, "%a %b %d %H:%M:%S %z %Y").replace(tzinfo=
                                                                                datetime.timezone(datetime.timedelta(hours=tz_offset))
                                                                               )
def get_jsonpath_result(json: dict, jsonpath: str) -> list:
    return [match.value for match in parse(jsonpath).find(json)]