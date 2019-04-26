from avoviirsprocessor.processor import Processor, TYPEFACE
from trollimage import colormap
from satpy.dataset import combine_metadata
import aggdraw
from satpy.enhancements import cira_stretch


class TIR(Processor):
    Product = 'tir'

    def __init__(self, message):
        super().__init__(message, TIR.Product,
                         'thermal infrared brightness tempeerature (c)')

    def enhance_image(self, img):
        img.invert()

    def apply_colorbar(self, dcimg):
        colors = colormap.greys
        colors.set_range(-65, 35)
        super().draw_colorbar(dcimg, colors, 20, 10)

    def load_data(self, scn):
        scn.load(['I05'])
        scn['tir'] = scn['I05']
        return scn


class MIR(Processor):
    Product = 'mir'

    def __init__(self, message):
        super().__init__(message, MIR.Product,
                         'mid-infrared brightness temperature (c)')
        self.colors = colormap.Colormap((0.0, (0.0, 0.0, 0.0)),
                                        (1.0, (1.0, 1.0, 1.0)))
        self.colors.set_range(-50, 50)

    def apply_colorbar(self, dcimg):
        super().draw_colorbar(dcimg, self.colors, 20, 10)

    def load_data(self, scn):
        scn.load(['I04'])
        scn['mir'] = scn['I04']
        return scn


class BTD(Processor):
    Product = 'btd'

    def __init__(self, message):
        super().__init__(message, BTD.Product,
                         'brightness temperature difference')
        self.color_bar_font = aggdraw.Font((0, 0, 0), TYPEFACE, size=14)
        self.colors = colormap.Colormap((0.0, (0.5, 0.0, 0.0)),
                                        (0.071428, (1.0, 0.0, 0.0)),
                                        (0.142856, (1.0, 0.5, 0.0)),
                                        (0.214284, (1.0, 1.0, 0.0)),
                                        (0.285712, (0.5, 1.0, 0.5)),
                                        (0.357140, (0.0, 1.0, 1.0)),
                                        (0.428568, (0.0, 0.5, 1.0)),
                                        (0.499999, (0.0, 0.0, 1.0)),
                                        (0.5000, (0.5, 0.5, 0.5)),
                                        (1.0, (1.0, 1.0, 1.0)))
        self.colors.set_range(-6, 5)

    def enhance_image(self, img):
        img.colorize(self.colors)

    def apply_colorbar(self, dcimg):
        super().draw_colorbar(dcimg, self.colors, 1, .5)

    def load_data(self, scn):
        scn.load(['M15', 'M16'])
        scn['btd'] = scn['M15'] - scn['M16']
        scn['btd'].attrs = combine_metadata(scn['M15'], scn['M16'])
        return scn


class VIS(Processor):
    Product = 'vis'

    def __init__(self, message):
        super().__init__(message, VIS.Product, 'true color')

    def enhance_image(self, img):
        cira_stretch(img)

    def load_data(self, scn):
        scn.load(['true_color'])
        scn = scn.resample(resampler='native')
        scn['vis'] = scn['true_color']
        return scn
