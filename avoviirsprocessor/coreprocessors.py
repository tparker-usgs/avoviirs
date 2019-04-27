from avoviirsprocessor.processor import Processor, TYPEFACE
from trollimage import colormap
from satpy.dataset import combine_metadata
import aggdraw
from satpy.enhancements import cira_stretch


class TIR(Processor):
    Product = 'tir'

    def __init__(self, message):
        super().__init__(message, TIR.Product, 'Thermal IR',
                         'thermal infrared brightness tempeerature (c)', )

    def enhance_image(self, img):
        img.crude_stretch(208.15, 308.15)  # -65c - 35c
        img.invert()

    def apply_colorbar(self, dcimg):
        colors = colormap.greys
        colors.set_range(-65, 35)
        super().draw_colorbar(dcimg, colors, 20, 10)

    def load_data(self):
        self.scene.load(['I05'])
        self.scene['tir'] = self.scene['I05']


class MIR(Processor):
    Product = 'mir'

    def __init__(self, message):
        super().__init__(message, MIR.Product, 'Mid-IR',
                         'mid-infrared brightness temperature (c)')
        self.colors = colormap.Colormap((0.0, (0.0, 0.0, 0.0)),
                                        (1.0, (1.0, 1.0, 1.0)))
        self.colors.set_range(-50, 50)

    def enhance_image(self, img):
        img.crude_stretch(223.15, 323.15)  # -50c - 50c

    def apply_colorbar(self, dcimg):
        super().draw_colorbar(dcimg, self.colors, 20, 10)

    def load_data(self):
        self.scene.load(['I04'])
        self.scene['mir'] = self.scene['I04']


class BTD(Processor):
    Product = 'btd'

    def __init__(self, message):
        super().__init__(message, BTD.Product, 'TIR BTD',
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
        img.crude_stretch(-6, 5)
        img.colorize(self.colors)

    def apply_colorbar(self, dcimg):
        super().draw_colorbar(dcimg, self.colors, 1, .5)

    def load_data(self):
        self.scene.load(['M15', 'M16'])
        self.scene['btd'] = self.scene['M15'] - self.scene['M16']
        self.scene['btd'].attrs = combine_metadata(self.scene['M15'],
                                                   self.scene['M16'])


class VIS(Processor):
    Product = 'vis'

    def __init__(self, message):
        super().__init__(message, VIS.Product, 'Visible', 'true color')

    def enhance_image(self, img):
        cira_stretch(img)

    def load_data(self):
        self.scene.load(['true_color'])
        self.scene = self.scene.resample(resampler='native')
        self.scene['vis'] = self.scene['true_color']
