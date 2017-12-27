import redis
import logging
import json
import datetime

from pytz import timezone
from helpers.common import *

redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)


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

    return value


def date_hook(json_dict):
    """Convert str to datatime object."""
    for (key, value) in json_dict.items():
        try:
            json_dict[key] = convert_to_datetime(value)
        except:
            pass

    return json_dict


def set_next_rule_to_redis(branch_id, data):
    """Set next rule in redis."""
    res = False
    try:
        data = json.dumps(data, default=date_handler)
        res = redis_db.set(branch_id, data)
    except Exception as e:
        logging.error("Can't save data to redis. Exception occured {0}".format(e))

    return res


def get_next_rule_from_redis(branch_id):
    """Get next rule from redis."""
    json_to_data = None
    try:
        data = redis_db.get(branch_id)
        if data is None:
            return None

        json_to_data = json.loads(data.decode("utf-8"), object_hook=date_hook)
    except Exception as e:
        logging.error("Can't get data from redis. Exception occured {0}".format(e))

    return json_to_data
