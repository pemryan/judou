# -*- coding: utf-8
from pyictclas import ictclas

def stats(c, stats):
    if c in stats:
        stats[c] += 1
    else:
        stats[c] = 1

if __name__ == '__main__':
    ictclas.init()

    f = open('./cell/userdic-utf8.txt')
    line = f.readline()
    while line:
        w = line.strip()
        ictclas.add_user_word(w, 'ns')
        line = f.readline()
    f.close()

    total = 0
    ansi = {}
    chars = {}
    words = {}
    f = open('../tests/20120303-utf8.txt')
    line = f.readline()
    while line:
        unicode_line = line.decode('utf8')
        if unicode_line.find(u'@交通路况') != -1 and unicode_line.find(u'/@交通路况') == -1:
            pass
        else:
            line = f.readline()
            continue
        for c in unicode_line:
            total += 1
            if ord(c)<=255:
                stats(c, ansi)
            stats(c, chars)
        wline = ictclas.process(line)
        print wline
        wc = wline.split(' ')
        for w in wc:
            if w.strip():
                stats(w, words)
        print len(ansi), len(chars), len(words), total
        line = f.readline()

    f.close()

    ictclas.exit()
