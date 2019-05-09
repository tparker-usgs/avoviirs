#!/usr/bin/env python

# -*- coding: utf-8 -*-

# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

""" display task_broker updates
"""

import zmq


UPDATE_PUBLISHER = "tcp://viirscollector:19191"


def main():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    socket.connect(UPDATE_PUBLISHER)

    while True:
        print(socket.recv_json())


if __name__ == '__main__':
    main()
