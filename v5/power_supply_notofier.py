#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sqlite3
import inspect
import logging
import redis
import requests

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

# For get function name intro function. Usage mn(). Return string with current function name. Instead 'query' will be QUERY[mn()].format(....)
mn = lambda: inspect.stack()[1][3]

redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)

VIBER_BOT_IP = 'https://mozart.hopto.org:7443'

USERS = [
    {'name': 'Sergii', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='}
    # {'name': 'Oleg', 'id': 'IRYaSCRnmV1IT1ddtB8Bdw=='}
]


QUERY = {}
QUERY['worker'] = "insert into power_statistics(state) VALUES ({0})"


# executes query and returns fetch* result
def execute_request(query, method='fetchall'):
    """Use this method in case you need to get info from database."""
    conn = None
    try:
        conn = sqlite3.connect('/var/sqlite_db/test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn = sqlite3.connect('/home/sergey/repos/irrigation_peregonivka/test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn = sqlite3.connect('C:\\repos\\irrigation_peregonivka\\test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # execute our Query
        cursor.execute(query)
        logging.debug("db request '{0}' executed".format(query))
        return getattr(cursor, method)()
    except Exception as e:
        logging.error("Error while performing operation with database: {0}".format(e))
        return None
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception as e:
            logging.error("Error while closing connection with database: {0}".format(e))


# executes query and returns fetch* result
def update_db_request(query):
    """Doesn't have fetch* methods. Returns lastrowid after database insert command."""
    conn = None
    lastrowid = 0
    try:
        conn = sqlite3.connect('/var/sqlite_db/test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn = sqlite3.connect('/home/sergey/repos/irrigation_peregonivka/test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn = sqlite3.connect('C:\\repos\\irrigation_peregonivka\\test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cursor = conn.cursor()
        # execute our Query
        cursor.execute(query)
        conn.commit()
        logging.debug("db request '{0}' executed".format(query))
        lastrowid = cursor.lastrowid
        return lastrowid
    except Exception as e:
        logging.error("Error while performing operation with database: {0}".format(e))
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception as e:
            logging.error("Error while closing connection with database: {0}".format(e))
            return None


STATE_BAT = 0
STATE_POWER = 1
REDIS_KEY = 'power_state'

def send_message(msg_text):
    """Send message to viber"""
    try:
        payload = {'users': USERS, 'msg_text': msg_text}
        response = requests.post(VIBER_BOT_IP + '/send_message', json=payload, timeout=(10, 3))
        response.raise_for_status()
    except Exception as e:
        logging.error("Can't send rule to viber. Ecxeption occured")
        raise e


def get_power_current_state():
    try:
        return STATE_POWER
    except Exception as e:
        logging.error("Can't check power supply state. Ecxeption occured")
        raise e


def worker():
    """Blablbal."""
    try:
        previous_state = redis_db.get(REDIS_KEY)
        current_state = get_power_current_state()
        if (current_state == STATE_POWER):
            text = 'Напруга подається із мережі.'
        else:
            text = 'Напруга подається з батареї.'

        if previous_state is None:
            logging.info("Seems like Rapberry just started")
            redis_db.set(REDIS_KEY, current_state)
            update_db_request(QUERY[mn()].format(current_state))
            send_message(msg_text='Зміна стану напруги. \nСервер був перезавантажен. \n{0}'.format(text))
            return

        previous_state = int(previous_state.decode())

        if (get_power_current_state() == previous_state):
            logging.info("Power - no change")
            return

        redis_db.set(REDIS_KEY, current_state)
        logging.info("Power - changed. Current state {0}: {1}".format(current_state, text))
        update_db_request(QUERY[mn()].format(current_state))
        send_message(msg_text='Зміна стану напруги. \n{0}'.format(text))

    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    worker()
