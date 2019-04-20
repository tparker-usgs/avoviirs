
import tomputils.util as tutil
from pyresample import parse_area_file
from trollsched.satpass import Pass
from satpy.scene import Scene
from satpy import find_files_and_readers
from satpy.writers import load_writer


REQUEST_TIMEOUT = 10000
TASK_SERVER = "tcp://viirscollector:19091"
UPDATE_PUBLISHER = "tcp://viirscollector:19191"
GOLDENROD = (218, 165, 32)
PNG_DIR = '/viirs/png'
AREA_DEF = '/app/avoviirsprocessor/trollconfig/areas.def'
TYPEFACE = "/app/avoviirsprocessor/Cousine-Bold.ttf"


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

    def process_message(self):
        logger = self.logger
        message = self.message
        self.logger.debug("Processing message: %s", message.encode())
        data = message.data
        product = message.subject.split("/")[-1]
        scn = self.create_scene(data)
        try:
            scn.load([product])
        except KeyError:
            logger.error("I don't know how to make a %s", product)
            logger.error("I know: {}".format(scn.all_composite_names()))
            return
        except ValueError:
            logger.debug("No M15 data, skipping")
            return

        for sector_def in self.find_sectors():
            local = scn.resample(sector_def)
            overlay = {'coast_dir': '/usr/local/gshhg',
                       'color': GOLDENROD,
                       'width': 1,
                       'level_coast': 1,
                       'level_borders': 2}

            start_string = data['start_time'].strftime('%m/%d/%Y %H:%M UTC')
            label = "{} {} {}"
            label = label.format(start_string, data['platform_name'],
                                 self.product_label)

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
            filename = filename_str.format(PNG_DIR, time_str,
                                           data['orbit_number'],
                                           data['sensor'][0],
                                           sector_def.area_id,
                                           product)

            print("writing {}".format(filename))
            writer.save_dataset(local[product], overlay=overlay,
                                decorate=decorate, filename=filename)
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
