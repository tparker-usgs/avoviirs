
import tomputils.util as tutil
from pyresample import parse_area_file
from trollsched.satpass import Pass
from satpy.scene import Scene
from satpy import find_files_and_readers
from satpy.writers import load_writer, to_image, add_decorate, add_overlay
import json
from posttroll.subscriber import Subscribe
from posttroll.message import datetime_encoder
from pprint import pprint
from mpop.satellites import PolarFactory
from datetime import timedelta, datetime
from dateutil import parser
from pyorbital.orbital import Orbital
from mpop.utils import debug_on
from trollsched.satpass import Pass
from mpop.projector import get_area_def
import mpop.imageo.geo_image as geo_image
#from PIL import Image
from pydecorate import DecoratorAGG
import aggdraw
from trollimage.colormap import rdbu
from trollsched.satpass import Pass
from mpop.projector import get_area_def
import os
import os.path
import tomputils.mattermost as mm
from trollimage import colormap
import sys
import traceback
import argparse

REQUEST_TIMEOUT = 10000
TASK_SERVER = "tcp://viirscollector:19091"
UPDATE_PUBLISHER = "tcp://viirscollector:19191"
GOLDENROD = (218, 165, 32)
PNG_DIR = '/viirs/png'
AREA_DEF = '/app/avoviirsprocessor/trollconfig/areas.def'
TYPEFACE = "/app/avoviirsprocessor/Cousine-Bold.ttf"
COAST_DIR = '/usr/local/gshhg'


def processor_factory(message):
    product = message.subject.split("/")[-1]

    if product == 'tir':
        return TIR(message)
    elif product == 'mir':
        return MIR(message)
    elif product == 'btd':
        return BTD(message)
    elif product == 'vis':
        return VIS(message)
    else:
        raise NotImplementedError("I don't know how to {}".format(product))


class Processor(object):
    def __init__(self, message, product_label):
        self.message = message
        self.product_label = product_label
        self.logger = tutil.setup_logging("avoviirsprocessor.watcher errors")

    def create_scene(self):
        data = self.message.data
        filter_parameters = {'start_time': data['start_time'],
                             'end_time': data['end_time'],
                             'platform_name': data['platform_name']}
        filenames = find_files_and_readers(base_dir='/viirs/sdr',
                                           reader='viirs_sdr',
                                           filter_parameters=filter_parameters)
        return Scene(filenames=filenames, reader='viirs_sdr')

    def find_sectors(self, scene):
        data = self.message.data
        overpass = Pass(data['platform_name'], scene.start_time,
                        scene.end_time, instrument='viirs')
        sectors = []
        for sector_def in parse_area_file(AREA_DEF):
            coverage = overpass.area_coverage(sector_def)
            self.logger.debug("{} coverage: {}".format(sector_def.area_id,
                                                       coverage))
            if coverage > .1:
                sectors.append(sector_def)
        return sectors

    def apply_label(self, img):
        data = self.data
        pilimg = img.pil_image()

        dc = DecoratorAGG(pilimg)
        dc.align_bottom()
        font = aggdraw.Font(GOLDENROD, TYPEFACE, size=14)

        start_string = data.strftime('%m/%d/%Y %H:%M UTC')
        label = "{} {} VIIRS {}".format(start_string, data['platform_name'],
                                        self.product_label)
        font = aggdraw.Font(GOLDENROD, TYPEFACE, size=14)
        dc.add_text(start_string + " " + label, font=font, height=30,
                    extend=True, bg_opacity=128, bg='black')

    def get_enhanced_pilimage(self, dataset, enhancer):
        img = to_image(dataset)

        enhancer.add_sensor_enhancements('viirs')
        enhancer.apply(img, **dataset.attrs)

        img = add_overlay(img, area=dataset.attrs['area'], coast_dir=COAST_DIR,
                          color=GOLDENROD, width=1, fill_value=0)

        pilimg = img.pil_image()
        img = self.apply_label(pilimg)

        return pilimg

    def process_message(self):
        logger = self.logger
        message = self.message
        self.logger.debug("Processing message: %s", message.encode())
        data = message.data
        product = message.subject.split("/")[-1]
        scn = self.create_scene()
        try:
            scn.load([product])
        except KeyError:
            logger.error("I don't know how to make a %s", product)
            logger.error("I know: {}".format(scn.all_composite_names()))
            return
        except ValueError:
            logger.debug("No M15 data, skipping")
            return

        for sector_def in self.find_sectors(scn):
            local = scn.resample(sector_def)
            img = self.get_enhanced_pilimage(local[product].squeeze(),
                                          writer.enhancer)
            time_str = data['start_time'].strftime('%Y%m%d.%H%M')
            filename_str = "{}/{}.{}.{}.--.{}.{}.png"
            filename = filename_str.format(PNG_DIR, time_str,
                                           data['orbit_number'],
                                           data['sensor'][0],
                                           sector_def.area_id,
                                           product)

            print("writing {}".format(filename))
            img.save(filename)

        logger.debug("All done with this taks.")


class TIR(Processor):
    def __init__(self, message):
        super().__init__(message,
                         'thermal infrared brightness tempeerature (c)')


class MIR(Processor):
    def __init__(self, message):
        super().__init__(message,
                         'mid-infrared brightness temperature (c)')


class BTD(Processor):
    def __init__(self, message):
        super().__init__(message,
                         'brightness temperature difference')


class VIS(Processor):
    def __init__(self, message):
        super().__init__(message,
                         'true color')
