#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import time
import RPi.GPIO as GPIO


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)


BRANCHES = [
{'id': 0, 'pin': 1, 'state': -1},
{'id': 1, 'pin': 1, 'state': -1},
{'id': 2, 'pin': 1, 'state': -1},
{'id': 3, 'pin': 1, 'state': -1},
{'id': 4, 'pin': 1, 'state': -1},
{'id': 5, 'pin': 1, 'state': -1},
{'id': 6, 'pin': 1, 'state': -1},
{'id': 7, 'pin': 1, 'state': -1},
{'id': 8, 'pin': 1, 'state': -1},
{'id': 9, 'pin': 1, 'state': -1},
{'id': 10, 'pin': 1, 'state': -1},
{'id': 11, 'pin': 1, 'state': -1},
{'id': 12, 'pin': 1, 'state': -1},
{'id': 13, 'pin': 1, 'state': -1},
{'id': 14, 'pin': 1, 'state': -1},
{'id': 15, 'pin': 1, 'state': -1},
{'id': 16, 'pin': 1, 'state': -1}
]

GPIO.setmode(GPIO.BCM)

for branch in BRANCHES:
    GPIO.setup(branch['pin'], GPIO.OUT)


def on(pin):
    try:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)
        return GPIO.input(pin)
    except Exception as e:
        logging.error("Exception occured when turning on {0} pin".format(pin))
        return -1


def off():
    try:
        GPIO.output(pin, GPIO.LOW)
        return GPIO.input(pin)
    except Exception as e:
        logging.error("Exception occured when turning off {0} pin".format(pin))
        return -1


def check_if_no_active():
    try:
        for branch in BRANCHES:
            state = GPIO.input(branch['pin'])
            if state is False:
                return state

        logging.info("No active branch")
        return True
    except Exception as e:
        logging.error("Exception occured. {0}".format(e))
        GPIO.cleanup()
        raise e


def form_pins_state():
    try:
        for branch in BRANCHES:
            branch['state'] = GPIO.input(branch['pin'])

        logging.info("Pins state is {0}".format(str(BRANCHES)))

        return BRANCHES
    except Exception as e:
        logging.error("Exception occured during forming of branches status. {0}".format(e))
        return None


def branch_on(branch_id=None, branch_alert=None, pump_enable=True):
    if (branch_id is None):
        logging.error("No branch id")
        return None

    if (branch_alert is None):
        logging.error("No branch alert time")
        return None

    if pump_enable is False:
        logging.info("Pump won't be turned on for {0} branch id".format(branch_id))
        on(17)

    on(BRANCHES[branch_id]['pin'])

    return form_pins_state()


def branch_off(branch_id=None, pump_enable=True):
    if (branch_id is None):
        logging.error("No branch id")
        return None

    if check_if_no_active():
        off(17)

    off(BRANCHES[branch_id]['pin'])

    return form_pins_state()


def branch_status():
    """Return status of arduino relay."""
    try:
        return form_pins_state()
    except Exception as e:
        logging.error(e)
        logging.error("Can't get arduino status. Exception occured")
        return None
