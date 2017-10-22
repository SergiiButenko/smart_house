#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import time
import RPi.GPIO as GPIO


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)


BRANCHES = [
{'id': 0, 'pin': 17, 'state': -1, 'mode', GPIO.IN},
{'id': 1, 'pin': 1, 'state': -1, 'mode', GPIO.OUT},
{'id': 2, 'pin': 2, 'state': -1, 'mode', GPIO.OUT},
{'id': 3, 'pin': 3, 'state': -1, 'mode', GPIO.OUT},
{'id': 4, 'pin': 4, 'state': -1, 'mode', GPIO.OUT},
{'id': 5, 'pin': 5, 'state': -1, 'mode', GPIO.OUT},
{'id': 6, 'pin': 6, 'state': -1, 'mode', GPIO.OUT},
{'id': 7, 'pin': 7, 'state': -1, 'mode', GPIO.OUT},
{'id': 8, 'pin': 8, 'state': -1, 'mode', GPIO.OUT},
{'id': 9, 'pin': 9, 'state': -1, 'mode', GPIO.OUT},
{'id': 10, 'pin': 10, 'state': -1, 'mode', GPIO.OUT},
{'id': 11, 'pin': 11, 'state': -1, 'mode', GPIO.OUT},
{'id': 12, 'pin': 12, 'state': -1, 'mode', GPIO.OUT},
{'id': 13, 'pin': 13, 'state': -1, 'mode', GPIO.OUT},
{'id': 14, 'pin': 14, 'state': -1, 'mode', GPIO.OUT},
{'id': 15, 'pin': 15, 'state': -1, 'mode', GPIO.OUT},
{'id': 16, 'pin': 16, 'state': -1, 'mode', GPIO.OUT}
]

GPIO.setmode(GPIO.BCM)

for branch in BRANCHES:
    GPIO.setup(branch['pin'], branch['mode'])


def on(pin):
    try:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)
        return GPIO.input(pin)
    except Exception as e:
        logging.error("Exception occured when turning on {0} pin".format(pin))
        return -1


def off(pin):
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
