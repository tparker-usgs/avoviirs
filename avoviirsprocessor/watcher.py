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
from pyresample import parse_area_file
from trollsched.satpass import Pass
from satpy.scene import Scene
from satpy import find_files_and_readers
from satpy.writers import load_writer
from avoviirsprocessor.processor import processor_factory, VOLCVIEW_BANDS
from avoviirsprocessor import logger


REQUEST_TIMEOUT = 10000
TASK_SERVER = "tcp://viirscollector:19091"
UPDATE_PUBLISHER = "tcp://viirscollector:19191"
GOLDENROD = (218, 165, 32)
PNG_DIR = '/viirs/png'
AREA_DEF = '/app/avoviirsprocessor/trollconfig/areas.def'
TYPEFACE = "/app/avoviirsprocessor/Cousine-Bold.ttf"
COVERAGE_LIMIT = .1
IMAGE_LABEL = {
    'mir': 'mid-infrared brightness temperature (c)',
    'tir': 'thermal infrared brightness tempeerature (c)',
    'btd': 'brightness temperature difference',
    'vis': 'true color'
}


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


def process_message(msg):
    logger.debug("Processing message: %s", msg.encode())
    data = msg.data
    product = msg.subject.split("/")[-1]
    filter_parameters = {'start_time': data['start_time'],
                         'end_time': data['end_time'],
                         'platform_name': data['platform_name']}
    filenames = find_files_and_readers(base_dir='/viirs/sdr',
                                       reader='viirs_sdr',
                                       filter_parameters=filter_parameters)
    scn = Scene(filenames=filenames, reader='viirs_sdr')
    try:
        scn.load([product])
    except KeyError:
        logger.error("I don't know how to make a %s", product)
        return
    except ValueError:
        logger.debug("I don't have the channels needed to generate %s",
                     product)
        return

    overpass = Pass(data['platform_name'], scn.start_time, scn.end_time,
                    instrument='viirs')
    for sector_def in parse_area_file(AREA_DEF):
        coverage = overpass.area_coverage(sector_def)
        logger.debug("{} coverage: {}".format(sector_def.area_id,
                                              coverage))
        if coverage < COVERAGE_LIMIT:
            continue

        local = scn.resample(sector_def)
        overlay = {'coast_dir': '/usr/local/gshhg',
                   'color': GOLDENROD,
                   'width': 1,
                   'level_coast': 1
                   }

        start_string = data['start_time'].strftime('%m/%d/%Y %H:%M UTC')
        label = "{} {} VIIRS thermal infrared brightness temperature(C)"
        label = label.format(start_string, data['platform_name'],
                             data['sensor'], IMAGE_LABEL[product])

        text = {'text': {'txt': label,
                         'align': {'top_bottom': 'bottom',
                                   'left_right': 'left'},
                         'font': TYPEFACE,
                         'font_size': 14,
                         'height': 30,
                         'bg': 'black',
                         'bg_opacity': 128,
                         'line': GOLDENROD}}
        decorate = {'decorate': [text]}

        writer, save_kwargs = load_writer('simple_image')
        time_str = data['start_time'].strftime('%Y%m%d.%H%M')
        filename_str = "{}/testing-{}-{}-{}-{}-{}.png"
        filename = filename_str.format(PNG_DIR, time_str, data['orbit_number'],
                                       data['platform_name'],
                                       sector_def.area_id, product)

        print("writing {}".format(filename))
        writer.save_dataset(local[product], overlay=overlay,
                            decorate=decorate, fill_value=0,
                            filename=filename)
    logger.debug("All done with this taks.")


def receive_message(msg_bytes):
    try:
        msg = Message.decode(msg_bytes)
        processor = processor_factory(msg)
        processor.process_message()
    except MessageError as e:
        logger.error("Message decode error.")
        logger.exception(e)
    except NotImplementedError as e:
        logger.exception(e)
    logger.debug("Whew, that was hard. Let rest for 10 seconds.")
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
            request = {'desired products': VOLCVIEW_BANDS.keys()}
            client.send_json(request)
            msg_bytes = client.recv()
            if msg_bytes:
                receive_message(msg_bytes)
            else:
                time.sleep(1)
        else:
            time.sleep(1)


if __name__ == '__main__':
    main()
