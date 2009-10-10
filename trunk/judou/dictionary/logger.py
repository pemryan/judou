#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @desc: Logging wrapper

import sys
import logging
from datetime import datetime

level = None

def init():
    global level

    if len(sys.argv) > 1 and sys.argv[1]=='debug':
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level,
                       format='%(asctime)s %(levelname)s %(message)s')

def is_debug():
    return logging.DEBUG == level

debug=logging.debug
info=logging.info
warning=logging.warning
exception=logging.exception
error=logging.error

class Timer(object):
    def start(self):
        self.start = datetime.now()

    def end(self):
        elapsed = datetime.now() - self.start
        return elapsed
