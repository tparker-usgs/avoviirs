"""
Create and deliver a volcview product.

This module provides utility functions and an abstract base class for
creating images for volcview.

"""

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
from datetime import timedelta
import io
import zmq


GOLDENROD = (218, 165, 32)
PNG_DIR = "/viirs/png"
MSG_DIR = "/viirs/messages"
TYPEFACE = "/app/avoviirsprocessor/Cousine-Bold.ttf"
FONT_SIZE = 14
COAST_DIR = "/usr/local/gshhg"
AREA_DEF = "/app/trollconfig/areas.def"
PROD_ENDPOINT = "http://volcview.wr.usgs.gov/vv-api"
DEV_ENDPOINT = "http://dev-volcview.wr.usgs.gov/vv-api"
ORBIT_SLACK = timedelta(minutes=30)
SECTOR_PROXY = "tcp://viirstools:29292"
POST_TIMEOUT = 30

def processor_factory(message):
    """Instanciate an approprieate processor object.

    Search for subclasses of Processor and return an initalized object
    suitable for handling the provided message.

    Parameters
    ----------
    message : posttroll.message.Message
        The message needing to be processed.

    Returns
    -------
        processor.Processor
            An inialized Processor suitable for handling the provided message.
    """
    product = message.subject.split("/")[-1]
    for processor in Processor.__subclasses__():
        if processor.Product == product:
            return processor(message)
    print("found {}".format(len(Processor.__subclasses__())))
    raise NotImplementedError("I don't know how to {}".format(product))


def publish_products(message):
    logger.debug("Processing message: %s", message.encode())
    processor = processor_factory(message)
    processor.load_data()

    for sector_def in processor.find_sectors():
        file_base = processor.get_file_base(sector_def)
        message_filename = "{}/{}.txt".format(MSG_DIR, file_base)
        with open(message_filename, "w") as msg_file:
            msg_file.write(message.encode())
        pilimg = processor.get_image(sector_def)
        # processor.write_pilimg(pilimg, file_base)
        processor.write_old_volcview(pilimg, sector_def)
        processor.publish_pilimg(pilimg, file_base, sector_def.area_id)

    logger.debug("All done with this task.")


def publish_product(filename, pngimg, volcview_args):
    user = tutil.get_env_var("VOLCVIEW_USER")
    passwd = tutil.get_env_var("VOLCVIEW_PASSWD")
    headers = {"username": user, "password": passwd}
    files = {"file": (filename, pngimg)}
    url = DEV_ENDPOINT + "/imageApi/uploadImage"
    print("publishing image to {}".format(url))
    print("data {}".format(volcview_args))
    response = requests.post(url, headers=headers, data=volcview_args, files=files, timeout=POST_TIMEOUT))
    print("server said: {}".format(response.text))
    return response


class Processor(ABC):
    """Abstract superclass for processors

    I create and deliver products to volcview.

    Parameters
    ----------
    message : posttroll.message.Message
       The message to be processed.
    product : string
       The product to be created.
    product_label: string
       The product-specific portion of the labled shown on the volcview
       image.
    """

    def __init__(self, message, product, volcview_band, product_label):
        self.message = message
        self.product = product
        self.product_label = product_label
        self.volcview_band = volcview_band
        self.data = message.data
        self.color_bar_font = aggdraw.Font(GOLDENROD, TYPEFACE, size=FONT_SIZE)
        self.scene = self._create_scene()
        context = zmq.Context()
        self.publisher = context.socket(zmq.PUB)
        self.publisher.connect(SECTOR_PROXY)

    @abstractmethod
    def load_data(self):
        """Load data into a scene
        """
        pass

    def apply_colorbar(self, dcimg):
        """Apply a colorbar to an image.

        Parameters
        ----------
        dcimage : pydecorate.DecoratorAGG
            Image to receive colorbar
        """
        pass

    def enhance_image(self, img):
        """Apply enhancements to image data.

        Parameters
        ----------
        img : trollimage.xrimage.XRImage
            Image to be enhanced
        """
        pass

    def decorate_pilimg(self, pilimg):
        """Apply decorations to an image

        Parameters
        ----------
        pilimg : PIL.Image
        """
        dc = DecoratorAGG(pilimg)
        dc.align_bottom()

        self.apply_colorbar(dc)
        self.apply_label(dc)

    def draw_colorbar(self, dcimg, colors, tick_marks, minor_tick_marks):
        """Draw a colorbar on an image

        Parameters
        ----------
        dcimg : pydecorate.DecoratorAGG
            Image to receive colorbar
        colors
        tick_marks
        minor_tick_marks

        .. note:: This is typically called by a concrete apply_colorbar method.
        """
        dcimg.add_scale(
            colors,
            extend=True,
            tick_marks=tick_marks,
            minor_tick_marks=minor_tick_marks,
            font=self.color_bar_font,
            height=20,
            margins=[1, 1],
        )
        dcimg.new_line()

    def apply_label(self, dcimg):
        """Apply the standard text label to an image

        Parameters
        ----------
         dcimg : pydecorate.DecoratorAGG
            Image to label
        """
        start_string = self.scene.start_time.strftime("%m/%d/%Y %H:%M UTC")
        label = "{} {} VIIRS {}".format(
            start_string, self.data["platform_name"], self.product_label
        )
        dcimg.add_text(
            label,
            font=TYPEFACE,
            height=30,
            extend=True,
            bg_opacity=128,
            bg="black",
            line=GOLDENROD,
            font_size=14,
        )

    def _create_scene(self):
        """Create a scene object from available data.

        Returns
        -------
         satpy.scene.Scene
            Inialized scene object
        """
        data = self.message.data
        filter_parameters = {
            "start_time": data["start_time"] - ORBIT_SLACK,
            "end_time": data["end_time"] + ORBIT_SLACK,
            "platform_name": data["platform_name"],
        }
        filenames = find_files_and_readers(
            base_dir="/viirs/sdr",
            reader="viirs_sdr",
            filter_parameters=filter_parameters,
        )
        try:
            scene = Scene(filenames=filenames, reader="viirs_sdr")
        except ValueError as e:
            logger.exception("Loading files didn't go well: %s", filenames)
            raise e

        return scene

    def find_sectors(self):
        """Identify sectors with at least some coverage by the provided scene.

        Returns
        -------
        list
            area_id of each sector with some coverage.
        """
        data = self.message.data
        overpass = Pass(
            data["platform_name"],
            self.scene.start_time,
            self.scene.end_time,
            instrument="viirs",
        )
        sectors = []
        coverage_threashold = float(tutil.get_env_var("COVERAGE_THRESHOLD", 0.1))
        for sector_def in parse_area_file(AREA_DEF):
            logger.debug("Checking coverage for %s", sector_def.area_id)
            coverage = overpass.area_coverage(sector_def)
            logger.debug("{} coverage: {}".format(sector_def.area_id, coverage))
            if coverage > coverage_threashold:
                sectors.append(sector_def)
        return sectors

    def get_image(self, sector_def):
        local = self.scene.resample(sector_def)
        img = to_image(local[self.product].squeeze())
        self.enhance_image(img)
        img = add_overlay(
            img, area=sector_def, coast_dir=COAST_DIR, color=GOLDENROD, fill_value=0
        )
        pilimg = img.pil_image()
        self.decorate_pilimg(pilimg)
        return pilimg

    def get_file_base(self, sector_def):
        data = self.message.data
        time_str = self.scene.start_time.strftime("%Y%m%d.%H%M")
        filename_str = "testing-{}-{}-{}-viirs-{}-{}"
        filename = filename_str.format(
            time_str,
            data["platform_name"],
            data["orbit_number"],
            sector_def.area_id,
            self.product,
        )
        return filename

    def write_pilimg(self, pilimg, file_base):
        image_filename = "{}/{}.png".format(PNG_DIR, file_base)
        print("writing {}".format(image_filename))
        pilimg.save(image_filename)

    def write_old_volcview(self, pilimg, sector_def):
        time_str = self.scene.start_time.strftime("%Y%m%d.%H%M")
        file_path = "{}/{}".format(PNG_DIR, sector_def.area_id[-4:])
        product = "ASH" if self.product == "btd" else self.product.upper()
        filename_str = "{}.viirs.--.--.{}.{}.png".format(
            time_str, sector_def.area_id, product
        )
        logger.info("writing file %s/%s", file_path, filename_str)
        pilimg.save("{}/{}".format(file_path, filename_str))
        logger.debug("finished writing file %s/%s", file_path, filename_str)

    def publish_pilimg(self, pilimg, file_base, area_id):
        unixtime = calendar.timegm(self.scene.start_time.timetuple())
        volcview_args = {
            "sector": area_id,
            "band": self.volcview_band,
            "dataType": "viirs",
            "imageUnixtime": unixtime,
        }
        filename = file_base + ".png"
        pngimg = io.BytesIO()
        pilimg.save(pngimg, format="PNG")
        pngimg.seek(0)
        publish_product(filename, pngimg, volcview_args)
        self.publisher.send_json(volcview_args)
