# -*- coding: utf-8
# @desc: Dictionary interface and implementations for Judou segmentation
import os
try:
    import sqlite3
except ImportError:
    import pysqlite2.dbapi2 as sqlite3
import math

import logger
from freq_helper import BaiduFreqDiscover

class JudouDictInterface(object):
    # dict sample: {unicode('中文'): Probability of '中文'}
    def get_dict_path(self, file_name):
        dict_dir = os.path.abspath(os.path.dirname(__file__))
        dict_path = dict_dir + '/%s' %file_name
        return dict_path

    def load(self):
        raise 'Not implement yet.'

    def __contains__(self, item):
        raise 'Not implement yet.'

    def __getitem__(self, key):
        raise 'Not implement yet.'

    def get_bi_freq(self, w1, w2, encoding=None):
        raise 'Not implement yet.'


class TxtDict(JudouDictInterface):
    def __init__(self):
        self.dict = {}

    def save(self, fname='dict.dat'):
        """Pickle dump dict.

        For a little fast load.
        """
        from cPickle import dump
        fp = open(fname, 'wb')
        dump(self.dict, fp)
        fp.close()

    def _load(self, fname='dict.dat'):
        """Pickle load dict.

        For a little fast load.
        """
        from cPickle import load
        try:
            fp = open(fname, 'rb')
            self.dict = load(fp)
            fp.close()
        except:
            return False

        return True

    def __contains__(self, item):
        return item in self.dict

    def __getitem__(self, key):
        return self.dict[key]

class FooDict(TxtDict):
    def load(self):
        """From People Daily Corpus.
        """
        # Load dict into memory
        if self._load(self.get_dict_path('pd.dat')):
            return

        self.dict = {}
        frequency_words = 0.0
        f = open(self.get_dict_path('dict.txt'))
        for line in f:
            word, frequency_word, pos = line.split()
            word = word.decode('gb18030')
            self.dict[word] = float(frequency_word)
            frequency_words += float(frequency_word)

        for k, v in self.dict.iteritems():
            self.dict[k] = -log(self.dict[k]/frequency_words)
        # Simple data sparse smoothing
        self.dict['#epsilon#'] = -log(1.0/frequency_words)
        print 'Load dictionary(%d/%d) done.' % (len(self.dict), frequency_words)

        f.close()
        self.save(self.get_dict_path('pd.dat'))


class SogouDict(TxtDict):
    def load(self):
        """From Sogou Internet Corpus.
        """
        # Load dict into memory
        if self._load(self.get_dict_path('sogou.dat')):
            return

        self.dict = {}
        frequency_words = 0.0
        f = open(self.get_dict_path('SogouLabDic.dic'))
        for line in f:
            items = line.split()
            if len(items) == 2:
                word, frequency_word = items
            if len(items) == 3:
                word, frequency_word, pos = items
            word = word.decode('gb18030') # There are Chinese character more than GBK
            self.dict[word] = float(frequency_word)
            frequency_words += float(frequency_word)

        for k, v in self.dict.iteritems():
            self.dict[k] = -log(self.dict[k]/frequency_words)
        # Simple data sparse smoothing
        self.dict['#epsilon#'] = -log(1.0/frequency_words)
        print 'Load dictionary(%d/%.0f) done.' % (len(self.dict), frequency_words)

        f.close()
        self.save(self.get_dict_path('sogou.dat'))

class JudouDict(JudouDictInterface):
    def load(self):
        self.conn = sqlite3.connect(self.get_dict_path('judou_dict.db3'))

    def __contains__(self, item):
        c = self.conn.execute('select id from dictionary where keyword=?', (item,))
        i = c.fetchone()
        if i:
            return True
        else:
            return False

    def __getitem__(self, key):
        return 0.0
        import memcachedb

        if not hasattr(self, 'mc'):
            self.mc = memcachedb.Client(['127.0.0.1:21201'])
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        fq = self.mc.get(key)
        if fq is None:
            logger.debug('Try to find frequency for %s...' % key)
            fd = BaiduFreqDiscover()
            fq = fd.get_freq(key, 'utf-8')
            self.mc.set(key, fq)
        if fq == 0:
            return 0.0
        else:
            return math.log(float(fq))

    def get_bi_freq(self, w1, w2, encoding=None):
        import memcachedb

        if not hasattr(self, 'mc'):
            self.mc = memcachedb.Client(['127.0.0.1:21201'])
        key = '%s,%s' % (w1, w2)
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        bfq = self.mc.get(key)
        if bfq is None:
            logger.debug('Try to find bi-frequency for (%s, %s)...' % (w1, w2))
            fd = BaiduFreqDiscover()
            bfq = fd.get_bi_freq(w1, w2, encoding)
            self.mc.set(key, bfq)
        #if bfq == 0:
        #    return 0.0
        #else:
        #    return math.log(float(bfq))
        return bfq

    def get_tri_freq(self, w1, w2, w3, encoding=None):
        '''(w1w2, w2w3, w1w2w3)
        '''
        import memcachedb

        if not hasattr(self, 'mc'):
            self.mc = memcachedb.Client(['127.0.0.1:21201'])
        key = '%s,%s,%s' % (w1, w2, w3)
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        tfq = self.mc.get(key)
        if tfq is None:
            logger.debug('Try to find bi-frequency for (%s, %s)...' % (w1, w2))
            fd = BaiduFreqDiscover()
            tfq = fd.get_tri_freq(w1, w2, w3, encoding)
            self.mc.set(key, tfq)
        return tfq

if __name__ == '__main__':
    logger.init()
    t = logger.Timer()

    dict = JudouDict()
    dict.load()

    t.start()
    for k1, k2, k3 in (
        ('结', '合', '成'),
        ('结合', '成', '分'),
        ('结合', '成', '分子'),
    ):
        logger.info('%s %s %s tri-freq: %s' % (k1, k2, k3, dict.get_tri_freq(k1, k2, k3, encoding='utf8')))
    
    for k1, k2 in (
        ('结', '合'),
        ('结', '合成'),
        ('结合', '成'),
        ('结合', '成分'),
        ('', '中华人民共和国'),
    ):
        logger.info('%s %s bi-freq: %d' % (k1, k2, dict.get_bi_freq(k1, k2, 'utf8')))
    logger.info('Done. Time %s' % t.end())
