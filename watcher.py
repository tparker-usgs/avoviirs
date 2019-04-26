#!/usr/bin/env python

# -*- coding: utf-8 -*-

# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

""" Request a task.
"""

import zmq
import time
import signal
import threading

from posttroll.message import Message, MessageError
from avoviirsprocessor.processor import processor_factory
from avoviirsprocessor import logger
from avoviirsprocessor.coreprocessors import TIR, MIR, BTD, VIS # NOQA
import tomputils.util as tutil


REQUEST_TIMEOUT = 10000
TASK_SERVER = "tcp://viirscollector:19091"
UPDATE_PUBLISHER = "tcp://viirscollector:19191"


class Updater(threading.Thread):
    def __init__(self, context):
        threading.Thread.__init__(self)
        self.socket = context.socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.socket.connect(UPDATE_PUBLISHER)
        self.task_waiting = False

    def run(self):
        while True:
            update = self.socket.recv_json()
            self.task_waiting = update['queue length'] > 0


def process_message(msg_bytes):
    try:
        msg = Message.decode(msg_bytes)
        processor = processor_factory(msg)
        processor.process_message()
    except MessageError as e:
        logger.error("Message decode error.")
        logger.exception(e)
    except NotImplementedError as e:
        logger.exception(e)
    logger.debug("Whew, that was hard. Let rest for 9 seconds.")
    time.sleep(10)


def main():
    # let ctrl-c work as it should.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    context = zmq.Context()
    logger.debug("starting updater")
    updater = Updater(context)
    updater.start()
    logger.debug("started updater")

    client = context.socket(zmq.REQ)
    client.connect(TASK_SERVER)

    while True:
        if updater.task_waiting:
            desired_products = tutil.get_env_var('VIIRS_PRODUCTS')
            desired_products = desired_products.split(',')
            request = {'desired products': desired_products}
            client.send_json(request)
            msg_bytes = client.recv()
            if msg_bytes:
                process_message(msg_bytes)
            else:
                time.sleep(1)
        else:
            time.sleep(1)


if __name__ == '__main__':
    main()
