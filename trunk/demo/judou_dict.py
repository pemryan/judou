# -*- coding: utf-8
# @desc: Tool which Build judou dicionary from cell dicts.
import os
import re
import sys
import sqlite3
import logging
from   datetime import datetime

import logger
import memcachedb
from   pinyin  import hanzi2pinyin
from   freq_helper  import DiscoverWorker


def sizeof_fmt(num):
   for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
       if num < 1024.0:
           return "%3.1f%s" % (num, x)
       num /= 1024.0

class DictBuilder(object):
    TXT_ENCODING = 'gb18030'
    sql_SELECT_ALL_CELLS = '''
    select id, name from cells where last_collect_error = 0;
    '''

    def __init__(self, cell_dict_txt_path):
        logging.debug('Cell dict txt files path is %s' % cell_dict_txt_path)
        self._cell_dict_txt_path = cell_dict_txt_path
        self._conn = sqlite3.connect(self._get_full_path('cell_dict.db'))

    def build(self):
        logging.debug("I'm busy...")
        cur = self._conn.cursor()
        cur.execute(self.sql_SELECT_ALL_CELLS)
        rows = cur.fetchall()
        logging.debug('%d working cells' % len(rows))
        for r in rows:
            self.build_cell(r)

    def build_cell(self, r):
        logging.debug(r)
        name = r[1]
        txt_fn = self._get_full_path('%d.txt' % r[0])
        byte_size = os.path.getsize(txt_fn)
        logging.info('Building cell %s %s(%s)' % (name, txt_fn, sizeof_fmt(byte_size)))
        f = open(txt_fn)
        for l in f.readlines():
            try:
                keyword = l.strip().decode(self.TXT_ENCODING)
            except UnicodeDecodeError:
                logging.exception('Could NOT decode %s' % ((keyword,),))
                continue
            if keyword:
                pinyin = hanzi2pinyin(keyword)
                l = (keyword, len(keyword), keyword[0], keyword[-1], pinyin)
                self.build_keyword(l)
        self.cell_done(txt_fn)
        f.close()

    def cell_done(self, fn):
        logging.debug('Cell %s done.' % fn)

    def build_keyword(self, l):
        '''
        (keyword, length, leading, ending, pinyin)
        0         1       2        3       4
        '''
        logging.debug('Cell line %s(%d)<%s, %s>%s' % l)

    def shutdown(self):
        self._conn.close()

    def _get_full_path(self, filename):
        return '%s%s' % (self._cell_dict_txt_path, filename)


class SQLiteDictBuilder(DictBuilder):
    sql_CREATE_DICT_TABLE = '''create table if not exists dictionary (id integer primary key autoincrement, keyword text unique, length integer, leading, ending text, pinyin text, keyword_index text, freq integer, flag integer)''' # NOTE: unique create index on keyword which will run code 5 times faster!!!
    sql_SELECT_KEYWORD = '''select * from dictionary where keyword=?'''
    sql_INSERT_KEYWORD = '''insert into dictionary values(NULL, ?, ?, ?, ?, ?, "", 0, 0)'''
    sql_SELECT_ALL = '''select id, keyword from dictionary'''
    sql_SELECT_HAS_ALPHANUM = 'select id, keyword from dictionary where keyword regexp "[a-zA-Z]+"'
    sql_UPDATE_FIXED = 'update dictionary set keyword=?, length=?, pinyin=? where id=?'
    sql_UPDATE_FREQ = 'update dictionary set freq=? where keyword=?'

    def __init__(self, *args):
        super(SQLiteDictBuilder, self).__init__(*args)

        dict_db_path = self.get_same_path('judou_dict.db3')
        logging.debug('Judou dict initing: %s' % dict_db_path)
        self.dict_conn = sqlite3.connect(dict_db_path)
        cur = self.dict_conn.cursor()
        cur.execute(self.sql_CREATE_DICT_TABLE)
        self.dict_conn.commit()

    def build_keyword(self, l):
        '''
        (keyword, length, leading, ending, pinyin)
        0         1       2        3       4
        '''
        super(SQLiteDictBuilder, self).build_keyword(l)

        cur = self.dict_conn.cursor()
        cur.execute(self.sql_SELECT_KEYWORD, (l[0], ))
        r = cur.fetchone()
        if r:
            logging.debug('Keyword exists: %s' % (r, ))
        else:
            logging.debug('Creating keyword %s...' % l[0])
            cur.execute(self.sql_INSERT_KEYWORD, l)
            #self.dict_conn.commit() # Remove this line will be 10 times fast!!!

    def cell_done(self, fn):
        self.dict_conn.commit()

    def shutdown(self):
        super(SQLiteDictBuilder, self).shutdown()

        self.dict_conn.close()
        logging.debug('Judou dict closed.')

    def get_same_path(self, filename):
        return '%s/%s' % (os.path.abspath(os.path.dirname(__file__)), filename)

    def inspect(self):
        logging.debug('Inspect keywords...')
        cur = self.dict_conn.cursor()

        def regexp(re_pattern, re_string):
            try:
                return bool(re.search(re_pattern, re_string))
            except:
                return False
        self.dict_conn.create_function('regexp', 2, regexp)

        for r in self.dict_conn.execute(self.sql_SELECT_HAS_ALPHANUM):
            id = r[0]
            keyword = r[1]
            # Segement should NOT contain any alpanum chars
            fixed_keyword = re.sub(r'[\s\w]+', '', keyword)
            if fixed_keyword:
                length = len(fixed_keyword)
                pinyin = hanzi2pinyin(fixed_keyword)
                logging.info('Will fix %d %s %s %d %s' % (id, keyword, fixed_keyword, length, pinyin))
                try:
                    self.dict_conn.execute(self.sql_INSERT_KEYWORD, (fixed_keyword, length, fixed_keyword[0], fixed_keyword[-1], pinyin))
                except sqlite3.IntegrityError:
                    logging.warning('Already had %s' % fixed_keyword)
        self.dict_conn.commit()

    def collect_freq(self, worker_num):
        logging.debug('Worker number is %d' % worker_num)
        def toworker(id, woker_id):
            return (id - worker_id) % worker_num == 0
        self.dict_conn.create_function('toworker', 2, toworker)
        for worker_id in xrange(worker_num):
            c = self.dict_conn.execute('select id, keyword from dictionary where toworker(id, ?)', (worker_id,))
            working_squence = c.fetchall()
            w = DiscoverWorker()
            def need_work(worker, k):
                if not hasattr(worker, 'mc'):
                    logger.debug('Worker%d setup memcachedb client' % worker.id)
                    worker.mc = memcachedb.Client(['127.0.0.1:21201'])
                f = worker.mc.get(k.encode('utf8'))
                if f:
                    return False
                else:
                    return True

            def _collect_freq(worker, id, k, f, c):
                logger.info('Workder%d - (%d)%s freq: %d' % (id, c[0], k, f))
                # SQLite db locked under multi-threading...
                #if not hasattr(worker, 'conn'):
                #    logger.debug('Worker%d open db conntection' % id)
                #    dict_db_path = self.get_same_path('judou_dict.db3')
                #    worker.conn = sqlite3.connect(dict_db_path)
                #worker.conn.execute(self.sql_UPDATE_FREQ, (f, k))
                #worker.conn.commit()
                if not hasattr(worker, 'mc'):
                    logger.debug('Worker%d setup memcachedb client' % worker.id)
                    worker.mc = memcachedb.Client(['127.0.0.1:21201'])
                worker.mc.set(k.encode('utf8'), f)
                logger.debug('%s' % worker.mc.get(k.encode('utf8')))

            w.init(worker_id, working_squence, lambda a: a[1], _collect_freq, need_work, discover='baidu')
            w.start()
            


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1]=='debug':
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level,
                       format='%(asctime)s %(levelname)s %(message)s')
    logging.info('Working on judou dictionary...')

    db = SQLiteDictBuilder('/home/ant/Desktop/judou/bin/cell_dict_txt/')
    menu = raw_input('Cell Dictionary Builder.\n1.Build and inspect words.\n2.Collect frequency of words.\nInput 1 or 2 to continue...\n')
    if menu not in ('1', '2'):
        sys.exit()
    start = datetime.now()
    if menu == '1':
        db.build()
        db.inspect()
    else:
        db.collect_freq(1000)
    db.shutdown()
    end = datetime.now()

    logging.info('Done! Elapsed time %s' % (end - start))
