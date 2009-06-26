# -*- coding: utf-8 -*-
# Last Modifed: 
"""But Another Chinese SEGmentation.

Summary
=======

Problem: Given a block of Chinese text, split it into a set of "words".

In: text, encoding of text
Out: a list of words, could be the actural text above if join together, each word is the same encoding with text.

To keep it simple in loop, we choose unicode as internal encoding, refer to
"Encoding Introduction" section for more information.

There are two basic problems in this task:
    * word definition
    * grain size of word

In IR system grain size of word should be as small as posible, and word should focus in set of special term and name.

Except above these, there are also some headaches we have to faced:
    * ambiguity segmentation: cause more rubish in search results
    * new named entity: transliterated foreign words and names, abbreviations, and personal, organization and company names etc.
    * varies way to written numbers

Three approaches are available at a high level:
    * statistical techniques(ST)
    * dicionary-based techniques(DT)
    * hybrid approach combining both(HA)

Approach disadvantage:
    * ST: data-sparseness
    * DT: size of and quality of the dictionary(domain-appropriate, out of date)
    * HA: a dicionary with part-of-speech and word frequency info(1.2 million entries in business) should be updated several times a period of time

REF:
    * 切分歧义字段的综合性分级处理方法, 孙斌
    * 中文分词, 詹卫东
      http://ccl.pku.edu.cn/doubtfire
    * Segmentation of Chinese Text, TOM EMERSON
      http://www.multilingual.com/FMPro?-db=archives&-format=ad%2fselected%5fresults.html&-lay=cgi&-sortfield=magazine%20number&-sortorder=descend&-op=eq&Ad%20Type=reprint&-max=1817529521&-recid=33266&-token=%5bFMP-currenttoken%5d&-find=
    * Overview of Chinese Word Segmentation, 孙茂松
      http://ccl.pku.edu.cn/doubtfire/link2file.asp?FileLink=/doubtfire/NLP/OVERVIEW/Overview%20of%20Chinese%20Word%20Segmentation.pdf
    * Overview of Chinese Parsing Technology, 刘群
      http://ccl.pku.edu.cn/doubtfire/link2file.asp?FileLink=/doubtfire/NLP/OVERVIEW/Overview%20of%20Chinese%20Parsing%20Technology.pdf

Research tools
==============

Public Segmenter
--------------
* 海量智能分词研究版
  http://www.hylanda.com/production/SegmentStudy.htm

* ICTCLAS
  http://www.nlp.org.cn/project/project.php?proj_id=6

Public corpus & lexicon
-----------------------

* 1998年人民日报语料库(1998.2)
* 搜狗实验室互联网词库(2006.10)
  http://www.sogou.com/labs/dl/w.html

Roadmap
=======

* Dictinary based approach: Not handle ambiguity and named entity

  1.CHaracter SEGmenter.
  2.Maximum Match SEGmenter.
  3.Reverse Maximum Match SEGmenter.
  4.ATOM SEGmenter.

* Statistic based approach: Handle simple ambiguity

  5.Data Structure: Word Graph.
  6.Maximum Probability Method(With unigram, is a special case of N-SP which N=1).

  TODO: {
  7.Shortest Path(N-Shortest Path).

* Statistic based approach: POS tagging and named entity recongnization

  8.Hidden Markov Model.

* Dictionary updating and improving framework: Keep up with the age

  9.Hybrid research approach.
  TODO: }


Memo
====

* Expectation Maximum?

* N-gram(unigram, bigram, trigram...)

unigram: 92%
P(W|S) = P(S|W)P(W)/P(S) ~= P(W) = P(w1,w2,...wi) ~= P(w1)P(w2)..P(wi)
P(wi) = number of wi in corpus n/total number of words N

P'(wi) = P'(wi-1)P(wi)
P'(w1) = P(w1)

used in Maximum Probability Method.

* Shortest Path(SP): Extend to N-SP

* Full Segmentation(FS)

Encoding Introduction
=====================

* ASCII: We all known this :)

* ISO-8859-1/Latin-1: Extend ASCII above 128

* GB2312(1980)/cp20936: First standard about Chinese encoding

 ** 7445 chars(6763 Chinese chars, 682 symbols), High Byte(HB)[B0-F7] LB[A1-FE], D7FA-D7FE not used.

* GBK(1995)/cp936: Factual standard encoding in PC industry, but not a standard of country.

 ** 21886 chars(21003 Chinese chars)

* GB18030(2000)/cp54936:  PC industry shold follow this country standard.

 ** 27484 chars

* BIG5/cp950: Traditional Chinese encoding
* GB12345(1990)

All of above belongs DBCS, and are big endian, the first bit of HB is always 1.

Compatibale: ASCII < GB2312 < GBK < GB18030

* Unicode(UCS)
 
 ** UCS-2: Python
 ** UCS-4

 ** UTF-8 : Compatibale with ISO-8859-1, one byte encode + three bytes encode
 ** UTF-16 : Two bytes encode

Compatibale: ASCII/ISO-8859-1 < Unicode

REF:
    * http://cscw.fudan.edu.cn/shaobin/study/code_cn.html
    * http://my.opera.com/lakeview/blog/show.dml/221495

===============================================================================
"""
import re
from math import log
import logger

# major.minor.patch
__revesion__ = '0.1.2'

# Max word length set to 8
MAX_LEN = 4
ENCODING = 'utf-8'

# Dictionary based approach
from word_dict import FooDict, SogouDict, JudouDict

# Preprocess segmentation
def ch_seg(text, encoding=None):
    """CHaracter SEGmentation.

    Return a list with each item will be one character.
    """
    # Internal unicode encoding
    if encoding:
        _text = text.decode(encoding)
    else:
        _text = text
    assert type(_text) is unicode

    # Loop and append each character to list
    ch_list = []
    if encoding:
        for character in _text:
            #yield character.encode(encoding)
            ch_list.append(character.encode(encoding))
    else:
        for character in _text:
            #yield character
            ch_list.append(character)

    return ch_list

def atom_seg(text, dict, encoding=None, export_word_graph=False):
    """Token(Atom) SEGmentation.

    Token or atom is each one Chinese character(Hanzi), number string and english word.
    e.g. 在2000年我开始使用网名twinsant
    Tokens seperated by space: 在 2000 年 我 开 始 使 用 网 名 twinsant
    """
    # Internal unicode encoding
    if encoding:
        _text = text.decode(encoding)
    else:
        _text = text
    assert type(_text) is unicode
    atom_list = []

    # See Python Library Reference 4.2.6
    # float: 2.71828
    # integer: 365
    # word: google AK47
    # NOT handled: Science format, etc.
    r = re.compile(r'[-+]?(\d+(\.\d*)?|\d*\.\d+)([eE][-+]?\d+)?|[-+]?(0[xX][\dA-Fa-f]+|0[0-7]*|\d+)|\w+')
    pos = 0
    if encoding:
        # Split items with each pattern
        for mo in r.finditer(_text):
            start, end = mo.span()
            for c in _text[pos:start]:
                atom_list.append(c.encode(encoding))
            atom_list.append(_text[start:end].encode(encoding))
            pos = end
        for c in _text[pos:]:
            atom_list.append(c.encode(encoding))
    else:
        # Same as above except not encode each item
        for mo in r.finditer(_text):
            start, end = mo.span()
            for c in _text[pos:start]:
                atom_list.append(c)
            atom_list.append(_text[start:end])
            pos = end
        for c in _text[pos:]:
            atom_list.append(c)
    if not atom_list:
        atom_list = ch_seg(_text)
    return atom_list

def bi_mm_seg(text, dict, encoding=None):
    mm_l = mm_seg(text, dict, encoding)
    rmm_l = rmm_seg(text, dict, encoding)
    return [i for i in set(mm_l) | set(rmm_l)]

def mm_seg(text, dict, encoding=None, export_word_graph=False):
    """The (Forward) Maximum Match SEGmentation.

    Starting on the left and moving to the right, find the longest word that exists in the dictionary, until you get to the end of the sentence.
    Precision: about 1/169
    """
    # Internal unicode encoding
    if encoding:
        _text = text.decode(encoding)
    else:
        _text = text
    assert type(_text) is unicode
    atom_list = atom_seg(_text, dict)

    word_list = []
    idx_s = 0
    idx_e = idx_s + MAX_LEN # Python handle out of index
    while idx_s < len(atom_list):
        found = False
        # Search word match in dictionary
        while idx_e - 1 > idx_s:
            word = ''.join(atom_list[idx_s:idx_e])
            #dbprint('atom_list[%d:%d]=%s' % (idx_s, idx_e, word.encode(encoding)))
            if word in dict:
                found = True
                #yield word.encode(encoding)
                word_list.append(word.encode(encoding))
                break
            idx_e -= 1
        # Hanzi
        if not found:
            word = ''.join(atom_list[idx_s:idx_e])
            #dbprint('Single char %s' % word.encode(encoding))
            #yield word.encode(encoding)
            word_list.append(word.encode(encoding))

        idx_s = idx_e
        idx_e = idx_s + MAX_LEN # Python handle out of index

    return word_list

def rmm_seg(text, dict, encoding=None, export_word_graph=False):
    """Reverse (Backward) Maximum Match SEGmentation.

    Conver string into unicode, then split it according the dictionary.
    Precision: about 1/245
    """
    # Internal unicode encoding
    if encoding:
        _text = text.decode(encoding)
    else:
        _text = text
    assert type(_text) is unicode
    atom_list = atom_seg(_text, dict)

    idx_e = len(atom_list)
    idx_s = idx_e - MAX_LEN
    if idx_s < 0:
        idx_s = 0

    word_list = []
    while idx_e > 0:
        found = False
        # Search word match in dictionary
        while idx_s + 1 < idx_e:
            word = ''.join(atom_list[idx_s:idx_e])
            #dbprint('atom_list[%d:%d]=%s' % (idx_s, idx_e, word.encode(encoding)))
            if word in dict:
                found = True
                #dbprint('Word atom_list[%d:%d]=%s' % (idx_s, idx_e, word.encode(encoding)))
                #yield word.encode(encoding)
                word_list.append(word.encode(encoding))
                break
            idx_s += 1
        # Hanzi
        if not found:
            word = ''.join(atom_list[idx_s:idx_e])
            #dbprint('Single char atom_list[%d:%d]=%s' % (idx_s, idx_e, word.encode(encoding)))
            #yield word.encode(encoding)
            word_list.append(word.encode(encoding))

        idx_e = idx_s
        idx_s = idx_e - MAX_LEN
        if idx_s < 0:
            idx_s = 0
    word_list.reverse()
    return word_list

def argmax_seg(text, dict, encoding=None, export_word_graph=False):
    """Maximum Probability Method SEGmentation.

    Build word graph, find the best path.
    e.g.
     结 合 成 分 子 时
    0  1  2  3  4  5  6
    Format:
        Prob: Word Probability
        CumProb: Cumulative Probability
        Index: (Start Index, End Index)
    (Word            ,       Prob,    CumProb,   Index))

    (                ,   0.000000,   0.000000,  (-1, 0)) # Dummy head
    (结              ,  10.192462,  10.192462,   (0, 1))
    (结合            ,   7.948717,   7.948717,   (0, 2))
    (合              ,   9.922798,  20.115260,   (1, 2))
    (合成            ,  11.984221,  22.176683,   (1, 3))
    (成              ,   7.775273,  15.723990,   (2, 3))
    (成分            ,  10.672035,  18.620752,   (2, 4))
    (分              ,   8.072198,  23.796188,   (3, 4))
    (分子            ,  10.168931,  25.892921,   (3, 5))
    (子              ,  11.532236,  30.152988,   (4, 5))
    (时              ,   6.865372,  32.758294,   (5, 6))
    结合 成 分子 时
    """
    # Internal unicode encoding
    if encoding:
        _text = text.decode(encoding)
    else:
        _text = text
    assert type(_text) is unicode

    # Build word graph
    wg = WordGraph()
    wg.build_word_graph(_text, dict, encoding)

    # Find the best path according Maximum Probability
    return wg.find_best_path()

class WordGraph(object):
    def build_word_graph(self, _text, dict, encoding):
        self.atom_list = atom_seg(_text, dict)

        self.word_graph = []
        idx_s = 0
        idx_e = idx_s
        self.word_graph.append((u'^', 0.0, 0.0, (-1, 0)))
        while idx_s < len(self.atom_list):
            while idx_e < idx_s + MAX_LEN:
                if idx_e > len(self.atom_list):
                    break
                idx = (idx_s, idx_e)
                word = ''.join(self.atom_list[idx_s:idx_e])
                #dbprint('self.atom_list[%d:%d]=%s' % (idx_s, idx_e, word.encode(encoding)))
                if idx_e - idx_s == 1 or word in dict:
                    #yield word.encode(encoding)
                    if word in dict:
                        pw = dict[word]
                    else:
                        pw = dict['#epsilon#']
                    p = pw + self.find_best_prob(idx[0])
                    self.word_graph.append((word, pw, p, idx))
                idx_e += 1

            idx_s += 1
            idx_e = idx_s
        self.word_graph.append((u'$', 0.0, 0.0, (len(self.atom_list), -1)))
        #print '\n'.join(['(%-16s, %10f, %10f, %8s)' % (w, p, ps, idx) for w, p, ps, idx in self.word_graph])

    def find_best_path(self):
        best_word_list = []
        i = len(self.word_graph) - 1
        idx_s = len(self.atom_list)
        while i > 0:
            i_prev = self.find_best_i(i, idx_s)
            if i_prev == -1:
                break
            best_word_list.append(i_prev)
            i = i_prev
            idx_s = self.word_graph[i][3][0]
        #print best_word_list

        # Build the words
        w_l = [self.word_graph[i][0].encode('utf-8') for i in best_word_list]
        w_l.reverse()
        return w_l

    def all_atoms(self):
        return [w[0].encode('utf-8') for w in self.word_graph if w[0] and w[0] not in (u'^', u'$')]

    def find_best_prob(self, idx_s):
        """Find prev best probability before the word.
        """
        pl = []
        for w, p, ps, idx in self.word_graph:
            if idx[1] == idx_s:
                pl.append(ps)
        return sorted(pl)[0]

    def find_best_i(self, i, idx_s):
        """Find index which probability is the best before index i.
        """
        #print len(self.word_graph), i, idx_s
        l = []
        for idx in xrange(i, 0, -1):
            idx_e = self.word_graph[idx][3][1]
            ps = self.word_graph[idx][2]
            if idx_e == idx_s:
                l.append((ps, idx))
        #print l
        if l:
            i_prev = sorted(l)[0][1]
        else:
            i_prev = -1
        return i_prev

    def export_graph(self, fn, dict):
        import networkx as nx
        G = nx.DiGraph()
        for i in xrange(len(self.word_graph)):
            pw = self.word_graph[i][0]
            pid = i
            def to_node_label(w, id):
                #return '%d. %s(%.2f)' % (id, w.encode('utf-8'), dict[w]) # rich format
                return '%s' % (w.encode('utf-8'),)
            prev_word_label = to_node_label(pw, pid)
            next_words = self.find_next_words(i)
            for next_word in next_words:
                w, id = next_word[0], next_word[1]
                next_word_label = to_node_label(w, id)
                bfq = dict.get_bi_freq(pw, w)
                if bfq > 0:
                    color = 'red'
                    style = 'solid'
                else:
                    color = 'black'
                    style = 'dashed'

                attr = {'label':'%d' % bfq, 'color':color, 'style':style}
                #G.add_edge(prev_word_label, next_word_label, attr) # rich format
                G.add_edge(prev_word_label, next_word_label)

        # Virtualization with matplotlib
        #import matplotlib.pyplot as plt
        #nx.draw_graphviz(G, 'dot')
        ##nx.draw_graphviz(G, 'neato')
        ##nx.draw_spectral(G)
        #plt.show()

        # Virtualization with graphviz
        a = nx.to_agraph(G)
        a.layout('dot')
        a.draw('%s.png' % fn)

    def export_graph2(self, fn, dict):
        import networkx as nx
        G = nx.DiGraph()
        for i in xrange(len(self.word_graph)):
            pw = self.word_graph[i][0]
            pid = i
            def to_node_label(w, id):
                return '%d. %s(%.2f)' % (id, w.encode('utf-8'), dict[w]) # rich format
            prev_word_label = to_node_label(pw, pid)
            next_words = self.find_next_words(i)
            for next_word in next_words:
                w, id = next_word[0], next_word[1]
                next_word_label = to_node_label(w, id)
                bfq = dict.get_bi_freq(pw, w)
                if bfq > 0:
                    color = 'red'
                    style = 'solid'
                else:
                    color = 'black'
                    style = 'dashed'

                attr = {'label':'%d' % bfq, 'color':color, 'style':style}
                G.add_edge(prev_word_label, next_word_label, attr) # rich format

        # Virtualization with graphviz
        a = nx.to_agraph(G)
        a.layout('dot')
        a.draw('%s.png' % fn)

    def find_next_words(self, target_idx):
        w, p, ps, idx = self.word_graph[target_idx]
        wl = []
        for i in xrange(target_idx+1, len(self.word_graph)):
            w, p, ps, f_idx = self.word_graph[i]
            if idx[1] == f_idx[0]:
                wl.append((w, i))
        return wl


def full_seg(text, dict, encoding=None, export_word_graph=False):
    """FULL SEGmentation.

    """
    # Internal unicode encoding
    if encoding:
        _text = text.decode(encoding)
    else:
        _text = text
    assert type(_text) is unicode
    atom_list = atom_seg(_text, dict)

    # Build word graph
    wg = WordGraph()
    wg.build_word_graph(_text, dict, encoding)
    if logger.is_debug() or export_word_graph:
        wg.export_graph2(text, dict)

    return wg.all_atoms()

def print_mem_footprint(DictClass):
    def _print_mem_footprint():
        from guppy import hpy
        
        h = hpy()
        print h.heap()

        d = DictClass()
        d.load()
        print h.heap()
    return _print_mem_footprint

print_foo_dict_mem_footprint = print_mem_footprint(FooDict)
print_sogou_dict_mem_footprint = print_mem_footprint(SogouDict)

# Test cases
# Entry point
if __name__ == '__main__':
    #print_foo_dict_mem_footprint()
    #print_sogou_dict_mem_footprint()
    test_cases = (
            ('结合成分子时',),
            ('分词测试一',),
            ('胡锦涛在中共中央政治局第三十八次集体学习时强调以创新的精神加强网络文化建设和管理满足人民群众日益增长的精神文化需要',),
            ('我是中国人，不过我的语文不怎么好。',),
            ('时间就是生命',),
            ('在2000年我开始使用网名twinsant',),
            ('张店区大学生不看重大城市的户口本',),
            ('你认为学生会听老师的吗',),
            ('计算语言学课程是三个课时',),
            ('中华人民共和国',),
            ('有意见分歧',),
            ('为人民工作',),
            ('中国产品质量',),
            ('努力学习语法规则',),
            ('这样的人才能经受住考验',),
            ('学历史知识',),
            ('这事的确定不下来',),
            ('做完作业才能看电视',),
            ('独立自主和平等互利的原则',),
            ('他说的确实在理',),
            ('联合国教科文组织',),
            ('雪村先生创作了很多歌曲',),
            ('词语破碎处，无物存在',),
            ('圆周率是3.1415926',),
            ('歼10击落F117',),
            ('1979年那是一个春天有一位老人在中国的南海边画了一个圈',),
            ('工信处女干事每月经过下属科室都要亲口交代24口交换机等技术性器件的安装工作', True),

            # invalid '1979年那是一个春天\n有一位老人在中国的南海边画了一个圈',
            )

    def test_case(seg, dict, n):
        print '-- Case %d by %s --' % (n, seg.__name__)
        if len(test_cases[n])>1:
            export_word_graph = test_cases[n][1]
        else:
            export_word_graph = False
        text = test_cases[n][0]
        print ' '.join(seg(text, dict, encoding=ENCODING, export_word_graph=export_word_graph))

    def test_with_dict(DictClass):
        print '-- Load dictionary %s --' % DictClass.__name__
        d = DictClass()
        d.load()
        for i in xrange(len(test_cases)):
            test_case(atom_seg, d, i)
            test_case(mm_seg, d, i)
            test_case(rmm_seg, d, i)
            test_case(argmax_seg, d, i)
            test_case(full_seg, d, i)
            print

    logger.init()
    for c in (JudouDict,):# SogouDict, FooDict):
        t = logger.Timer()
        t.start()
        test_with_dict(c)
        logger.info('Done. Time %s' % t.end())
        #raw_input('Press Enter to continue...')

# vim: set enc=utf-8:
