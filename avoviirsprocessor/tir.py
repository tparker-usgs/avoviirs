#!/usr/bin/env python

# -*- coding: utf-8 -*-

# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

""" TIR
"""


from avoviirsprocessor.processor import Processor


class TIR(Processor):
    def __init__(self, message):
        super().__init__(self, message,
                         'VIIRS thermal infrared brightness temperature(C))')
