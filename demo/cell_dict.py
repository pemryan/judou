# -*- coding: utf-8
'''
This script grap Sogou Cell Dicitionary (http://pinyin.sogou.com/dict/) which formatted as txt file from web and write them into a directory, then store according information in a sqlite databse for each text file.

TODO:
    * Validate code style
    * Refactoring
'''
import urllib2, re, datetime, os, urllib, sys
import BeautifulSoup # http://www.crummy.com/software/BeautifulSoup/
import sqlite3 # Different in Python 2.4 and 2.5

HOME_PAGE_URL = 'http://pinyin.sogou.com/dict/'
CELL_LIST_ORDER_BY_CREATE_URL = HOME_PAGE_URL + 'list.php?o=crt'
CELL_HISTORY_URL_PATTERN = HOME_PAGE_URL + 'history.php?id=%d'
CELL_HISTORY_TXT_URL_PATTERN = HOME_PAGE_URL + 'history_txt.php?id=%d'
CELL_DICT_TXT_DIR = '/cell_dict_txt/'

class CellDict:
    def __init__(self, data_dir=None):
        self._soup = None
        self.data_dir = data_dir
        self.conn = sqlite3.connect(self.get_data_dir() + 'cell_dict.db')
        self.http_error = 0

    def stats(self):
        d = {}

        max_cell_id = self._get_max_cell_id()
        total_cell_number = self._get_total_cell_number()

        d['max_cell_id'] = max_cell_id
        d['total_cell_number'] = total_cell_number
        return d

    def cell_info(self, cell_id):
        d = {}

        try:
            self.encoding_bug = None
            page = urllib2.urlopen(CELL_HISTORY_URL_PATTERN % cell_id)
            charset = page.headers['Content-Type'].split(' charset=')[1].lower()
            soup = BeautifulSoup.BeautifulSoup(page, fromEncoding=charset)
            if soup.originalEncoding != charset:
                self.encoding_bug = charset

            name_a = soup.find('a', href=re.compile('^cell.php'))
            name = name_a.string
            if self.encoding_bug:
                originalString = ''.join([chr(ord(c)) for c in name])
                name = originalString.decode(charset)
            d['name'] = name

            table = soup.find('table', {'class':'historytable'})
            last_update_time_text = table.find('td', text=re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'))
            last_update_time = self.s2t(last_update_time_text)
            d['last_update_time'] = last_update_time

            history_txt_id_a = table.find('a', href=re.compile('^history_txt.php'))
            history_txt_id_text = re.match(r'^history_txt.php\?id=(\d+)', history_txt_id_a['href']).group(1)
            history_txt_id = int(history_txt_id_text)
            d['history_txt_id'] = history_txt_id
        except AttributeError:
            d = {}
            print 'Maybe deleted: %d' % cell_id
            pass
        except TypeError:
            d = {}
            print 'Maybe private: %d' % cell_id
            pass
        except UnicodeDecodeError:
            d = {}
            print 'ERROR UnicodeDecodeError %d' % cell_id
            pass
        except urllib2.HTTPError:
            d = {}
            print 'ERROR urllib2.HTTPError'
            self.http_error += 1
            if self.http_error == 10:
                time.sleep(60)
                self.http_error = 0
            pass

        return d


    def get_data_dir(self):
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


    def cell_db_info(self, cell_id):
        d = {}

        c = self.conn.cursor()
        c.execute('''
                  select * from cells where id=?
                  ''', (cell_id,))
        for r in c:
            if r[3]:
                d['last_update_time'] = self.s2t(r[3])
            else:
                d['last_update_time'] = datetime.datetime.now()
            d['last_collect_time'] = self.s2t(r[4])
            d['last_collect_error'] = int(r[5])

        return d

    def collect_cell(self, cell_id, reloadall=False):
        print 'Try to collect cell %d' % cell_id
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

        db_info = self.cell_db_info(cell_id)
        #print 'DB %s' % db_info
        if db_info and db_info['last_collect_error'] > 3:
            return

        info = self.cell_info(cell_id)
        #print 'WEB %s' % info
        now = datetime.datetime.now()

        c = self.conn.cursor()
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
                    c.execute('''
                          insert into cells values (?, ?, ?, ?, ?, ?)
                          ''', (cell_id, info['name'], info['history_txt_id'], self.t2s(info['last_update_time']), self.t2s(now), 0))
                except sqlite3.IntegrityError:
                    # Update name, history_txt_id, last_update_time, last_collect_time
                    print 'Re-download %s at %s' % (txt_path, self.t2s(now))
                    c.execute('''
                          update cells set name=?, last_update_time=?, last_collect_time=?, last_collect_error=? where id=?
                          ''', (info['name'], self.t2s(info['last_update_time']), self.t2s(now), 0, cell_id))
        else:
            try:
                c.execute('''
                      insert into cells values (?, ?, ?, ?, ?, ?)
                      ''', (cell_id, '', -1, '', self.t2s(now), 1))
            except sqlite3.IntegrityError:
                print 'Failed download %s at %s' % (txt_path, self.t2s(now))
                c.execute('''
                      update cells set last_collect_time=?, last_collect_error=? where id=?
                      ''', (self.t2s(now), db_info['last_collect_error'] + 1, cell_id))
        print
        self.conn.commit()

    def t2s(self, t):
        return t.strftime('%Y-%m-%d %H:%M:%S')

    def s2t(self, s):
        return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

    def collect_cells(self, limit=1, reloadall=False):
        stats = self.stats()
        if limit > stats['max_cell_id'] or limit==-1:
            limit = stats['max_cell_id']

        c = self.conn.cursor()
        c.execute('''
                  create table if not exists cells (id primary key, name text, history_txt_id integer, last_update_time text, last_collect_time text, last_collect_error integer)
                  ''')

        for i in xrange(1, limit+1):
            self.collect_cell(i, reloadall)

    def close(self):
        self.conn.commit()
        self.conn.close()

    def _get_max_cell_id(self):
        max_cell_id = 1

        if not self._soup:
            page = urllib2.urlopen(CELL_LIST_ORDER_BY_CREATE_URL)
            self._soup = BeautifulSoup.BeautifulSoup(page)

        max_cell_id_a = self._soup.find('a', href=re.compile('^cell.php'))
        max_cell_id_text = re.match(r'^cell.php\?id=(\d+)', max_cell_id_a['href']).group(1)
        max_cell_id = int(max_cell_id_text)

        return max_cell_id

    def _get_total_cell_number(self):
        total_cell_number = 0

        if not self._soup:
            page = urllib2.urlopen(CELL_LIST_ORDER_BY_CREATE_URL)
            self._soup = BeautifulSoup.BeautifulSoup(page)
        div = self._soup.find('div', {'class':'total'})
        try:
            total_cell_number_text = re.match(ur'(\d+)个', div.strong.string).group(1)
        except AttributeError:
            try:
                total_cell_number_text = re.match(ur'(\d+)个'.encode('gb18030'), div.strong.string).group(1)
            except AttributeError:
                print 'Something wrong!'
                print CELL_LIST_ORDER_BY_CREATE_URL
                print div
                sys.exit(1)
        total_cell_number = int(total_cell_number_text)

        return total_cell_number


if __name__ == '__main__':
    cd = CellDict()
    print cd.stats()
    #print cd.cell_info(1)
    info = cd.cell_info(0)
    if info:
        print info
    #print
    cd.collect_cells()
    #cd.collect_cell(109, True) # script

    #cd.collect_cell(11640) # 搜狗标准词库 Not public
    #
    #cd.collect_cell(11826) # 搜狗精选词库

    #cd.collect_cell(11377) # 搜狗标准大词库

    #cd.collect_cell(11817) # 搜狗万能词库

    #cd.collect_cell(4) # 网络流行新词

    #print
    #cd.collect_cells(10, True)
    # Unlimit collect
    #cd.collect_cells(-1)

    cd.close()
