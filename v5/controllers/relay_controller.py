#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import time
import RPi.GPIO as GPIO


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

PUMP_PIN = 17

BRANCHES = [
    {'id': 1, 'pin': 1, 'state': -1, 'mode': GPIO.OUT},
    {'id': 1, 'pin': 1, 'state': -1, 'mode': GPIO.OUT},
    {'id': 2, 'pin': 2, 'state': -1, 'mode': GPIO.OUT},
    {'id': 3, 'pin': 3, 'state': -1, 'mode': GPIO.OUT},
    {'id': 4, 'pin': 4, 'state': -1, 'mode': GPIO.OUT},
    {'id': 5, 'pin': 5, 'state': -1, 'mode': GPIO.OUT},
    {'id': 6, 'pin': 6, 'state': -1, 'mode': GPIO.OUT},
    {'id': 7, 'pin': 7, 'state': -1, 'mode': GPIO.OUT},
    {'id': 8, 'pin': 8, 'state': -1, 'mode': GPIO.OUT},
    {'id': 9, 'pin': 9, 'state': -1, 'mode': GPIO.OUT},
    {'id': 10, 'pin': 10, 'state': -1, 'mode': GPIO.OUT},
    {'id': 11, 'pin': 11, 'state': -1, 'mode': GPIO.OUT},
    {'id': 12, 'pin': 12, 'state': -1, 'mode': GPIO.OUT},
    {'id': 13, 'pin': 13, 'state': -1, 'mode': GPIO.OUT},
    {'id': 14, 'pin': 14, 'state': -1, 'mode': GPIO.OUT},
    {'id': 15, 'pin': 15, 'state': -1, 'mode': GPIO.OUT},
    {'id': 16, 'pin': 16, 'state': -1, 'mode': GPIO.OUT},
    {'id': 17, 'pin': PUMP_PIN, 'state': -1, 'mode': GPIO.OUT}
]


GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

for branch in BRANCHES:
    GPIO.setup(branch['pin'], branch['mode'], initial=GPIO.LOW)


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
            state = GPIO.input(branch['pin'])
            if state == GPIO.HIGH:
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

        logging.info("Pins state are {0}".format(str(BRANCHES)))

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
