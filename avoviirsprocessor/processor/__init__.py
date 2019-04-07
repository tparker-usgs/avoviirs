# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#  Purpose: process VIIRS data
#   Author: Tom Parker
#
# -----------------------------------------------------------------------------
"""
avoviirsprocessor.processor
=========

Process VIIRS data at AVO

:license:
    CC0 1.0 Universal
    http://creativecommons.org/publicdomain/zero/1.0/
"""

from btdprocessor import BTDProcessor
from ir108hrprocessor import IR108HRProcessor
from ir108processor import IR108Processor
from mirprocessor import MIRProcessor
from truecolorprocessor import TrueColorProcessor
from visprocessor import VisProcessor

__all__ = ['BTDProcessor', 'BTDProcessor', 'IR108HRProcessor',
           'IR108Processor', 'MIRProcessor', 'TrueColorProcessor',
           'VisProcessor']
