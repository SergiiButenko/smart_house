#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import json
import requests
import inspect
import sqlite3
import logging
import pytemperature

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

# For get function name intro function. Usage mn(). Return string with current function name. Instead 'query' will be QUERY[mn()].format(....)
mn = lambda: inspect.stack()[1][3]

QUERY = {}
QUERY['weather'] = "insert into weather(datetime, temperature, humidity) VALUES ('{0}', {1}, {2})"


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


def weather():
    """Blablbal."""
    url = 'http://api.openweathermap.org/data/2.5/weather?id=698782&appid=319f5965937082b5cdd29ac149bfbe9f'
    try:
        response = requests.get(url=url, timeout=(3, 3))
        response.raise_for_status()
        logging.info("response: " + response.text)

        json_data = json.loads(response.text)
        temperature = str(round(pytemperature.k2c(json_data['main']['temp']), 2))
        logging.info("temperature: " + temperature)
        humidity = str(round(json_data['main']['humidity'], 2))
        logging.info("humidity: " + humidity)

        now = datetime.datetime.now()
        logging.info("now: " + str(now))

        update_db_request(QUERY[mn()].format(now, temperature, humidity))
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    weather()
