#!/usr/bin/python3
# -*- coding: utf-8 -*-
from pyfirmata import Arduino, util
import serial.tools.list_ports
import logging
import time
from helpers import sqlite_database as database
from helpers.common import *

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)


def find_arduino(serial_number):
    ports = list(serial.tools.list_ports.comports())
    return ports[0]

    # for pinfo in serial.tools.list_ports.comports():
    #     if pinfo.serial_number == serial_number:
    #         return serial.Serial(pinfo.device)
    # raise IOError("Could not find an arduino - is it plugged in?")


# For get function name intro function. Usage mn(). Return string with current function name. Instead 'query' will be QUERY[mn()].format(....)
def arduino():
    try:
        serial_port = find_arduino(serial_number='556393131333516090E0')
        board = Arduino(serial_port)
        it = util.Iterator(board)
        it.start()

        for x in xrange(0, 5):
            logging.info('Enable reporting for {0} analog pin'.format(x))
            board.analog[x].enable_reporting()
            time.sleep(1)

        for x in xrange(1, 5):
            logging.info('Reading from {0} analog pin: {1}'.format(x, board.analog[x].read()))
            time.sleep(1)

        board.exit()
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    arduino()
