#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import json
import requests
import time
import inspect
import sqlite3
import logging
import redis

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)

BACKEND_IP = 'http://127.0.0.1:7543'

HUMIDITY_MAX = 1000
RULES_FOR_BRANCHES = [None] * 18

RULES_ENABLED = True

# For get function name intro function. Usage mn(). Return string with current function name. Instead 'query' will be QUERY[mn()].format(....)
mn = lambda: inspect.stack()[1][3]

QUERY = {}
QUERY['get_next_active_rule'] = "SELECT l.id, l.line_id, l.rule_id, l.timer as \"[timestamp]\", l.interval_id  FROM life AS l WHERE l.state = 1 AND l.active=1 AND l.line_id={0} AND timer>=datetime('now', 'localtime') ORDER BY timer LIMIT 1"
QUERY['enable_rule'] = "UPDATE life SET state=2 WHERE id={0}"
QUERY['enable_rule_state_6'] = "UPDATE life SET state=6 WHERE id={0}"
QUERY['inspect_conditions'] = "UPDATE life SET state={0} WHERE id={1}"


def date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError


def date_hook(json_dict):
    for (key, value) in json_dict.items():
        try:
            json_dict[key] = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        except:
            pass
    return json_dict


def set_next_rule_to_redis(branch_id, data):
    """Set next rule in redis."""
    try:
        data = json.dumps(data, default=date_handler)
        res = redis_db.set(branch_id, data)
    except Exception as e:
        logging.error("Can't save data to redis. Exception occured {0}".format(e))

    return res


def get_next_rule_from_redis(branch_id):
    """Get next rule from redis."""
    try:
        data = redis_db.get(branch_id)
        if data is None:
            return None

        json_to_data = json.loads(data.decode("utf-8"), object_hook=date_hook)
    except Exception as e:
        logging.error("Can't get data from redis. Exception occured {0}".format(e))

    return json_to_data


def branch_on(line_id, alert_time=25):
    """Blablbal."""
    try:
        payload = (('id', line_id), ('mode', 'auto'))
        response = requests.get(url=BACKEND_IP + '/activate_branch', params=payload)

        logging.debug('response {0}'.format(response.text))

        logging.info('Branch {0} is turned on by rule'.format(line_id))
    except requests.exceptions.Timeout as e:
        logging.error(e)
        logging.error("Can't turn on {0} branch by rule. Timeout Exception occured".format(line_id))
    except Exception as e:
        logging.error(e)
        logging.error("Can't turn on {0} branch by rule. Exception occured".format(line_id))
        return None

    logging.debug('return status')
    return response


def branch_off(line_id):
    """Blablbal."""
    try:
        logging.debug('Branch {0} is turning off by rule'.format(line_id))
        response = requests.get(url=BACKEND_IP + '/deactivate_branch', params={"id": line_id, 'mode': 'auto'})

        logging.debug('response {0}'.format(response.text))
        logging.info('Branch {0} is turned off by rule'.format(line_id))
    except requests.exceptions.Timeout as e:
        logging.error(e)
        logging.error("Can't turn off {0} branch by rule.Timeout Exception occured".format(line_id))
    except Exception as e:
        logging.error(e)
        logging.error("Can't turn off {0} branch by rule. Exception occured".format(line_id))
        return None

    logging.debug('return status')
    return response


# executes query and returns fetch* result
def execute_request(query, method='fetchall'):
    """Blablbal."""
    conn = None
    try:
        conn = sqlite3.connect('/var/sqlite_db/test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
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
    """Blablbal."""
    conn = None
    lastrowid = 0
    try:
        # conn = psycopg2.connect("dbname='test' user='sprinkler' host='185.20.216.94' port='35432' password='drop#'")
        conn = sqlite3.connect('/var/sqlite_db/test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
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


def get_next_active_rule(line_id):
    """Blablbal."""
    query = QUERY[mn()].format(line_id)
    res = execute_request(query, 'fetchone')
    if res is None:
        return None

    logging.info("Next active rule retrieved for line id {0}".format(line_id))
    return {'id': res[0], 'line_id': res[1], 'rule_id': res[2], 'timer': res[3], 'interval_id': res[4]}


def update_all_rules():
    """Set next active rules for all branches."""
    try:
        for i in range(1, len(RULES_FOR_BRANCHES)):
            set_next_rule_to_redis(i, get_next_active_rule(i))
        logging.info("Rules updated")
    except Exception as e:
        logging.error("Exeption occured while updating all rules. {0}".format(e))


def sync_rules_from_redis():
    """Synchronize all rules that are present in redis."""
    try:
        for i in range(1, 18):
            RULES_FOR_BRANCHES[i] = get_next_rule_from_redis(i)
            print(i)
            print(get_next_rule_from_redis(str(i)))
    except Exception as e:
        logging.error("Exeption occured while synchronizing rules from redis. {0}".format(e))
        raise e


def inspect_conditions(rule):
    """Check if rule can be executed or not."""
    try:
        if rule is None:
            return False

        if (RULES_ENABLED is False):
            logging.warn("All rules are disabled on demand")
            return False

        response = requests.get(url=BACKEND_IP + '/weather2', params={"force_update": 'false'})
        logging.debug('response {0}'.format(response.text))

        json_data = json.loads(response.text)
        if (json_data['data']['allow_irrigation'] is False):
            if (rule['rule_id'] == 1):
                update_db_request(QUERY[mn()].format(json_data['data']['rule_status'], rule['id']))
                logging.warn("Rule '{0}' is canceled. {1}".format(rule['id'], json_data['data']['user_message']))
                return False
            else:
                logging.warn("Humidity sensor will execute 'disable branch' rule dispite humidity sensor values")
    except Exception as e:
        logging.error(e)
        logging.error("Can't check conditions for rule. Ecxeption occured")
        return False

    return True


def enable_rule():
    """Synch with redis each 10 seconds. Execute rules if any."""
    try:
        logging.info("enable rule thread started.")

        logging.info("Updating rules on start.")
        update_all_rules()
        logging.debug("rules updated")

        while True:
            # logging.info("enable_rule_daemon heartbeat. RULES_FOR_BRANCHES: {0}".format(str(RULES_FOR_BRANCHES)))
            sync_rules_from_redis()

            time.sleep(10)

            for rule in RULES_FOR_BRANCHES:
                # if (inspect_conditions(rule) is False):
                #     continue

                logging.info("Rule '{0}' is going to be executed".format(str(rule)))

                if (datetime.datetime.now() >= rule['timer']):
                    logging.info("Rule '{0}' execution started".format(str(rule)))
                    if (rule['line_id'] == 17):
                        arduino_branch_name = 'pump'
                    else:
                        arduino_branch_name = rule['line_id']

                    logging.debug("arduino_branch_name retrieved : {0}".format(arduino_branch_name))

                    if rule['rule_id'] == 1:
                        logging.debug("rule['rule_id'] : {0}".format(rule['rule_id']))

                        response = branch_on(rule['line_id'])
                        if response is None:
                            logging.error("Can't turn on {0} branch".format(rule['line_id']))
                            continue

                        json_data = json.loads(response.text)
                        if (json_data[str(arduino_branch_name)] == '0'):
                            logging.error("Can't turn on {0} branch".format(rule['line_id']))
                            continue

                        if (json_data[str(arduino_branch_name)] == '1'):
                            logging.info("Turned on {0} branch".format(rule['line_id']))
                            logging.debug("updating db")
                            update_db_request(QUERY[mn()].format(rule['id']))

                            logging.debug("get next active rule")
                            set_next_rule_to_redis(rule['line_id'], get_next_active_rule(rule['line_id']))

                            logging.info("Rule '{0}' is done. Removing".format(str(rule)))

                    if rule['rule_id'] == 2:
                        logging.debug("rule['rule_id'] : {0}".format(rule['rule_id']))
                        response = branch_off(rule['line_id'])
                        if response is None:
                            logging.error("Can't turn off {0} branch".format(rule['line_id']))
                            continue

                        json_data = json.loads(response.text)
                        if (json_data[str(arduino_branch_name)] == '1'):
                            logging.error("Can't turn off {0} branch".format(rule['line_id']))
                            continue

                        if (json_data[str(arduino_branch_name)] == '0'):
                            logging.info("Turned off {0} branch".format(rule['line_id']))
                            logging.debug("updating db")
                            update_db_request(QUERY[mn()].format(rule['id']))

                            logging.debug("get next active rule")
                            set_next_rule_to_redis(rule['line_id'], get_next_active_rule(rule['line_id']))

                            logging.info("Rule '{0}' is done. Removing".format(str(rule)))

    except Exception as e:
        logging.error("enable rule thread exception occured. {0}".format(e))
    finally:
        logging.info("enable rule thread stopped.")


if __name__ == "__main__":
    enable_rule()
