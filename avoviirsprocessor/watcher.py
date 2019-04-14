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
from datetime import timedelta
import tomputils.util as tutil
from pyresample import parse_area_file
from trollsched.satpass import Pass
from satpy.scene import Scene
from satpy import find_files_and_readers
from satpy.writers import load_writer


REQUEST_TIMEOUT = 10000
SERVER_ENDPOINT = "tcp://viirscollector:19091"

ORBIT_SLACK = timedelta(minutes=30)
GRANULE_SPAN = timedelta(seconds=85.4)
GOLDENROD = (218, 165, 32)
PNG_DIR = '/data/omps/png'
PNG_DEV_DIR = '/data/omps/png-dev'
AREA_DEF = '/app/trollConfig/areas.def'
TYPEFACE = "/app/fonts/Cousine-Bold.ttf"
ORBIT_SLACK = timedelta(minutes=30)
GRANULE_SPAN = timedelta(seconds=85.4)
GOLDENROD = (218, 165, 32)
PNG_DIR = '/viirs/png'
AREA_DEF = '/app/avoviirsprocessor/trollconfig/areas.def'
TYPEFACE = "/app/avoviirsprocessor/Cousine-Bold.ttf"
PPP_CONFIG_DIR = '/app/avoviirsprocessor/trollconfig'


def process_message(msg):
    logger.debug("Processing message: %s", msg.encode())
    data = msg.data
    product = msg.subject.split("/")[-1]
    print("TOMP SAYS PRODUCT {}".format(product))
    filter_parameters = {'orbit': data['orbit_number']}
    filenames = find_files_and_readers(base_dir='/viirs/sdr',
                                       reader='viirs_sdr',
                                       ppp_config_dir=PPP_CONFIG_DIR,
                                       filter_parameters=filter_parameters)
    scn = Scene(filenames=filenames, reader='viirs_sdr')
    try:
        scn.load(str(product))
    except KeyError:
        logger.error("TOMP SAYS I don't know how to make a :{}: :{}:".format(type(product), type('ir108')))
        logger.error("I only know how to make a {}".format(scn.all_composite_names()))
        return
    except ValueError:
        logger.debug("No M15 data, skipping")
        return

    overpass = Pass(data['platform_name'], scn.start_time, scn.end_time,
                    instrument='viirs')
    for sector_def in parse_area_file(AREA_DEF):
        coverage = overpass.area_coverage(sector_def)
        logger.debug("{} coverage: {}".format(sector_def.area_id,
                                              coverage))
        if coverage < .1:
            continue

        local = scn.resample(sector_def)
        overlay = {'coast_dir': '/usr/local/gshhg',
                   'color': GOLDENROD,
                   'width': 1,
                   'level_coast': 1,
                   'level_borders': 2}

        start_string = data['start_time'].strftime('%m/%d/%Y %H:%M UTC')
        label = "{} {} VIIRS thermal infrared brightness temperature(C)"
        label = label.format(start_string, data['platform_name'])

        text = {'text': {'txt': label,
                         'align': {'top_bottom': 'bottom',
                                   'left_right': 'right'},
                         'font': TYPEFACE,
                         'font_size': 14,
                         'height': 30,
                         'bg': 'black',
                         'bg_opacity': 128,
                         'line': GOLDENROD}}
        decorate = {'decorate': [text]}

        writer, save_kwargs = load_writer('simple_image')
        time_str = data['start_time'].strftime('%Y%m%d.%H%M')
        filename_str = "{}/{}.{}.--.--.{}.{}.png"
        filename = filename_str.format(PNG_DIR, time_str, data['sensor'],
                                       sector_def.area_id, product)
        print("writing {}".format(filename))
        writer.save_dataset(local[product], overlay=overlay,
                            decorate=decorate, filename=filename)


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
                process_message(msg)
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
