#!/usr/bin/env python

# -*- coding: utf-8 -*-

# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

""" assess processing health
"""

import zmq
import signal
import os
import time

UPDATE_PUBLISHER = "tcp://viirscollector:19191"
MAX_IDLE = 60 * 60
HEARTBEAT_FILE = "/tmp/heartbeat"


def sniff_queue(socket):
    while True:
        print(socket.recv_json())


def print_length(socket):
    print(socket.recv_json()["queue length"])


def main():
    # let ctrl-c work as it should.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    socket.connect(UPDATE_PUBLISHER)

    if socket.recv_json()["queue length"] > 0:
        st = os.stat(HEARTBEAT_FILE)
        if st.st_mtime < time.time() - MAX_IDLE:
            exit(1)


if __name__ == "__main__":
    main()
