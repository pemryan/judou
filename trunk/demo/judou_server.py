#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import asyncore, asynchat
import os, socket, string

import logging
import logging.handlers

from word_dict import JudouDict
from judou import argmax_seg, rmm_seg, mm_seg, full_seg, bi_mm_seg
try:
    from judou_daemon_conf import LOG_FILENAME
except ImportError:
    print 'cp judou_daemon_conf_sample.py judou_daemon_conf.py , and config your own settings.'
    sys.exit(1)

logger = logging.getLogger('judou_server')
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    LOG_FILENAME, maxBytes=1024*1024, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class JudouChannel(asynchat.async_chat):
    def __init__(self, dict, server, sock, addr, keep_alive=False):
        asynchat.async_chat.__init__(self, sock)
        self.set_terminator('\r\n')
        self.data = ""
        self.keep_alive = keep_alive

        self.dict = JudouDict()
        self.dict.load()

    def collect_incoming_data(self, data):
        self.data = data

    def found_terminator(self):
        logger.debug(self.data)
        l = rmm_seg(self.data, self.dict, 'utf-8')
        logger.debug(l)
        self.push(' '.join(l))
        if not self.keep_alive:
            self.close_when_done()

    def handle_error(self):
        logger.exception(self.data)
        self.close_when_done()


class JudouServer(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((host, port))
        self.listen(5)
        self.dict = JudouDict()
        self.dict.load()

    def handle_accept(self):
        conn, addr = self.accept()
        JudouChannel(self, self.dict, conn, addr)

    def run(self):
        try:
            asyncore.loop()
        except KeyboardInterrupt:
            logger.info('Shutdown gracefully...')

#
# try it out
if __name__ == '__main__':

    PORT = 7788
    s = JudouServer("localhost", PORT)
    logger.info("serving at port %d..." , PORT)
    s.run()
