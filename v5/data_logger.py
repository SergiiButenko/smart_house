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
ARDUINO_SMALL_H_IP = 'http://butenko.asuscomm.com:5555'

QUERY = {}
QUERY['weather'] = "INSERT INTO temp_statisitics(temperature_street, humidity_street, temperature_small_h_1_fl, humidity_small_h_1_fl, temperature_small_h_2_fl, humidity_small_h_2_fl, temperature_big_h_1_fl, humidity_big_h_1_fl, temperature_big_h_2_fl, humidity_big_h_2_fl) VALUES ({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9})"


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
    try:
        temperature_street = 0
        humidity_street = 0

        temperature_small_h_1_fl = 0
        humidity_small_h_1_fl = 0

        temperature_small_h_2_fl = 0
        humidity_small_h_2_fl = 0

        temperature_big_h_1_fl = 0
        humidity_big_h_1_fl = 0

        temperature_big_h_2_fl = 0
        humidity_big_h_2_fl = 0

        url = 'http://api.openweathermap.org/data/2.5/weather?id=698782&appid=319f5965937082b5cdd29ac149bfbe9f'
        try:
            response = requests.get(url=url, timeout=(3, 3))
            response.raise_for_status()
            json_data = json.loads(response.text)
            temperature_street = str(round(pytemperature.k2c(json_data['main']['temp']), 2)), 
            humidity_street = str(round(json_data['main']['humidity'], 2))
        except requests.exceptions.RequestException as e:
            logging.error(e)
            logging.error("Can't get weather info Exception occured")
            humidity_street = 0
            temperature_street = 0

        try:
            response = requests.get(url=ARDUINO_SMALL_H_IP + '/temperature', timeout=(3, 3))
            response.raise_for_status()
            json_data = json.loads(response.text)

            temperature_small_h_1_fl = json_data['1_floor_temperature']
            humidity_small_h_1_fl = json_data['1_floor_humidity']

            temperature_small_h_2_fl = json_data['2_floor_temperature']
            humidity_small_h_2_fl = json_data['2_floor_humidity']
            logging.info(response.text)
        except requests.exceptions.RequestException as e:
            logging.error(e)
            logging.error("Can't get temp info Exception occured")

            temperature_small_h_1_fl = 0
            humidity_small_h_1_fl = 0

            temperature_small_h_2_fl = 0
            humidity_small_h_2_fl = 0

        update_db_request(QUERY[mn()].format(
            temperature_street, humidity_street,
            temperature_small_h_1_fl, humidity_small_h_1_fl,
            temperature_small_h_2_fl, humidity_small_h_2_fl,
            temperature_big_h_1_fl, humidity_big_h_1_fl,
            temperature_big_h_2_fl, humidity_big_h_2_fl)
        )
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    weather()
