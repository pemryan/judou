#!/usr/bin/env python
# -*- coding: utf-8

'''cell_dict.py

http://code.google.com/p/judou

Description:
    This script grap from web the Sogou Cell Dicitionary
    (http://pinyin.sogou.com/dict/), download the txt files,
    write them into a directory, then store the according information
    in a sqlite databse for each text file.

TODO:
    * Validate code style
    * Refactoring

ChangeLog:
    * twinsant 2009-06-18 created
    * pem      2009-06-23 revised  to make it more readable
    * pem      2009-07-07 revised
'''

import os
import sys
import datetime
import urllib
import urllib2
import re
import BeautifulSoup # http://www.crummy.com/software/BeautifulSoup/
import sqlite3       # this module has different behaviour in Python 2.4 and 2.5

CELL_DICT_TXT_DIR = '/cell_dict_txt/'  # dir for formated cell dict text files
HOME_PAGE_URL = 'http://pinyin.sogou.com/dict/'
CELL_LIST_ORDER_BY_CREATE_URL = HOME_PAGE_URL + 'list.php?o=crt'
CELL_HISTORY_URL_PATTERN = HOME_PAGE_URL + 'history.php?id=%d'
CELL_HISTORY_TXT_URL_PATTERN = HOME_PAGE_URL + 'history_txt.php?id=%d'


def time2str(time):
    ''' convert datetime to string like 2009-06-22 19:17:28 '''
    return time.strftime('%Y-%m-%d %H:%M:%S')

def str2time(string):
    ''' convert string like 2009-06-22 19:17:28 to datetime '''
    return datetime.datetime.strptime(string, '%Y-%m-%d %H:%M:%S')

class CellDict:
    ''' implementation of the steps as in 'Description '''

    def __init__(self, data_dir=None):
        ''' initalize '''
        self._soup = None
        self.data_dir = data_dir
        self.http_error = 0
        self.conn = sqlite3.connect(self.get_data_dir() + 'cell_dict.db')

    def db_conn_close(self):
        ''' Close db connection '''
        self.conn.commit()
        self.conn.close()

    def get_data_dir(self):
        ''' '''
        dir = './'
        if self.data_dir:
            dir = self.data_dir + CELL_DICT_TXT_DIR
        else:
            dir = os.path.abspath(os.path.dirname(__file__)) + CELL_DICT_TXT_DIR
        try:
            os.makedirs(dir)
        except OSError:
            pass
        return dir

    def get_cell_stats(self):
        ''' Return $max_cell_id' and $total_cell_number'''
        cell_stats = {}

        max_cell_id = self._get_max_cell_id()
        total_cell_number = self._get_total_cell_number()

        cell_stats['max_cell_id'] = max_cell_id
        cell_stats['total_cell_number'] = total_cell_number
        return cell_stats


    def get_cell_info(self, cell_id):
        '''
        return the info of the cell dict with the specified cell_id:
        name
        last update time
        history cell txt id
        '''
        cell_info = {}

        try:
            self.encoding_bug = None
            # http://pinyin.sogou.com/dict/history.php?id=17641
            page = urllib2.urlopen(CELL_HISTORY_URL_PATTERN % cell_id)
            # charset (currently gb2312)
            charset = page.headers['Content-Type'].split(' charset=')[1].lower()

            soup = BeautifulSoup.BeautifulSoup(page, fromEncoding=charset)
            if soup.originalEncoding != charset:
                self.encoding_bug = charset

            # name of this cell dict. if cannot find, catch AttributeError
            name = soup.find('a', href=re.compile('^cell.php')).string
            if self.encoding_bug:
                originalString = ''.join([chr(ord(char)) for char in name])
                name = originalString.decode(charset)
            cell_info['name'] = name
            #print name

            # last update time of this cell dict
            table = soup.find('table', {'class':'historytable'})
            last_update_time_string = table.find('td', text=re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'))
            last_update_time = str2time(last_update_time_string)
            cell_info['last_update_time'] = last_update_time

            # the id of the historical version of this dict
            history_txt_id_a = table.find('a', href=re.compile('^history_txt.php'))
            history_txt_id_text = re.match(r'^history_txt.php\?id=(\d+)', history_txt_id_a['href']).group(1)
            history_txt_id = int(history_txt_id_text)

            cell_info['history_txt_id'] = history_txt_id
        except AttributeError:
            cell_info = {}
            print 'Maybe deleted: %d' % cell_id
            pass
        except TypeError:
            cell_info = {}
            print 'Maybe private: %d' % cell_id
            pass
        except UnicodeDecodeError:
            cell_info = {}
            print 'ERROR UnicodeDecodeError %d' % cell_id
            pass
        except urllib2.HTTPError:
            cell_info = {}
            print 'ERROR urllib2.HTTPError'
            self.http_error += 1
            if self.http_error == 10:
                time.sleep(60)
                self.http_error = 0
            pass

        return cell_info


    def get_db_info(self, cell_id):
        ''' db_info: get info of the cell dict with cell_id from the sqlitedb
            in:   cell_id
            out:     last_update_time
                     last_collect_time
                     last_collect_error
        '''
        db_info = {}

        cell_cursor = self.conn.cursor()
        cell_cursor.execute('''
                  select * from cells where id=?
                  ''', (cell_id,))
        for r in cell_cursor:
            if r[3]:
                db_info['last_update_time'] = str2time(r[3])
            else:
                db_info['last_update_time'] = datetime.datetime.now()
            db_info['last_collect_time'] = str2time(r[4])
            db_info['last_collect_error'] = int(r[5])

        return db_info

    def collect_cell(self, cell_id, reloadall=False):
        '''
        collect the dict specified by cell_id:
            grap the dict txt file
            put dict info into sqlitedb
        '''
        print 'Trying to collect cell dict with id = %d' % cell_id

        txt_path = self.get_data_dir() + '%d.txt' % cell_id
        file_not_exists = False
        file_deleted_or_private = False
        try:
            f = open(txt_path)
            first_line = f.readline()
            if first_line.decode('gb18030').startswith('<script>'):
                file_deleted_or_private = True
        except IOError:
            file_not_exists = True
            print 'Not exists: %s' % txt_path

        db_info = self.get_db_info(cell_id)
        #print 'DB %s' % db_info
        if db_info and db_info['last_collect_error'] > 3:
            return

        info = self.get_cell_info(cell_id)
        #print 'WEB %s' % info
        now = datetime.datetime.now()

        cell_cursor = self.conn.cursor()

        if info:
            # Get txt file, if txt file not exists or last_update_time > last_collect_time or last_collect_error>0
            if db_info:
                txt_is_new = info['last_update_time'] > db_info['last_collect_time']
                last_collect_error = db_info['last_collect_error']
            else:
                txt_is_new = True
                last_collect_error = 1

            if reloadall or file_not_exists or file_deleted_or_private or txt_is_new or last_collect_error > 0:
                txt_url = CELL_HISTORY_TXT_URL_PATTERN % info['history_txt_id']

                print '%s -> %s' % (txt_url, txt_path)
                urllib.urlretrieve(txt_url, txt_path)

                try:
                    cell_cursor.execute('''
                          insert into cells values (?, ?, ?, ?, ?, ?)
                          ''', (cell_id, info['name'], info['history_txt_id'], time2str(info['last_update_time']), time2str(now), 0))
                except sqlite3.IntegrityError:
                    # Update name, history_txt_id, last_update_time, last_collect_time
                    print 'Re-download %s at %s' % (txt_path, time2str(now))
                    c.execute('''
                          update cells set name=?, last_update_time=?, last_collect_time=?, last_collect_error=? where id=?
                          ''', (info['name'], time2str(info['last_update_time']), time2str(now), 0, cell_id))
        else:
            try:
                cell_cursor.execute('''
                      insert into cells values (?, ?, ?, ?, ?, ?)
                      ''', (cell_id, '', -1, '', time2str(now), 1))
            except sqlite3.IntegrityError:
                print 'Failed download %s at %s' % (txt_path, time2str(now))
                cell_cursor.execute('''
                      update cells set last_collect_time=?, last_collect_error=? where id=?
                      ''', (time2str(now), db_info['last_collect_error'] + 1, cell_id))
        print
        self.conn.commit()

    def _get_total_cell_number(self):
        '''
        get the total number of cell dicts
        from this url: CELL_LIST_ORDER_BY_CREATE_URL
        '''
        total_cell_number = 0

        if not self._soup:
            page = urllib2.urlopen(CELL_LIST_ORDER_BY_CREATE_URL)
            self._soup = BeautifulSoup.BeautifulSoup(page)
        div = self._soup.find('div', {'class':'total'})
        #grap from the url: 目前共有细胞词库 xxxxx个
        try:
            total_cell_number_text = re.match(ur'(\d+)个', div.strong.string).group(1)
        except AttributeError:
            try:
                total_cell_number_text = re.match(ur'(\d+)个'.encode('gb18030'), div.strong.string).group(1)
            except AttributeError:
                print 'I cannot get total cell number, please check this URL'
                print CELL_LIST_ORDER_BY_CREATE_URL
                print div
                sys.exit(1)

        total_cell_number = int(total_cell_number_text)
        return total_cell_number

    def _get_max_cell_id(self):
        '''
        get the max id of cell dicts
        from this links in this url: CELL_LIST_ORDER_BY_CREATE_URL
        '''
        max_cell_id = 1

        if not self._soup:
            page = urllib2.urlopen(CELL_LIST_ORDER_BY_CREATE_URL)
            self._soup = BeautifulSoup.BeautifulSoup(page)
        # 从 http://pinyin.sogou.com/dict/cell.php?id=17641 中取出 17641
        max_cell_id_name = self._soup.find('a', href=re.compile('^cell.php'))
        max_cell_id_string = re.match(r'^cell.php\?id=(\d+)', max_cell_id_name['href']).group(1)
        max_cell_id = int(max_cell_id_string)
        return max_cell_id


def collect_all_cells(limit=1, reloadall=False):
    '''collect cell dicts in bulk
    for example:
        collect_all_cells(10) will fetch the dicts with id=1~10
    '''
    dic = CellDict()
    stats = dic.get_cell_stats()
    print stats

    if limit > stats['max_cell_id'] or limit==-1:
        limit = stats['max_cell_id']

    cell_cursor = dic.conn.cursor()
    cell_cursor.execute('''
                create table if not exists cells (id primary key, name text, history_txt_id integer, last_update_time text, last_collect_time text, last_collect_error integer)
                ''')

    for i in xrange(1, limit+1):
        dic.collect_cell(i, reloadall)

    dic.db_conn_close()

#def main():
    #dic = CellDict()
    #print dic.get_cell_stats()
    ##print cd.get_cell_info(1)
    #info = dic.get_cell_info(0)
    #if info:
        #print info
    ##print
    #dic.collect_all_cells()
    ##dic.collect_cell(109, True) # script
    ##dic.collect_cell(11640) # 搜狗标准词库 Not public
    ##dic.collect_cell(11826) # 搜狗精选词库
    ##dic.collect_cell(11377) # 搜狗标准大词库
    ##dic.collect_cell(11817) # 搜狗万能词库
    ##dic.collect_cell(4)     # 网络流行新词

    ##print
    ##dic.collect_cells(10, True)
    ## Unlimit collect
    ##dic.collect_cells(-1)

    #dic.db_conn_close()

if __name__ == '__main__':
    import socket
    socket.setdefaulttimeout(30)
    collect_all_cells(10)
