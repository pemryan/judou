#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ctypes import *

# 通过 C 接口载入 libbamboo ，“.dylib”是 Mac OSX 下的动态库后缀， Linux 下应该是“libbamboo.so”：
libbamboo = CDLL('libbamboo.so')
# 调用 bamboo_init() 函数得到一个分词器实例：
bamboo_init = libbamboo.bamboo_init
bamboo_init.restype = c_void_p
bamboo_handler = bamboo_init(c_char_p('crf_seg'), None)
# 如果返回的实例是 None （也即 C 中的 Null ），表示实例生成失败，那我们打印出错原因：
if bamboo_handler is None:
    bamboo_strerror = libbamboo.bamboo_strerror
    bamboo_strerror.restype = c_char_p
    print bamboo_strerror()
else:
    # 把文本传给分词器准备分词：
    # 待分词的文本必须是 utf-8 编码的 bytes string ，所以我们要把 unicode string encode 一下：
    libbamboo.bamboo_setopt(bamboo_handler, c_long(0), c_char_p(u'我爱北京天安门'.encode('utf-8')))
    # 真正开始分词：
    bamboo_parse = libbamboo.bamboo_parse
    bamboo_parse.restype = c_char_p
    # 下一行得到分词结果（空格分隔），格式还是 utf-8 编码的 bytes string ，我们把它 decode 成 unicode ：
    segged = bamboo_parse(bamboo_handler).decode('utf-8')
    print type(segged), len(segged), segged
# 调用 bamboo_clean() 函数释放分词器实例：
libbamboo.bamboo_clean(bamboo_handler)
