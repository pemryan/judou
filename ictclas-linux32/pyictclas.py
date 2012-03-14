# -*- coding: utf-8
'''
author: twinsant@gmail.com
'''
import os
try:
    from ctypes import c_bool # Python2.6
except ImportError:
    from ctypes import c_int
    c_bool = c_int
from ctypes import *

ICTCLAS_ENCODING = 'gb18030'
POS_SIZE = 8

class c_result(Structure):
    _fields_ = [
        ('start', c_int),
        ('length', c_int),
        ('s_pos', c_char*POS_SIZE),
        ('i_pos', c_int),
        ('word_id', c_int),
        ('word_type', c_int),
        ('weight', c_int)
    ]

class ICTCLAS(object):
    EXPORTS = [
        ('_exit', '_Z12ICTCLAS_Exitv', [], c_bool),
        ('_init', '_Z12ICTCLAS_InitPKci', [c_char_p, c_int], c_bool),
        ('_is_word', '_Z14ICTCLAS_IsWordPKc', [], c_int),
        ('_keyword', '_Z15ICTCLAS_KeyWordP8result_tRi', [POINTER(c_result), POINTER(c_int)], c_int),
        ('_set_pos_map', '_Z17ICTCLAS_SetPOSmapi', [], c_int),
        ('_del_usr_word', '_Z18ICTCLAS_DelUsrWordPKc', [c_char_p], c_int),
        ('_get_uni_prob', '_Z18ICTCLAS_GetUniProbPKc', [c_char_p], c_float),
        ('_add_user_word', '_Z19ICTCLAS_AddUserWordPKc', [c_char_p], c_int),
        ('_file_process', '_Z19ICTCLAS_FileProcessPKcS0_i', [c_char_p, c_char_p, c_int], c_bool),
        ('_finger_print', '_Z19ICTCLAS_FingerPrintv', [], c_ulong),
        ('_file_process_ex', '_Z21ICTCLAS_FileProcessExPKcS0_', [], c_int),
        ('_save_the_usr_dic', '_Z21ICTCLAS_SaveTheUsrDicv', [], c_int),
        ('_import_user_dict', '_Z22ICTCLAS_ImportUserDictPKc', [c_char_p], c_uint),
        ('_paragraph_process', '_Z24ICTCLAS_ParagraphProcessPKci', [c_char_p, c_int], c_char_p),
        ('_paragraph_process_a', '_Z25ICTCLAS_ParagraphProcessAPKcPi', [c_char_p, c_void_p], POINTER(c_result)),
        ('_paragraph_process_e', '_Z25ICTCLAS_ParagraphProcessEPKcPci', [c_char_p, c_char_p, c_void_p], POINTER(c_result)),
        ('_paragraph_process_aw', '_Z26ICTCLAS_ParagraphProcessAWiP8result_t', [], c_int),
        ('_get_prragraph_processa_word_count', '_Z37ICTCLAS_GetParagraphProcessAWordCountPKc', [], c_int),
    ]
    GBK_CODE = 0
    UTF8_CODE = GBK_CODE + 1
    BIG5_CODE = UTF8_CODE + 1

    NO_TAG = 0
    TAGGING = 1

    LIB_SO = 'libICTCLAS2011.so'

    def __init__(self):
        lib_path = os.path.realpath(__file__)
        self.dir = os.path.abspath(os.path.dirname(lib_path))
        self.lib_so = os.path.join(self.dir, self.LIB_SO)

    def init(self):
        try:
            self.ld = cdll.LoadLibrary(self.lib_so)
        except OSError:
            self.ld = cdll.LoadLibrary(self.LIB_SO)
        for name, export_name, argtypes, restype in self.EXPORTS:
            setattr(self, name, getattr(self.ld, export_name))
            func = getattr(self, name)
            assert hasattr(self, name) and func
            func.argtypes = argtypes
            func.restype = restype
        assert self._init(self.dir, self.UTF8_CODE)

    def exit(self):
        assert self._exit()

    def process(self, text, pos_tagged=NO_TAG):
        res = self._paragraph_process(text, pos_tagged)
        return res

    def process_a(self, text, encoding='utf-8'):
        p_result_count = pointer(c_int(0))
        p_result = self._paragraph_process_a(text, p_result_count)
        result_count = p_result_count.contents.value
        res = []
        for i in xrange(result_count):
            class Word(object):
                def __str__(self):
                    return '%s/%s' % (self.word, self.s_pos)
            r = Word()
            r.start = p_result[i].start
            r.length = p_result[i].length
            _start = r.start/2 # byte2unicode
            _end = _start + r.length/2
            utext = text.decode(encoding)
            r.word = utext[_start:_end].encode(encoding)
            r.s_pos = p_result[i].s_pos
            r.i_pos = p_result[i].i_pos
            r.word_id = p_result[i].word_id
            r.word_type = p_result[i].word_type
            r.weight = p_result[i].weight
            res.append(r)
        return res

    def process_file(self, source_file_name, result_file_name, pos_tagged=NO_TAG):
        assert False
        return self._file_process(source_file_name, result_file_name, pos_tagged)

    def add_user_word(self, w, pos, encoding='utf-8'):
        uw = '%s\t%s' % (w, pos)
        uw = uw.decode(encoding).encode(ICTCLAS_ENCODING)
        return self._add_user_word(uw)

    def del_usr_word(self, w, encoding='utf-8'):
        uw = w
        uw = uw.decode(encoding).encode(ICTCLAS_ENCODING)
        return self._del_usr_word(uw)

    def get_uni_prob(self, w):
        return self._get_uni_prob(w)

    def save_the_usr_dic(self):
        return self._save_the_usr_dic()

    def keyword(self, text):
        assert False

    def finger_print(self):
        return self._finger_print()

ictclas = ICTCLAS()
