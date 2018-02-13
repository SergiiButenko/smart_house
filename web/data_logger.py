#!/usr/bin/python3
# -*- coding: utf-8 -*-
from pyfirmata import ArduinoMega, util
import serial.tools.list_ports
import logging
import time
from helpers import sqlite_database as database
from helpers.common import *
ANALOG_PIN = 16

PINS = list(range(12, 28))

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)


def find_arduino(serial_number):
    ports = list(serial.tools.list_ports.comports())
    return ports[0][0]

    # for pinfo in serial.tools.list_ports.comports():
    #     if pinfo.serial_number == serial_number:
    #         return serial.Serial(pinfo.device)
    # raise IOError("Could not find an arduino - is it plugged in?")


def inverse(val):
    logging.info('   not inversed value {0}'.format(val))
    return 1 - val


# For get function name intro function. Usage mn(). Return string with current function name. Instead 'query' will be QUERY[mn()].format(....)
def moisture_sensors():
    try:
        logging.info('Finding arduino...')
        serial_port = find_arduino(serial_number='556393131333516090E0')
        logging.info('Serial port {0}'.format(serial_port))

        logging.info('Connecting to arduino...')
        board = ArduinoMega(serial_port)
        logging.info('Connected')

        logging.info('Starting thread...')
        it = util.Iterator(board)
        it.start()
        time.sleep(5)
        logging.info('Started')

        for x in range(0, ANALOG_PIN):
            logging.info('Enable reporting for {0} analog pin...'.format(x))
            board.analog[x].enable_reporting()
            time.sleep(1)
            logging.info('Reading from {0} analog pin...'.format(x))

            avr = 0
            for i in range(0, 11):
                # 0 - 100%
                # 1 - 0%
                val = inverse(board.analog[x].read())
                avr = avr + val
                logging.info('   value {0}'.format(val))
                time.sleep(1)

            avr = round(avr / 10, 4)
            logging.info('Avr value {0}'.format(avr))

            database.update(database.QUERY[mn()].format(PINS[x], avr))

            time.sleep(1)
            logging.info('Disable reporting for {0} analog pin...'.format(x))
            board.analog[x].disable_reporting()
            time.sleep(5)

        time.sleep(10)
        try:
            logging.info('Stopping serial')
            board.exit()
            logging.info('done')
        except Exception as e:
            logging.warn('Expected TypeError occured. Trying one more time. {0}'.format(e))
            board.exit()
            logging.info('done')

    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    moisture_sensors()
