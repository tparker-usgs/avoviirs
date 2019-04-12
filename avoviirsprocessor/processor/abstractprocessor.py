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
from satpy.writers import get_enhanced_image

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
            scn.load(['M15'])
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
            filename = "{}/M15-{}.png".format(PNG_DIR, sector_def.area_id)
            print("writing {}".format(filename))
            overlay = {'coast_dir': '/usr/local/gshhg',
                       'area': sector_def,
                       'color': GOLDENROD,
                       'width': 3,
                       'level_coast': 1,
                       'level_borders': 2}

            decorate = {'decorate': [
                                     {'text': {'txt': "Tom's Sample test",
                                               'align': {'top_bottom': 'bottom',
                                                         'left_right': 'right'},
                                               'font': TYPEFACE,
                                               'font_size': 22,
                                               'height': 30,
                                               'bg': 'black',
                                               'bg_opacity': 255,
                                               'line': 'white'}}]}

            #local.save_dataset('M15', filename=filename, writer='simple_image',
                               #overlay=overlay)

            img = get_enhanced_image(local['M15'], overlay=overlay,
                                     decorate=decorate)
            writer, save_kwargs = load_writer('simple_image')
            writer.save_dataset('M15', overlay=overlay, compute=compute)
# crs = new_scn['I04'].attrs['area'].to_cartopy_crs()
# ax = plt.axes(projection=crs)
#
# ax.coastlines()
# ax.gridlines()
# ax.set_global()
# plt.imshow(new_scn['I04'], transform=crs, extent=crs.bounds, origin='upper')
# cbar = plt.colorbar()
# cbar.set_label("Kelvin")
# plt.show()
#         img = get_enhanced_image(dataset.squeeze(), enhance=self.enhancer, overlay=overlay,
#                                decorate=decorate, fill_value=fill_value)
# img.pil_image()

def processor_factory(message):
    topic = message.subject

    types = AbstractProcessor.__subclasses__()
    for type in types:
        if type.is_familiar(topic):
            return type(message)

    err_msg = "I don't know how to handle message topic {}".format(topic)
    raise NotImplementedError(err_msg)
