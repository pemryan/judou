#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup, Extension
"""
CXXFLAGS=-O2 -DNDEBUG -fPIC
CXX=g+

OBJECTS=rand48.o qdigest.o prng.o lossycount.o gk.o frequent.o countmin.o cgt.o ccfc.o


all: $(OBJECTS)
    $(CXX) $(CXXFLAGS) -shared pyzlcl.cc $(OBJECTS) -o Release/pyzlcl.so -lboost_python
    rm -rf *.o

$(OBJECTS): rand48.h qdigest.h prng.h lossycount.h gk4.h frequent.h countmin.h cgt.h ccfc.h
    $(CXX) $(CXXFLAGS) -c $*.cc

"""
setup(
        name = 'pyzlcl',
        version = '1.0',
        ext_modules = [
            Extension('pyzlcl', [
                'pyzlcl.cc','rand48.cc', 'qdigest.cc',  'prng.cc',  'lossycount.cc'
                ],
                extra_compile_args=[
                    '-O3', '-pipe','-DNDEBUG',
                    '-fomit-frame-pointer',
                ],
                libraries=['boost_python',],
                language='c++',
                ),
            ],
)
