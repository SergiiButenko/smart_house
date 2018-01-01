import redis
import logging
import json
from helpers.common import *

redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)


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
