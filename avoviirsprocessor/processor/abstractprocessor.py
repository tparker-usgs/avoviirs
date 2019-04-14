#!/usr/bin/env python

# -*- coding: utf-8 -*-

# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

""" Create a product.
"""

from abc import ABC,  abstractmethod
from datetime import timedelta

import tomputils.util as tutil
from pyresample import parse_area_file
from trollsched.satpass import Pass
from satpy.scene import Scene
from satpy import find_files_and_readers
from satpy.utils import debug_on
from satpy.writers import load_writer

ORBIT_SLACK = timedelta(minutes=30)
GRANULE_SPAN = timedelta(seconds=85.4)
GOLDENROD = (218, 165, 32)
PNG_DIR = '/viirs/png'
AREA_DEF = '/app/avoviirsprocessor/trollconfig/areas.def'
TYPEFACE = "/app/avoviirsprocessor/Cousine-Bold.ttf"
PPP_CONFIG_DIR = '/app/avoviirsprocessor/trollconfig'


class AbstractProcessor(ABC):
    def __init__(self, message):
        self.msg = message
        self.logger = tutil.setup_logging("msg_pub errors")
        debug_on()

        super(AbstractProcessor, self).__init__()

    @abstractmethod
    def is_familiar(topic):
        pass

    def process_message(self):
        self.logger.debug("Processing message: %s", self.msg.encode())
        data = self.msg.data
        filter_parameters = {'orbit': data['orbit_number']}
        filenames = find_files_and_readers(base_dir='/viirs/sdr',
                                           reader='viirs_sdr',
                                           ppp_config_dir=PPP_CONFIG_DIR,
                                           filter_parameters=filter_parameters)
        scn = Scene(filenames=filenames, reader='viirs_sdr')
        try:
            scn.load(['ir108'])
        except ValueError:
            self.logger.debug("No M15 data, skipping")
            return

        overpass = Pass(data['platform_name'], scn.start_time, scn.end_time,
                        instrument='viirs')
        for sector_def in parse_area_file(AREA_DEF):
            coverage = overpass.area_coverage(sector_def)
            self.logger.debug("{} coverage: {}".format(sector_def.area_id,
                                                       coverage))
            if coverage < .1:
                continue

            local = scn.resample(sector_def)
            print("writing {}".format(filename))
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
                                           sector_def.area_id, 'ir108')
            writer.save_dataset(local['ir108'], overlay=overlay,
                                decorate=decorate, filename=filename)


def processor_factory(message):
    topic = message.subject

    types = AbstractProcessor.__subclasses__()
    for type in types:
        if type.is_familiar(topic):
            return type(message)

    err_msg = "I don't know how to handle message topic {}".format(topic)
    raise NotImplementedError(err_msg)
