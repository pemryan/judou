#!/usr/bin/env python
# -*- coding: utf-8

# @desc: Keyword frequency helper tool.
import re
import logger
import urllib
import urllib2
import threading

class Parser(object):
    def __init__(self, url, headers=None):
        if headers:
            req = urllib2.Request(url, None, headers)
            self.page = urllib2.urlopen(req).read()
        else:
            self.page = urllib2.urlopen(url).read()

    def justdoit(self, find_func):
        return find_func(self.page)

class FrequencyDiscover(object):
    def quote(self, text):
        return '"' + text + '"'

    def get_freq(self, keyword):
        logger.debug(params)
        return 0


class BaiduFreqDiscover(FrequencyDiscover):
    QUERY_URL_PATTERN = 'http://www.baidu.com/s?ie=gb2312&%s'

    def get_freq(self, keyword, encoding=None):
        params = urllib.urlencode({'wd':self.to_keywords((keyword,), encoding)})
        url = self.QUERY_URL_PATTERN % params 
        logger.debug('Query %s' % url)
        p = Parser(url)
        def find(page):
            try:
                upage = page.decode('gb18030')
                pattern = ur'相关网页约(.*)篇'
            except UnicodeDecodeError:
                upage = page
                pattern = ur'相关网页约(.*)篇'.encode('gb18030')
            ammount = 0
            for m in re.finditer(pattern, upage):
                ammount_text = m.group(1)
                def s2i(s):
                    return int(s.replace(',', ''))
                ammount = s2i(ammount_text)
                break
            if not ammount:
                logger.warning('Zero frequency for %s: %d' % (keyword, ammount))
            return ammount
        return p.justdoit(find)

    def to_keywords(self, keyword_list, encoding=None):
        if encoding:
            l_keywords = [self.quote(w.decode(encoding).encode('gb18030')) for w in keyword_list]
        else:
            l_keywords = [self.quote(w.encode('gb18030')) for w in keyword_list]
        return ' '.join(l_keywords)

    def get_bi_freq(self, word1, word2, encoding=None):
        params = urllib.urlencode({'wd':self.to_keywords((word1, word2), encoding)})
        url = self.QUERY_URL_PATTERN % params 
        logger.debug('Query %s' % url)
        p = Parser(url)
        def find(page):
            word1word2 = '%s%s' % (word1, word2)
            if encoding:
                word1word2 = word1word2.decode(encoding)
            try:
                upage = page.decode('gb18030')
                pattern = word1word2
            except UnicodeDecodeError:
                upage = page
                pattern = word1word2.encode('gb18030')
            ammount = len(re.findall(pattern, upage))
            return ammount
        return p.justdoit(find)

    def get_tri_freq(self, word1, word2, word3, encoding=None):
        params = urllib.urlencode({'wd':self.to_keywords((word1, word2, word3), encoding)})
        url = self.QUERY_URL_PATTERN % params 
        logger.debug('Query %s' % url)
        p = Parser(url)
        def find(pattern_func):
            def _find(page):
                pattern = pattern_func()
                if encoding:
                    pattern = pattern.decode(encoding)
                try:
                    upage = page.decode('gb18030')
                    pattern = pattern
                except UnicodeDecodeError:
                    upage = page
                    pattern = pattern.encode('gb18030')
                ammount = len(re.findall(pattern, upage))
                return ammount
            return _find
        fw1w2 = p.justdoit(find(lambda :'%s%s' % (word1, word2)))
        fw2w3 = p.justdoit(find(lambda :'%s%s' % (word2, word3)))
        fw1w2w3 = p.justdoit(find(lambda :'%s%s%s' % (word1, word2, word3)))
        return (fw1w2, fw2w3, fw1w2w3)

class GoogleFreqDiscover(FrequencyDiscover):
    QUERY_URL_PATTERN = 'http://www.google.cn/search?%s'

    def get_freq(self, keyword, encoding=None):
        if encoding:
            params = urllib.urlencode({'q':self.quote(keyword.decode(encoding).encode('utf8'))})
        else:
            params = urllib.urlencode({'q':self.quote(keyword.encode('utf8'))})
        url = self.QUERY_URL_PATTERN % params 
        logger.debug('Query %s' % url)
        user_agent='Mozilla/3.0(compatible;MISE 5.5;Windows NT)'
        headers={'User-Agent':user_agent}
        p = Parser(url, headers)
        def find(page):
            pattern = ur'约有<b>(.*)</b>项符合'
            try:
                upage = page.decode('gb18030')
            except UnicodeDecodeError:
                upage = page
                pattern = pattern.encode('gb18030')
            ammount = 0
            for m in re.finditer(pattern, upage):
                ammount_text = m.group(1)
                def s2i(s):
                    return int(s.replace(',', ''))
                ammount = s2i(ammount_text)
                break
            if not ammount:
                logger.warning('Zero frequency for %s: %d' % (keyword, ammount))
            return ammount
        return p.justdoit(find)

class YahooFreqDiscover(FrequencyDiscover):
    QUERY_URL_PATTERN = 'http://search.cn.yahoo.com/search?%s'

    def get_freq(self, keyword, encoding=None):
        if encoding:
            params = urllib.urlencode({'p':self.quote(keyword.decode(encoding).encode('utf8'))})
        else:
            params = urllib.urlencode({'p':self.quote(keyword.encode('utf8'))})
        url = self.QUERY_URL_PATTERN % params 
        logger.debug('Query %s' % url)
        p = Parser(url)
        def find(page):
            pattern = r'找到相关网页约(.*)条'
            ammount = 0
            for m in re.finditer(pattern, page):
                ammount_text = m.group(1)
                def s2i(s):
                    return int(s.replace(',', ''))
                ammount = s2i(ammount_text)
                break
            if not ammount:
                logger.warning('Zero frequency for %s: %d' % (keyword, ammount))
            return ammount
        return p.justdoit(find)

class DiscoverWorker(threading.Thread):
    def init(self, id, iter, k_func, done_func, need_work_func, encoding=None, discover='baidu'):
        self.id = id
        self.iter = iter
        self.k_func = k_func
        self.done_func = done_func
        self.need_work_func = need_work_func
        assert discover in ('google', 'baidu', 'yahoo')
        if discover == 'baidu':
            self.fd = BaiduFreqDiscover()
        elif discover == 'google':
            self.fd = GoogleFreqDiscover()
        elif discover == 'yahoo':
            self.fd = YahooFreqDiscover()
        self.encoding = encoding

    def run(self):
        for i in self.iter:
            k = self.k_func(i)
            if self.need_work_func(self, k):
                f = self.fd.get_freq(k, self.encoding)
                self.done_func(self, self.id, k, f, i)

if __name__ == '__main__':
    logger.init()
    logger.info('Keyword frequency helper tool.')
    t = logger.Timer()

    l = ('张九龄', 'baidu', '百度', 'google', '谷歌', 'sogou', '搜狗', '分词', '中文分词', 'thisshouldbeammount0')
    #     0        1       2         3       4        5       6       7           8 # 1 worker
    #     0        1       0         1       0        1       0       1           0 # 2 workers
    #     0        1       2         0       1        2       0       1           2 # 3 workers
    fd = BaiduFreqDiscover()

    for k1, k2, k3 in (
        ('结', '合', '成'),
        ('结合', '成', '分'),
        ('结合', '成', '分子'),
    ):
        logger.info('%s %s %s tri-freq: %s' % (k1, k2, k3, fd.get_tri_freq(k1, k2, k3, encoding='utf8')))

    for k1, k2 in (
        ('结', '合'),
        ('结', '合成'),
        ('结合', '成'),
        ('结合', '成分'),
    ):
        logger.info('%s %s bi-freq: %d' % (k1, k2, fd.get_bi_freq(k1, k2, encoding='utf8')))

    t.start()
    for k in l:
        logger.info('%s freq: %d' % (k, fd.get_freq(k, encoding='utf8')))
    logger.info('Done! Elapsed time %s\n' % t.end())

    logger.info('Worker mode.')
    t = logger.Timer()
    t.start()
    worker_num = 6
    for i in xrange(worker_num):
        id = i
        #working_squence = [l[j] for j in xrange(i, len(l), worker_num)]
        working_squence = [l[j] for j in xrange(len(l)) if (j-id) % worker_num == 0]
        logger.info('Workder%d working squence: %s' % (id, working_squence))
        w = DiscoverWorker()
        def _done(worker, id, k, f, c):
            if hasattr(worker, 'foo'):
                logger.debug('Demo %s' % worker.foo)
            else:
                worker.foo = '%d' % id
                logger.debug('foo not exists')
            logger.info('Workder%d - %s freq: %d' % (id, k, f))

        w.init(id, working_squence, lambda a: a, _done, lambda w, b: True,  'utf8', discover='baidu')
        w.start()
    logger.info('Done! Elapsed time %s' % t.end())
