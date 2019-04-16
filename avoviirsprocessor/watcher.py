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
from datetime import timedelta
import tomputils.util as tutil
from pyresample import parse_area_file
from trollsched.satpass import Pass
from satpy.scene import Scene
from satpy import find_files_and_readers
from satpy.writers import load_writer

REQUEST_TIMEOUT = 10000
TASK_SERVER = "tcp://viirscollector:19091"
UPDATE_PUBLISHER = "tcp://viirscollector:19191"

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


class Updater(threading.Thread):
    def __init__(self, context):
        threading.Thread.__init__(self)
        self.socket = context.socket(zmq.SUB)
        self.socket.connect(UPDATE_PUBLISHER)

    def run(self):
        if self.socket.recv_string():
            global task_waiting
            task_waiting = True
            logger.debug("Task waiting")
        else:
            task_waiting = False
            logger.debug("No task waiting")


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
        scn.load([product])
    except KeyError:
        logger.error("I don't know how to make a %s", product)
        logger.error("I know: {}".format(scn.all_composite_names()))
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
        filename_str = "{}/{}.{}.{}.--.{}.{}.png"
        filename = filename_str.format(PNG_DIR, time_str, data['orbit'],
                                       data['sensor'][0], sector_def.area_id,
                                       product)
        print("writing {}".format(filename))
        writer.save_dataset(local[product], overlay=overlay,
                            decorate=decorate, filename=filename)


def main():
    # let ctrl-c work as it should.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    global logger
    logger = tutil.setup_logging("avoviirsprocessor.watcher errors")

    context = zmq.Context()

    updater = Updater(context)
    updater.start()

    client = context.socket(zmq.REQ)
    client.connect(TASK_SERVER)

    while True:
        if task_waiting:
            logger.debug("sending request")
            client.send(b"gimme something to do")
            logger.debug("waiting for response")
            msg_bytes = client.recv()
            if msg_bytes:
                try:
                    msg = Message.decode(msg_bytes)
                    process_message(msg)
                except MessageError as e:
                    logger.error("Message decode error.")
                    logger.exception(e)
                logger.debug("Whew, that was hard. Let rest for 10 seconds.")
                time.sleep(10)
        time.sleep(1)


if __name__ == '__main__':
    main()
