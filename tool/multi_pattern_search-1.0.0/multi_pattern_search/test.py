#coding=utf-8

from multi_pattern_search import MultiPatternSearch

search = MultiPatternSearch()
search.add_keyword("张沈鹏")
search.add_keyword("我是")

print search.exist("asdga sddqbq 珍珠饰张沈鹏品 ")
for k, v in search.count("我是张沈鹏.我是张沈鹏.我是张沈鹏.我是张沈鹏.").iteritems():
    print k.decode('utf-8'), v


