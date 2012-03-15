# -*- coding: utf-8
from pyictclas import ictclas

if __name__ == '__main__':
    ictclas.init()
    print ictclas.process('中文分词')
    for w in ictclas.process_a('中文分词'):
        print w
    print ictclas.finger_print()
    ictclas.process_a('中文分词')
    print ictclas.finger_print()

    t2 = '点击下载超女纪敏佳深受观众喜爱。禽流感爆发在非典之后。'
    print ictclas.process(t2)
    ictclas.process_a(t2)
    print ictclas.finger_print()
    assert ictclas.add_user_word('点击', 'v')
    assert ictclas.save_the_usr_dic()
    print ictclas.process(t2)
    assert ictclas.del_usr_word('点击')
    print ictclas.process(t2)

    t3 = '明天上午将举行北京国际长跑节，比赛起点设在天安门广场，终点设在先农坛体育场。比赛进行期间，珠市口西大街、前门大街、天坛东路等相关比赛路段将会采取临时交通管理措施，南部城区出行可以选择南二环行驶。 '
    print ictclas.process(t3)

    ictclas.exit()
