# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#  Purpose: process VIIRS data
#   Author: Tom Parker
#
# -----------------------------------------------------------------------------
"""
avoviirsprocessor
=================

Process VIIRS data at AVO

:license:
    CC0 1.0 Universal
    http://creativecommons.org/publicdomain/zero/1.0/
"""


import tomputils.util as tutil
from avoviirsprocessor.version import __version__

logger = tutil.setup_logging("avoviirsprocessor errors")

__all__ = ["__version__"]
