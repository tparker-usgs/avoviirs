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


def main():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://viirscollector:19091")

    while True:
        print("sending request")
        socket.send(b"gimme something to do")
        print("waiting for response")
        message = socket.recv()
        print("Received message {}. \nWhew. Let rest for 10 seconds.".format(message))
        time.sleep(10)


if __name__ == '__main__':
    main()
