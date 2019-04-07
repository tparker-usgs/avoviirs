#!/usr/bin/env python

# -*- coding: utf-8 -*-

# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

""" Create a product.
"""


from abc import ABC


class Processor(ABC):
    def __init__(self, message):
        self.message = message
        super(Processor, self).__init__()


def processor_factory(message):
    topic = message.subject
    err_msg = "I don't know how to handle message topic {}".format(topic)
    raise NotImplementedError(err_msg)
