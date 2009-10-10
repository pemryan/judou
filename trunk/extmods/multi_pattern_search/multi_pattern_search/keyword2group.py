#!/usr/bin/env python
# -*- coding: utf-8 -*-

from array import array
from collections import defaultdict
from multi_pattern_search import MultiPatternSearch


class CensorKeyword(object):
    def __init__(self):
        self.txt = ""

    def _reload(self):
        self.group_name_list = []
        self.may_hav_keyword = []
        self.group_keyword = []
        self.single_keyword_to_cat_id = {}
        self.group_keyword_to_group_id = {}
        self.group_id_to_cat_id = array('I')
        self.group_keyword_length = array('B')
        self.single_search = MultiPatternSearch()
        self.group_search = MultiPatternSearch()

    def _init_search(self):
        self.may_hav_keyword = tuple(self.may_hav_keyword)
        self.group_keyword = tuple(self.group_keyword)
        self.group_name_list = tuple(self.group_name_list)

        for i in self.single_keyword_to_cat_id.keys():
            self.single_search.add_keyword(i)
        group_keyword_set = set()

        for i in self.group_keyword:
            group_keyword_set.update(i)

        for i in self.may_hav_keyword:
            if i:
                group_keyword_set.update( i[1] )


        for i in group_keyword_set:
            self.group_search.add_keyword(i)


    def _keyword_to_group_id(self):
        #词做倒排
        group_keyword_to_group_id = self.group_keyword_to_group_id
        for pos, group_keyword_list in enumerate(self.group_keyword):
            for keyword in group_keyword_list:
                if keyword not in group_keyword_to_group_id:
                    group_keyword_to_group_id[keyword] = array('I')
                group_keyword_to_group_id[keyword].append(pos)

    def load_txt(self, txt):
        if txt==self.txt:
            return
        
        self.txt = txt

        self._reload()

        SINGE_KEYWORD = 0
        GROUP_KEYWORD = 1
        MAY_HAV_KEYWORD = 2

        txt = txt.split("\n")
        state = SINGE_KEYWORD
        group_keyword = set()
        #处理文本
        for line in txt:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">>>"):
                if state == GROUP_KEYWORD:
                    line = line[3:].strip()
                    if line:
                        num = int(line)
                    else:
                        num = 1
                    may_hav_keyword = set()
                    state = MAY_HAV_KEYWORD
                else:
                    cat_id = len(self.group_name_list)
                    group_name_list = line[3:].strip()
                    self.group_name_list.append(group_name_list)
                    state = SINGE_KEYWORD
            elif len(line) == 1:
                if line == '{':
                    state = GROUP_KEYWORD
                elif line == "}":
                    if state == MAY_HAV_KEYWORD:
                        self.may_hav_keyword.append( (num, may_hav_keyword) )
                    else:
                        self.may_hav_keyword.append(None)
                    state = SINGE_KEYWORD
                    if group_keyword:
                        group_keyword = tuple(group_keyword)
                        self.group_keyword.append(group_keyword)
                        self.group_id_to_cat_id.append(cat_id)
                        self.group_keyword_length.append(len(group_keyword))
                        group_keyword = set()
            elif state == SINGE_KEYWORD:
                if line not in self.single_keyword_to_cat_id:
                    line = line.lower()
                    self.single_keyword_to_cat_id[line] = cat_id
            elif state == GROUP_KEYWORD:
                group_keyword.add(line)
            elif state == MAY_HAV_KEYWORD:
                may_hav_keyword.add(line)

        self._keyword_to_group_id()
        self._init_search()

    def which_group_id(self, text):
        total_group = len(self.group_name_list)
        group = total_group

        single_search = self.single_search.count(text)
        all_keys = single_search.keys()
        if single_search:
            for key in single_search.keys():
                cat_id = self.single_keyword_to_cat_id[key]
                if cat_id < group:
                    group = cat_id

        group_search = self.group_search.count(text)
        all_keys.extend(group_search.keys())
        all_keys = set(all_keys)

        group_count = defaultdict(int)
        for k in group_search.keys():
            group_id_list = self.group_keyword_to_group_id.get(k, ())
            for i in group_id_list:
                group_count[i]+=1

        for k, v in group_count.iteritems():
            if self.group_keyword_length[k] <= v:
                may_hav_keyword = self.may_hav_keyword[k]
                if may_hav_keyword:
                    min_num, may_set = may_hav_keyword
                    if len(may_set&all_keys)< min_num:
                        continue

                #返回最小的那个 事情比事后优先级高
                cat_id = self.group_id_to_cat_id[k]
                if cat_id < group:
                    group = cat_id

        # TODO 返回精确的命中关键词
        if group < total_group:
            return group, all_keys

    def which_group_name(self, text):
        pos = self.which_group_id(text)
        if pos is not None:
            pos , keywords = pos
            keywords = " ".join(keywords)
            return self.group_name_list[pos], keywords


if __name__ == "__main__":
    test_input = """
>>> 关键词表一
贵公司
{
中国
>>> 2
二十
地方
}

>>> 关键词表二
{
你们
>>> 1
我们
他们
}
"""
    censor_keyword = CensorKeyword()
    censor_keyword.load_txt(test_input)
    test = """dd"""

    print "\n".join(
    censor_keyword.which_group_name("贵公司的黄菊")
    )
    print censor_keyword.which_group_id("贵公司的黄菊")
    print censor_keyword.which_group_id("中国的二十个地方")
    print censor_keyword.which_group_id("你们我们他们")
