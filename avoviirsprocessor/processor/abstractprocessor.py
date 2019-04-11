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

# import json
# from posttroll.subscriber import Subscribe
# from posttroll.message import datetime_encoder
# from pprint import pprint
# from datetime import timedelta, datetime
# from pyorbital.orbital import Orbital
# from mpop.utils import debug_on
# from mpop.projector import get_area_def
# from pydecorate import DecoratorAGG
# import aggdraw
# import os
# import os.path
# import tomputils.mattermost as mm
# import sys
# import traceback
# from trollimage.colormap import rainbow
# import numpy as np
# from pycoast import ContourWriterAGG
# from trollimage.image import Image
# from pyresample.utils import parse_area_file

ORBIT_SLACK = timedelta(minutes=30)
GRANULE_SPAN = timedelta(seconds=85.4)
GOLDENROD = (218, 165, 32)
PNG_DIR = '/viirs/png'
AREA_DEF = '/app/avoviirsprocessor/trollconfig/areas.def'
TYPEFACE = "/app/avoviirsprocessor/Cousine-Bold.ttf"


class AbstractProcessor(ABC):
    def __init__(self, message):
        self.msg = message
        self.logger = tutil.setup_logging("msg_pub errors")

        super(AbstractProcessor, self).__init__()

    @abstractmethod
    def is_familiar(topic):
        pass

    def process_message(self):
        self.logger.debug("Processing message: %s", self.msg.encode())
        data = self.msg.data
        scn = Scene(start_time=data['start_time'], end_time=['end_time'],
                    reader='viirs_sdr')
        try:
            scn.load(['M15'])
        except ValueError:
            self.logger.debug("No M15 data, skipping")
            return

        overpass = Pass(self.msg.d, scn.start_time, scn.end_time,
                        instrument='viirs')
        for sector_def in parse_area_file(AREA_DEF):
            coverage = overpass.area_coverage(sector_def)
            self.logger.debug("{} coverage: {}".format(sector_def.area_id,
                                                       coverage))
            if coverage < .1:
                continue

            local = scn.resample(sector_def)
            filename = "/virrs/sdr/M15-{}.png".format(sector_def.area_id)
            print("writing {}".format(filename))
            local.save_dataset('M15', filename=filename)


def processor_factory(message):
    topic = message.subject

    types = AbstractProcessor.__subclasses__()
    for type in types:
        if type.is_familiar(topic):
            return type(message)

    err_msg = "I don't know how to handle message topic {}".format(topic)
    raise NotImplementedError(err_msg)
