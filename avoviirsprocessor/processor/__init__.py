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

from avoviirsprocessor.processor.btdprocessor import BTDProcessor
from avoviirsprocessor.processor.ir108hrprocessor import IR108HRProcessor
from avoviirsprocessor.processor.ir108processor import IR108Processor
from avoviirsprocessor.processor.mirprocessor import MIRProcessor
from avoviirsprocessor.processor.truecolorprocessor import TrueColorProcessor
from avoviirsprocessor.processor.visprocessor import VisProcessor
from avoviirsprocessor.processor.processor import Processor, processor_factory

__all__ = ['BTDProcessor', 'BTDProcessor', 'IR108HRProcessor',
           'IR108Processor', 'MIRProcessor', 'TrueColorProcessor',
           'VisProcessor', 'Processor', 'processor_factory']
