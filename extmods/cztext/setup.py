#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from distutils.core import setup, Extension

setup(
        name = 'cztext',
        version = '1.0',
        description="中文文字截取",
        author_email="zsp007@gmail.com",
        ext_modules = [
            Extension('cztext', ['cztext.cpp'],
                extra_compile_args=['-O3', '-pipe',
                '-fomit-frame-pointer']),
            ],
)
