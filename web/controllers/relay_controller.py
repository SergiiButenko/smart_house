#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import time
import RPi.GPIO as GPIO
from helpers import sqlite_database as database
from helpers.common import *

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

PUMP_PIN = 14
RAIN_PIN = 12
EXCEPT_PINS = [1, 2, 3, PUMP_PIN, RAIN_PIN]

BRANCHES = [
    {'id': 1, 'pin': 1, 'state': -1, 'mode': GPIO.OUT},
    {'id': 1, 'pin': 2, 'state': -1, 'mode': GPIO.OUT},
    {'id': 2, 'pin': 3, 'state': -1, 'mode': GPIO.OUT},
    {'id': 3, 'pin': 4, 'state': -1, 'mode': GPIO.OUT},
    {'id': 4, 'pin': 17, 'state': -1, 'mode': GPIO.OUT},
    {'id': 5, 'pin': 27, 'state': -1, 'mode': GPIO.OUT},
    {'id': 6, 'pin': 22, 'state': -1, 'mode': GPIO.OUT},
    {'id': 7, 'pin': 10, 'state': -1, 'mode': GPIO.OUT},
    {'id': 8, 'pin': 9, 'state': -1, 'mode': GPIO.OUT},
    {'id': 9, 'pin': 21, 'state': -1, 'mode': GPIO.OUT},
    {'id': 10, 'pin': 20, 'state': -1, 'mode': GPIO.OUT},
    {'id': 11, 'pin': 16, 'state': -1, 'mode': GPIO.OUT},
    {'id': 12, 'pin': 1, 'state': -1, 'mode': GPIO.OUT},
    {'id': 13, 'pin': 2, 'state': -1, 'mode': GPIO.OUT},
    {'id': 14, 'pin': 3, 'state': -1, 'mode': GPIO.OUT},
    {'id': 15, 'pin': 4, 'state': -1, 'mode': GPIO.OUT},
    {'id': 16, 'pin': 5, 'state': -1, 'mode': GPIO.OUT},
    {'id': 17, 'pin': PUMP_PIN, 'state': -1, 'mode': GPIO.OUT},
]

iteraion = 1


GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

for branch in BRANCHES:
    GPIO.setup(branch['pin'], branch['mode'], initial=GPIO.LOW)


def rissing(channel):
    """Fillup rain table"""
    global iteraion
    time.sleep(0.005)
    if GPIO.input(Input_Sig) == 1:
        logging.info("Event:{0}".format(iteraion))
        iteraion += 1

        database.update(database.QUERY[mn()].format(10))


GPIO.setup(RAIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(RAIN_PIN, GPIO.RISING, callback=rissing, bouncetime=200)


def on(pin):
    """Set pin to hight state."""
    try:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)
        return GPIO.input(pin)
    except Exception as e:
        logging.error("Exception occured when turning on {0} pin. {1}".format(pin, e))
        GPIO.cleanup()
        return -1


def off(pin):
    """Set pin to low state."""
    try:
        GPIO.output(pin, GPIO.LOW)
        return GPIO.input(pin)
    except Exception as e:
        logging.error("Exception occured when turning off {0} pin. {1}".format(pin, e))
        GPIO.cleanup()
        return -1


def check_if_no_active():
    """Check if any of branches is active now."""
    try:
        for branch in BRANCHES:
            # pump won't turn off, cause it stays on after branch off
            if branch['pin'] in EXCEPT_PINS:
                continue

            state = GPIO.input(branch['pin'])
            if state == GPIO.HIGH:
                logging.info("branch {0} is active".format(branch['id']))
                return False

        logging.info("No active branch")
        return True
    except Exception as e:
        logging.error("Exception occured when checking active {0}".format(e))
        GPIO.cleanup()
        raise e


def form_pins_state():
    """Form returns arr of dicts."""
    try:
        for branch in BRANCHES:
            branch['state'] = GPIO.input(branch['pin'])

        logging.debug("Pins state are {0}".format(str(BRANCHES)))

        return BRANCHES
    except Exception as e:
        logging.error("Exception occured during forming of branches status. {0}".format(e))
        GPIO.cleanup()
        return None


def branch_on(branch_id=None, branch_alert=None, pump_enable=True):
    """Turn on branch by id."""
    if (branch_id is None):
        logging.error("No branch id")
        return None

    if (branch_alert is None):
        logging.error("No branch alert time")
        return None

    on(BRANCHES[branch_id]['pin'])

    if pump_enable is False:
        logging.info("Pump won't be turned on with {0} branch id".format(branch_id))
    else:
        on(PUMP_PIN)
        logging.info("Pump turned on with {0} branch id".format(branch_id))

    return form_pins_state()


def branch_off(branch_id=None, pump_enable=True):
    """Turn off branch by id."""
    if (branch_id is None):
        logging.error("No branch id")
        return None

    off(BRANCHES[branch_id]['pin'])

    if pump_enable is True and check_if_no_active():
        off(PUMP_PIN)
        logging.info("Pump turned off with {0} branch id".format(branch_id))
    else:
        logging.info("Pump won't be turned off with {0} branch id".format(branch_id))

    return form_pins_state()


def branch_status():
    """Return status of raspberryPi relay."""
    try:
        return form_pins_state()
    except Exception as e:
        logging.error(e)
        logging.error("Can't get raspberryPi status. Exception occured")
        return None
