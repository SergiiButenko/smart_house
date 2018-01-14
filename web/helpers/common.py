import inspect
import datetime
import json
from pytz import timezone


# For get function name intro function. Usage mn(). Return string with current function name. Instead 'query' will be database.QUERY[mn()].format(....)
mn = lambda: inspect.stack()[1][3]

BACKEND_IP = 'http://0.0.0.0:7542'
VIBER_BOT_IP = 'https://mozart.hopto.org:7443'

BRANCHES_LENGTH = 18
RULES_FOR_BRANCHES = [None] * BRANCHES_LENGTH
BRANCHES_SETTINGS = [None] * BRANCHES_LENGTH

REDIS_KEY_FOR_VIBER = 'viber_sent_intervals'
VIBER_SENT_TIMEOUT = 10
USERS = [
    {'name': 'Sergii', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='},
    {'name': 'Oleg', 'id': 'IRYaSCRnmV1IT1ddtB8Bdw=='},
    {'name': 'Irina', 'id': 'mSR74mGibK+ETvTTx2VvcQ=='}
]

HOURS = 24
RAIN_MAX = 20

START_RULE = 1
STOP_RULE = 2
ENABLED_RULE = 1


def date_handler(obj):
    """Convert datatime to string format."""
    if hasattr(obj, 'isoformat'):
        datetime_obj_utc = obj.replace(tzinfo=timezone('UTC'))
        return datetime_obj_utc.isoformat()
    else:
        raise TypeError


def convert_to_obj(data):
    """Convert to dict."""
    try:
        data = json.loads(data)
    except:
        pass
    return data


def convert_to_datetime(value):
    """Conver data string to datatime object."""
    try:
        value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
    except:
        pass

    try:
        value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
    except:
        pass

    try:
        value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S+00:00")
    except:
        pass

    try:
        value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f+00:00")
    except:
        pass
        # 2017-10-26T15:29:51.685474+00:00

    # 'date_start': '2017-10-31',
    try:
        value = datetime.datetime.strptime(value, "%Y-%m-%d")
    except:
        pass

    # 'date_start': '06:15',
    try:
        value = datetime.datetime.strptime(value, "%H:%M")
    except:
        pass

    # 'date_start': '06:15',
    try:
        value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except:
        pass

    return value


def date_hook(json_dict):
    """Convert str to datatime object."""
    for (key, value) in json_dict.items():
        try:
            json_dict[key] = convert_to_datetime(value)
        except:
            pass

    return json_dict

