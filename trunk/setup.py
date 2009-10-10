#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from distutils.core import setup, Extension

setup(
        name = 'judou',
        version = '0.0.1',
        description="中文分词工具包",
        packages = find_packages(),
        ext_package='',
        package_data={
        "mmseg.data":["*.dic"],
        },
        long_description=""" """,
        ext_modules = [     ],
)
