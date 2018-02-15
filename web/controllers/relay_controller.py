#!/usr/bin/python3
# -*- coding: utf-8 -*-
from pyfirmata import Arduino, util
import serial.tools.list_ports
import logging
import time
from helpers import sqlite_database as database
from helpers.common import *

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

PUMP_PIN = 12
RAIN_PIN = 13
# 1,2,3 goes to light activities
EXCEPT_PINS = [1, 2, 3, PUMP_PIN, RAIN_PIN]
RAIN_BUCKET_ITERATION = 1

BRANCHES = [
    # {'id': 1, 'pin': 3, 'state': -1},
    # {'id': 1, 'pin': 3, 'state': -1},
    # {'id': 2, 'pin': 3, 'state': -1},
    # {'id': 3, 'pin': 3, 'state': -1},
    # {'id': 4, 'pin': 3, 'state': -1},
    # {'id': 5, 'pin': 3, 'state': -1},
    # {'id': 6, 'pin': 3, 'state': -1},
    # {'id': 7, 'pin': 3, 'state': -1},
    # {'id': 8, 'pin': 3, 'state': -1},
    # {'id': 9, 'pin': 3, 'state': -1},
    # {'id': 10, 'pin': 3, 'state': -1},
    # {'id': 11, 'pin': 3, 'state': -1},
    {'id': 12, 'pin': 3, 'state': -1},
    {'id': 13, 'pin': 4, 'state': -1},
    {'id': 14, 'pin': 5, 'state': -1},
    {'id': 15, 'pin': 6, 'state': -1},
    {'id': 16, 'pin': 7, 'state': -1}
    # {'id': 17, 'pin': PUMP_PIN, 'state': -1},
]


def find_arduino(serial_number):
    ports = list(serial.tools.list_ports.comports())
    return ports[0][0]


logging.info('Finding arduino...')
serial_port = find_arduino(serial_number='556393131333516090E0')
logging.info('Serial port {0}'.format(serial_port))

logging.info('Connecting to arduino...')
board = Arduino(serial_port)
logging.info('Connected')


def on(pin):
    """Set pin to hight state."""
    try:
        global board
        board.digital[pin].write(1)
        time.sleep(1)
        return board.digital[pin].read()
    except Exception as e:
        logging.error("Exception occured when turning on {0} pin. {1}".format(pin, e))
        return -1


def off(pin):
    """Set pin to low state."""
    try:
        global board
        board.digital[pin].write(0)
        time.sleep(1)
        return board.digital[pin].read()
    except Exception as e:
        logging.error("Exception occured when turning on {0} pin. {1}".format(pin, e))
        return -1


def check_if_no_active():
    """Check if any of branches is active now."""
    try:
        global board
        for branch in BRANCHES:
            # pump won't turn off, cause it stays on after branch off
            if branch['pin'] in EXCEPT_PINS:
                continue

            state = board.digital[branch['pin']].read()
            if state == 1:
                logging.info("branch {0} is active".format(branch['id']))
                return False

        logging.info("No active branch")
        return True
    except Exception as e:
        logging.error("Exception occured when checking active {0}".format(e))
        raise e


def form_pins_state():
    """Form returns arr of dicts."""
    try:
        global board
        for branch in BRANCHES:
            branch['state'] = board.digital[branch['pin']].read()
            time.sleep(0.5)

        logging.debug("Pins state are {0}".format(str(BRANCHES)))

        return BRANCHES
    except Exception as e:
        logging.error("Exception occured during forming of branches status. {0}".format(e))
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
