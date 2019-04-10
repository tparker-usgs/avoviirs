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

import dateutil
import tomputils.util as tutil
from pyresample.utils import parse_area_file
# from trollsched.satpass import Pass

# import json
# from posttroll.subscriber import Subscribe
# from posttroll.message import datetime_encoder
# from pprint import pprint
# from datetime import timedelta, datetime
# from dateutil import parser
# from pyorbital.orbital import Orbital
# from mpop.utils import debug_on
# from trollsched.satpass import Pass
# from mpop.projector import get_area_def
# from pydecorate import DecoratorAGG
# import aggdraw
# import os
# import os.path
# import tomputils.mattermost as mm
# import sys
# import traceback
# from satpy.scene import Scene
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

        for sector_def in parse_area_file(AREA_DEF):
            self.logger.debug("Found area %s for topic %s", sector_def.area_id,
                              self.msg.subject)

        start = dateutil.parser.parse(self.msg.data["start_time"])
        end = start + GRANULE_SPAN
        start_slack = start - ORBIT_SLACK
        self.logger.debug("start %s :: %s", start_slack, type(start_slack))
        self.logger.debug("end %s :: %s", end, type(end))
        # base_dir = "/viirs/sdr"
        # overpass = Pass("SUOMI NPP", start_slack, end, instrument='omps')
        #
        # images = []
        # colorbar_text_color = GOLDENROD
        # img_colormap = None
        # dev = False
        # for sector_def in parse_area_file(AREA_DEF):
        #     coverage = overpass.area_coverage(sector_def)
        #     print("%s coverage: %f" % (sector_def.area_id, coverage))
        #
        #     if coverage < .1:
        #         continue
        #
        #     global_scene = Scene(platform_name="SUOMI NPP", sensor="omps",
        #                          start_time=start, end_time=end,
        #                          base_dir=base_dir,
        #                          reader=reader)
        #     global_scene.load(['so2_trm'])
        #     local = global_scene.resample(sector_def,
        #                                   radius_of_influence=100000)
        #     ma = np.ma.masked_outside(local.datasets['so2_trm'], 0.5, 2)
        #     mask = ma.mask
        #     if mask.all():
        #         continue
        #     local.datasets['so2_trm'] = np.ma.masked_where(mask,
        #                                                    local.datasets[
        #                                                        'so2_trm'])
        #     so2_max = np.nanmax(local.datasets['so2_trm'])
        #     so2_min = np.nanmin(local.datasets['so2_trm'])
        #     so2_count = local.datasets['so2_trm'].count()
        #
        #     if so2_max < 1:
        #         continue
        #
        #     images.append((sector_def.area_id, so2_count, so2_max))
        #
        #     # plot
        #     img = Image(local['so2_trm'], mode='L')
        #     img.fill_value = (1, 1, 1)
        #     img.colorize(rainbow)
        #
        #     # add coast
        #     cw_ = ContourWriterAGG()
        #     pilimg = img.pil_image()
        #     cw_.add_coastlines(pilimg, sector_def, resolution='f',
        #                        outline="black", width=0.5)
        #
        #     label = "%s Suomi-NPP OMPS SO2"
        #     tick_marks = 10
        #     minor_tick_marks = 5
        #
        #     dc = DecoratorAGG(pilimg)
        #     dc.align_bottom()
        #
        #     font = aggdraw.Font(colorbar_text_color, TYPEFACE, size=14)
        #     if img_colormap is not None:
        #         dc.add_scale(img_colormap, extend=True,
        #                      tick_marks=tick_marks,
        #                      minor_tick_marks=minor_tick_marks, font=font,
        #                      height=20, margins=[1, 1], )
        #         dc.new_line()
        #
        #     lat = float(sector_def.proj_dict['lat_0'])
        #     lon = float(sector_def.proj_dict['lon_0'])
        #     passes = Orbital("Suomi NPP").get_next_passes(start_slack, 1,
        #                                                   lon, lat, 0)
        #     if passes is not None:
        #         file_start = passes[0][0]
        #     else:
        #         file_start = start
        #     start_string = file_start.strftime('%m/%d/%Y %H:%M UTC')
        #     font = aggdraw.Font(GOLDENROD, TYPEFACE, size=14)
        #     dc.add_text(label % start_string, font=font, height=30,
        #                 extend=True, bg_opacity=128, bg='black')
        #
        #     if dev:
        #         filepath = os.path.join(PNG_DEV_DIR, sector_def.area_id)
        #     else:
        #         filepath = os.path.join(PNG_DIR, sector_def.area_id)
        #
        #     if not os.path.exists(filepath):
        #         print("Making out dir " + filepath)
        #         os.makedirs(filepath)
        #
        #     # filename = "%s-%s-%s.png" % (size_sector,
        #     #                             self.product,
        #     #                             file_start.strftime('%Y%m%d-%H%M'))
        #
        #     filename = "%s.omps.--.--.%s.so2.png" % (
        #         file_start.strftime('%Y%m%d.%H%M'), sector_def.area_id)
        #
        #     filepath = os.path.join(filepath, filename)
        #
        #     print("Saving to %s" % filepath)
        #     pilimg.save(filepath)


def processor_factory(message):
    topic = message.subject

    types = AbstractProcessor.__subclasses__()
    for type in types:
        if type.is_familiar(topic):
            return type(message)

    err_msg = "I don't know how to handle message topic {}".format(topic)
    raise NotImplementedError(err_msg)
