
import calendar
import requests
from pyresample import parse_area_file
from trollsched.satpass import Pass
from satpy.scene import Scene
from satpy import find_files_and_readers
from satpy.writers import to_image, add_overlay
from pydecorate import DecoratorAGG
from avoviirsprocessor import logger
import aggdraw
import tomputils.util as tutil
from abc import ABC, abstractmethod


GOLDENROD = (218, 165, 32)
PNG_DIR = '/viirs/png'
TYPEFACE = "/app/avoviirsprocessor/Cousine-Bold.ttf"
COAST_DIR = '/usr/local/gshhg'
AREA_DEF = '/app/trollconfig/areas.def'
PROD_ENDPOINT = "http://volcview.wr.usgs.gov/vv-api"
DEV_ENDPOINT = "http://dev-volcview.wr.usgs.gov/vv-api"
VOLCVIEW_BANDS = {'tir': 'Thermal IR',
                  'mir': 'Mid-IR',
                  'btd': 'TIR BTD',
                  'vis': 'Visible'}


def processor_factory(message):
    product = message.subject.split("/")[-1]
    for processor in Processor.__subclasses__():
        if processor.product() == product:
            return product(message)
    raise NotImplementedError("I don't know how to {}".format(product))


def publish(sector, product, dataType, time, file):
    user = tutil.get_env_var('VOLCVIEW_USER')
    passwd = tutil.get_env_var('VOLCVIEW_PASSWD')
    headers = {'username': user, 'password': passwd}
    files = {'file': (file, open(file, 'rb'))}
    data = {'sector': sector,
            'band': VOLCVIEW_BANDS[product],
            'dataType': dataType,
            'imageUnixtime': calendar.timegm(time.timetuple()),
            }

    url = DEV_ENDPOINT + "/imageApi/uploadImage"
    print("publishing image to {}".format(url))
    print("data {}".format(data))
    response = requests.post(url, headers=headers, data=data, files=files)
    print("server said: {}".format(response.text))
    return response


class Processor(ABC):
    def __init__(self, message, product, product_label):
        self.message = message
        self.product_label = product_label
        self.data = message.data
        self.product = product
        self.color_bar_font = aggdraw.Font(GOLDENROD, TYPEFACE, size=14)

    @abstractmethod
    def enhance_image(self, img):
        pass

    @staticmethod
    @abstractmethod
    def product():
        pass

    def decorate_pilimg(self, pilimg):
        dc = DecoratorAGG(pilimg)
        dc.align_bottom()

        self.apply_colorbar(dc)
        self.apply_label(dc)

    def apply_colorbar(self, dcimg):
        pass

    def draw_colorbar(self, dcimg, colors, tick_marks, minor_tick_marks):
        dcimg.add_scale(colors, extend=True, tick_marks=tick_marks,
                        minor_tick_marks=minor_tick_marks,
                        font=self.color_bar_font, height=20, margins=[1, 1])
        dcimg.new_line()

    def apply_label(self, dcimg):
        start_string = self.data['start_time'].strftime('%m/%d/%Y %H:%M UTC')
        label = "{} {} VIIRS {}".format(start_string,
                                        self.data['platform_name'],
                                        self.product_label)
        dcimg.add_text(label, font=TYPEFACE, height=30, extend=True,
                       bg_opacity=128, bg='black', line=GOLDENROD,
                       font_size=14)

    @abstractmethod
    def load_data(self):
        pass

    def create_scene(self):
        data = self.message.data
        filter_parameters = {'start_time': data['start_time'],
                             'end_time': data['end_time'],
                             'platform_name': data['platform_name']}
        filenames = find_files_and_readers(base_dir='/viirs/sdr',
                                           reader='viirs_sdr',
                                           filter_parameters=filter_parameters)
        try:
            scene = Scene(filenames=filenames, reader='viirs_sdr')
        except ValueError as e:
            logger.exception("Loading files didn't go well: %s", filenames)
            raise e

        return scene

    def find_sectors(self, scene):
        data = self.message.data
        overpass = Pass(data['platform_name'], scene.start_time,
                        scene.end_time, instrument='viirs')
        sectors = []
        for sector_def in parse_area_file(AREA_DEF):
            coverage = overpass.area_coverage(sector_def)
            logger.debug("{} coverage: {}".format(sector_def.area_id,
                                                  coverage))
            if coverage > .1:
                sectors.append(sector_def)
        return sectors

    def get_enhanced_pilimage(self, dataset, area):
        img = to_image(dataset)
        self.enhance_image(img)
        img = add_overlay(img, area=area, coast_dir=COAST_DIR, color=GOLDENROD,
                          fill_value=0)
        return img.pil_image()

    def process_message(self):
        message = self.message
        logger.debug("Processing message: %s", message.encode())
        data = message.data
        scn = self.create_scene()
        try:
            scn = self.load_data(scn)
        except KeyError:
            logger.exception("missing data, skipping %s", self.product)
            return

        for sector_def in self.find_sectors(scn):
            local = scn.resample(sector_def)
            pilimg = self.get_enhanced_pilimage(local[self.product].squeeze(),
                                                sector_def)
            self.decorate_pilimg(pilimg)
            time_str = data['start_time'].strftime('%Y%m%d.%H%M')
            filename_str = "{}/testing-{}-{}-{}-viirs-{}-{}.png"
            filename = filename_str.format(PNG_DIR, time_str,
                                           data['platform_name'],
                                           data['orbit_number'],
                                           sector_def.area_id,
                                           self.product)

            print("writing {}".format(filename))
            pilimg.save(filename)

            publish(sector_def.area_id, self.product, 'viirs',
                    data['start_time'], filename)

        logger.debug("All done with this taks.")
