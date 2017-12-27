#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import json
import requests
import time
import logging
from helpers import sqlite_database as database
from helpers.redis import *
from helpers.common import *

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)


BACKEND_IP = 'http://127.0.0.1:7542'
VIBER_BOT_IP = 'https://mozart.hopto.org:7443'

HUMIDITY_MAX = 1000
RULES_FOR_BRANCHES = [None] * 40

RULES_ENABLED = True
REDIS_KEY_FOR_VIBER = 'viber_sent_intervals'
VIBER_SENT_TIMEOUT = 10


USERS = [
    {'name': 'Sergii', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='},
    {'name': 'Oleg', 'id': 'IRYaSCRnmV1IT1ddtB8Bdw=='},
    {'name': 'Irina', 'id': 'mSR74mGibK+ETvTTx2VvcQ=='}
]

HOURS = 24
RAIN_MAX = 20


def branch_on(line_id, alert_time):
    """Blablbal."""
    try:
        for attempt in range(2):
            try:
                response = requests.get(url=BACKEND_IP + '/activate_branch', params={"id": line_id, 'time_min': alert_time, 'mode': 'auto'}, timeout=(3, 3))
                response.raise_for_status()
                logging.debug('response {0}'.format(response.text))

                resp = json.loads(response.text)['branches']
                if (resp[line_id]['status'] != 1):
                    logging.error('Branch {0} cant be turned on by rule. response {1}'.format(line_id, response.text))
                    time.sleep(2)
                    continue
                else:
                    logging.info('Branch {0} is turned on by rule'.format(line_id))
                    return response

            except Exception as e:
                logging.error(e)
                logging.error("Can't turn on {0} branch by rule. Exception occured. {1} try out of 2".format(line_id, attempt))
                time.sleep(2)
                continue
        raise Exception("Can't turn on {0} branch".format(line_id))

    except Exception as e:
        logging.error(e)
        logging.error("Can't turn on {0} branch by rule. Exception occured".format(line_id))
        raise Exception("Can't turn on {0} branch".format(line_id))


def branch_off(line_id):
    """Blablbal."""
    try:
        for attempt in range(2):
            try:
                response = requests.get(url=BACKEND_IP + '/deactivate_branch', params={"id": line_id, 'mode': 'auto'}, timeout=(3, 3))
                response.raise_for_status()
                logging.debug('response {0}'.format(response.text))

                resp = json.loads(response.text)['branches']
                if (resp[line_id]['status'] != 0):
                    logging.error('Branch {0} cant be turned off by rule. response {1}. {2} try out of 2'.format(line_id, response.text, attempt))
                    time.sleep(2)
                    continue
                else:
                    logging.info('Branch {0} is turned off by rule'.format(line_id))
                    return response
            except requests.exceptions.Timeout as e:
                logging.error(e)
                logging.error("Can't turn off {0} branch by rule. Timeout Exception occured  {1} try out of 2".format(line_id, attempt))
                time.sleep(2)
                continue
            except Exception as e:
                logging.error(e)
                logging.error("Can't turn off {0} branch by rule. Exception occured. {1} try out of 2".format(line_id, attempt))
                time.sleep(2)
                continue

        raise Exception("Can't turn off {0} branch".format(line_id))

    except Exception as e:
        logging.error(e)
        logging.error("Can't turn off {0} branch by rule. Exception occured".format(line_id))
        raise Exception("Can't turn off {0} branch".format(line_id))


def update_all_rules():
    """Set next active rules for all branches."""
    try:
        for i in range(1, len(RULES_FOR_BRANCHES)):
            set_next_rule_to_redis(i, database.get_next_active_rule(i))
        logging.info("Rules updated")
    except Exception as e:
        logging.error("Exeption occured while updating all rules. {0}".format(e))


def sync_rules_from_redis():
    """Synchronize all rules that are present in redis."""
    try:
        for i in range(1, 18):
            RULES_FOR_BRANCHES[i] = get_next_rule_from_redis(i)
    except Exception as e:
        logging.error("Exeption occured while synchronizing rules from redis. {0}".format(e))
        raise e


def inspect_conditions():
    """Check if rule can be executed or not."""
    try:
        rain = database.select(database.QUERY[mn() + '_rain'].format(HOURS))[0][0]
        if rain is None:
            rain  = 0

        if rain < RAIN_MAX:
            return True
        else:
            logging.info("Rain volume for last {0} hours is {1}mm".format(HOURS, rain))
            return False
    except Exception as e:
        logging.error("Exeption occured while getting rain volume. {0}".format(e))
        return False


def send_to_viber_bot(rule):
    """Send messages to viber."""
    try:
        id = rule['id']
        rule_id = rule['rule_id']
        line_id = rule['line_id']
        time = rule['time']
        interval_id = rule['interval_id']
        user_friendly_name = rule['user_friendly_name']

        if (rule_id == 2):
            logging.debug("Turn off rule won't be send to viber")
            return

        arr = redis_db.lrange(REDIS_KEY_FOR_VIBER, 0, -1)
        logging.debug("{0} send rule was get from redis".format(arr))
        if (interval_id.encode() in arr):
            logging.info('interval_id {0} is already send'.format(interval_id))
            return

        try:
            payload = {'rule_id': id, 'line_id': line_id, 'time': time, 'interval_id': interval_id, 'users': USERS, 'timeout': VIBER_SENT_TIMEOUT, 'user_friendly_name': user_friendly_name}
            response = requests.post(VIBER_BOT_IP + '/notify_users_irrigation_started', json=payload, timeout=(7, 3))
            response.raise_for_status()
        except Exception as e:
            logging.error(e)
            logging.error("Can't send rule to viber. Ecxeption occured")
        finally:
            redis_db.rpush(REDIS_KEY_FOR_VIBER, interval_id)
            logging.debug("interval_id: {0} is added to redis".format(interval_id))
            time = 60 * 60 * 60 * 12
            redis_db.expire(REDIS_KEY_FOR_VIBER, time)
            logging.debug("REDIS_KEY_FOR_VIBER: {0} expires in 12 hours".format(REDIS_KEY_FOR_VIBER))
    except Exception as e:
        raise e


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
                if rule is None:
                    continue

                logging.info("Rule '{0}' is going to be executed".format(str(rule)))

                if (inspect_conditions() is False):
                    logging.info("Rule can't be executed cause of rain volume too high")
                    database.update(database.QUERY[mn() + "_canceled_by_rain"].format(rule['id']))
                    set_next_rule_to_redis(rule['line_id'], database.get_next_active_rule(rule['line_id']))
                    continue

                if (datetime.datetime.now() >= (rule['timer'] - datetime.timedelta(minutes=VIBER_SENT_TIMEOUT))):
                    try:
                        send_to_viber_bot(rule)
                    except Exception as e:
                        logging.error("Can't send rule {0} to viber. Exception occured. {1}".format(str(rule), e))

                if (datetime.datetime.now() >= rule['timer']):
                    logging.info("Rule '{0}' execution started".format(str(rule)))

                    try:
                        if rule['rule_id'] == 1:
                            branch_on(rule['line_id'], rule['time'])

                        if rule['rule_id'] == 2:
                            branch_off(rule['line_id'])

                    except Exception as e:
                        logging.error("Rule '{0}' can't be executed. Exception occured. {1}".format(str(rule), e))
                        # Set failed state
                        database.update(database.QUERY[mn() + '_cancel_interval'].format(rule['interval_id'], 3))
                        database.update(database.QUERY[mn()].format(rule['id'], 3))
                    else:
                        logging.info("Rule '{0}' is done.".format(str(rule)))
                        # Set ok state
                        database.update(database.QUERY[mn()].format(rule['id'], 2))
                    finally:
                        logging.debug("get next active rule")
                        set_next_rule_to_redis(rule['line_id'], database.get_next_active_rule(rule['line_id']))
    except Exception as e:
        logging.error("enable rule thread exception occured. {0}".format(e))
    finally:
        logging.info("enable rule thread stopped.")


if __name__ == "__main__":
    enable_rule()
