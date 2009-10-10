#!/usr/binenv python
# -*- coding: utf-8

import socket
import logger

class JudouClient(object):
    def __init__(self, server_list):
        assert server_list
        self.server_list = server_list

    def seg(self, text):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host, port = self.round_robin()
        s.connect((host, port))
        s.send(text + '\r\n')
        data = s.recv(1024)
        s.close()

        return data

    def round_robin(self):
        pair = self.server_list[0].split(':')
        return pair[0], int(pair[1])

if __name__ == '__main__':
    logger.init()
    c = JudouClient(['localhost:7788'])
    for text in (
        '结合成分子时',
        '分词测试一',
        '胡锦涛在中共中央政治局第三十八次集体学习时强调以创新的精神加强网络文化建设和管理满足人民群众日益增长的精神文化需要',
        '我是中国人，不过我的语文不怎么好。',
        '时间就是生命',
        '在2000年我开始使用网名twinsant',
        '张店区大学生不看重大城市的户口本',
        '你认为学生会听老师的吗',
        '计算语言学课程是三个课时',
        '中华人民共和国',
        '有意见分歧',
        '为人民工作',
        '中国产品质量',
        '努力学习语法规则',
        '这样的人才能经受住考验',
        '学历史知识',
        '这事的确定不下来',
        '做完作业才能看电视',
        '独立自主和平等互利的原则',
        '他说的确实在理',
        '联合国教科文组织',
        '雪村先生创作了很多歌曲',
        '词语破碎处，无物存在',
        '圆周率是3.1415926',
        '歼10击落F117',
        '1979年那是一个春天有一位老人在中国的南海边画了一个圈',
        '国务院一月二十五日举行春节团拜会, 胡锦涛主席走进会场代表中央政治局致词。',
    ):
        t = logger.Timer()
        t.start()
        s = c.seg(text)
        if s:
            logger.info('%s. Time %s' % (s, t.end()))
        else:
            logger.error('%s: Time %s' % (text, t.end()))
