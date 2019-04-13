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

from posttroll.message import Message
import avoviirsprocessor.processor as processor
from datetime import timedelta
import tomputils.util as tutil

REQUEST_TIMEOUT = 10000
SERVER_ENDPOINT = "tcp://viirscollector:19091"

ORBIT_SLACK = timedelta(minutes=30)
GRANULE_SPAN = timedelta(seconds=85.4)
GOLDENROD = (218, 165, 32)
PNG_DIR = '/data/omps/png'
PNG_DEV_DIR = '/data/omps/png-dev'
AREA_DEF = '/app/trollConfig/areas.def'
TYPEFACE = "/app/fonts/Cousine-Bold.ttf"


def main():
    # let ctrl-c work as it should.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    global logger
    logger = tutil.setup_logging("avoviirsprocessor.watcher errors")

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(SERVER_ENDPOINT)

    poll = zmq.Poller()
    poll.register(socket, zmq.POLLIN)

    while True:
        logger.debug("sending request")
        socket.send(b"gimme something to do")
        logger.debug("waiting for response")
        socks = dict(poll.poll(REQUEST_TIMEOUT))
        if socks.get(socket) == zmq.POLLIN:
            try:
                logger.debug("getting message")
                msg_bytes = socket.recv(zmq.NOBLOCK)
                msg = Message.decode(msg_bytes)
                proc = processor.processor_factory(msg)
                proc.process_message()
                logger.debug("Whew, that was hard. Let rest for 10 seconds.")
                time.sleep(10)
            except zmq.Again:
                logger.debug("message was there, now it's gone")

        else:
            logger.debug("Nothing better to do, lets reconnect")
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()
            poll.unregister(socket)
            # Create new connection
            socket = context.socket(zmq.REQ)
            socket.connect(SERVER_ENDPOINT)
            poll.register(socket, zmq.POLLIN)


if __name__ == '__main__':
    main()
