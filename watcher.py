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
from avoviirsprocessor.processor import publish_products
from avoviirsprocessor import logger
from avoviirsprocessor.coreprocessors import TIR, MIR, BTD, VIS  # NOQA
import tomputils.util as tutil
from pathlib import Path

HEARTBEAT_FILE = "/tmp/heartbeat"

REQUEST_TIMEOUT = 10000
TASK_SERVER = "tcp://viirscollector:19091"
UPDATE_PUBLISHER = "tcp://viirscollector:19191"


class UpdateSubscriber(threading.Thread):
    def __init__(self, context):
        threading.Thread.__init__(self)
        self.socket = context.socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.socket.connect(UPDATE_PUBLISHER)
        self.task_waiting = False

    def run(self):
        while True:
            update = self.socket.recv_json()
            self.task_waiting = update["queue length"] > 0


def process_message(msg_bytes):
    try:
        message = Message.decode(msg_bytes)
        publish_products(message)
    except MessageError:
        logger.exception("Message decode error.")
    except NotImplementedError:
        logger.exception("Crap. I accepted a message I can't process.")
    except ValueError:
        logger.exception("I got a message, but couldn't find the data")
    except KeyError:
        logger.exception("missing data, skipping")

    Path(HEARTBEAT_FILE).touch()
    logger.debug("Whew, that was hard. Let rest for 10 seconds.")
    time.sleep(10)


def main():
    # let ctrl-c work as it should.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    context = zmq.Context()
    logger.debug("starting update_subscriber")
    update_subscriber = UpdateSubscriber(context)
    update_subscriber.start()
    logger.debug("started update_subscriber")

    task_client = context.socket(zmq.REQ)
    task_client.connect(TASK_SERVER)

    desired_products = tutil.get_env_var("VIIRS_PRODUCTS")
    desired_products = desired_products.split(",")

    while True:
        if update_subscriber.task_waiting:
            request = {"desired products": desired_products}
            task_client.send_json(request)
            msg_bytes = task_client.recv()
            if msg_bytes:
                process_message(msg_bytes)
            else:
                time.sleep(1)
        else:
            time.sleep(1)


if __name__ == "__main__":
    main()
