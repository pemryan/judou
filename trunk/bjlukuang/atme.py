# -*- coding: utf-8
from pyictclas import ictclas
from pybamboo import bamboo
from pysegment import pyseg


def stats(c, stats):
    if c in stats:
        stats[c] += 1
    else:
        stats[c] = 1

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-U', '--without-user-dict', dest='without_user_dict', action="store_true", default=False)
    parser.add_option('-O', '--output', dest='output', action="store", type="string", default="whitespace")
    parser.add_option('-S', '--segmenter', dest='segmenter', action="store", type="string", default="ictclas")
    (options, args) = parser.parse_args()

    if options.segmenter == 'ictclas':
        segmenter = ictclas
    elif options.segmenter == 'bamboo':
        segmenter = bamboo
    elif options.segmenter == 'pyseg':
        segmenter = pyseg
    segmenter.init()

    if options.without_user_dict == False:
        f = open('./cell/userdic-utf8.txt')
        line = f.readline()
        while line:
            w = line.strip()
            segmenter.add_user_word(w, 'ns')
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
        wline = segmenter.process(line)
        if options.output == 'whitespace':
            print wline
        wc = wline.split(' ')
        for w in wc:
            if w.strip():
                stats(w, words)
        if options.output == 'whitespace':
            print len(ansi), len(chars), len(words), total
        line = f.readline()

    f.close()

    if options.output == 'words':
        for w, c in words.items():
            print w, c

    segmenter.exit()
