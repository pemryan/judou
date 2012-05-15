# -*- coding: utf-8

from ctypes import *

class Bamboo:
    ''' Hacked from seg.py
    http://code.google.com/p/nlpbamboo/wiki/Interface'''

    BAMBOO_OPTION_TEXT = 0

    PARSER_CRF = 'crf_seg'

    def init(self):
        '''
            * parser：Bamboo Parser的name，取值可以是ugm_seg,mfm_seg, crf_seg, crf_pos, crf_ner_nr, crf_ner_ns, crf_ner_nt, keyword
            * cfg：Parser对应的配置文件名，如果为null或者不指定，则缺省用/opt/bamboo/etc目录下的标准配置文件 
        '''
        self.ld = CDLL('libbamboo.so')

        self._init = self.ld.bamboo_init
        self._init.restype = c_void_p
        self._init.argtypes = [c_char_p, c_char_p]

        self._clean = self.ld.bamboo_clean
        self._clean.restype = None
        self._clean.argtypes = [c_void_p]

        self._setopt = self.ld.bamboo_setopt
        self._setopt.restype = None
        self._setopt.argtypes = [c_void_p, c_long, c_char_p]

        self._parse = self.ld.bamboo_parse
        self._parse.restype = c_char_p
        self._parse.argtypes = [c_void_p]

        self._handler = self._init(self.PARSER_CRF, None)
        assert self._handler

    def process(self, text):
        self._setopt(self._handler, self.BAMBOO_OPTION_TEXT, text)
        return self._parse(self._handler)

    def clean(self):
        self._clean(self._handler)

    def exit(self):
        self.clean()

    def add_user_word(self, w, pos):
        pass

bamboo = Bamboo()
