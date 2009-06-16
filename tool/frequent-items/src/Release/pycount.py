#coding:utf-8

#0.001 是要统计的频率下限
from pyzlcl import Lcl
from mmhash import get_hash
from array import array
from mmhash import get_hash

def _cn_en_iter(line):
    line = line.decode("utf-8")
    pre_char = ""
    for i in line:
        if u'\u4e00' <= i < u'\u9fa6':
            if pre_char:
                yield pre_char, 3, True
                pre_char = ""
            yield i, 1 , False
        elif u'a' <= i <= u'z' or u'0' <= i <= u'9':
            pre_char += i
        elif u'A' <= i <= u'Z':
            pre_char += i.lower()
        elif pre_char:
            yield pre_char,3, True
            pre_char = ""

    if pre_char:
        yield pre_char,3, True

def cn_en_iter(line):
    for char, char_length, is_word in _cn_en_iter(line):
        yield char.encode("utf-8", "ignore"), char_length, is_word


class Digg(object):
    def update(self, word):

        lcl = self.lcl
        word_dict = self.word_dict

        if self.count%500 == 1:
            for k, v in lcl.output(10):
                lcl.update(k, -v)
            if self.count > 1000000:
                self.lcl = Lcl(self.min_frequent)

        if word in word_dict:
            word_dict[word]+=1
        else:
            hash = get_hash(word)
            print word, hash
            lcl.update(hash, 1)

        self.count+=1


    def __init__(self, min_frequent=0.0001):
        self.min_frequent = min_frequent
        self.lcl = Lcl(min_frequent)
        self.word_dict = {}
        self.count = 0

    def add_line(self, line):
        len_buffer = array('I')
        char_buffer = list()
        for char, char_length, is_word in cn_en_iter(line):
            len_buffer.append(char_length)
            char_buffer.append(char)

            while sum(len_buffer)> 7:
                len_buffer.pop(0)
                char_buffer.popleft()

            if is_word:
                print "((("
                self.update(char)


            char_buffer_len = len(char_buffer)
            for a in xrange(0, char_buffer_len-2):
                for b in xrange(a+2, char_buffer_len):
                    print a, b, "!!"
                    word = "".join(char_buffer[a:b])
                    self.update(word)

if __name__ == "__main__":
    test_text = """
    书不是借来的就不能好好地去读。您没有听说过那些收藏书籍的人的事吗？七略四库是天子的藏书，但是天子中读书的人又有几个？搬运时使牛累得出汗，放置在家就堆满屋子的书是富贵人家的书，但是富贵人家中读书的又有几个？其余像祖辈父辈积藏许多图书、子辈孙辈丢弃图书的情况就更不用说了。不只书籍是这样，天下的事物都这样。不是那人自己的东西而勉强向别人借来，他一定会担心别人催着要回，就忧惧地摩挲抚弄那东西久久不停，说：‘今天存放在这里，明天就要拿走了，我不能再看到它了。’如果已经被我占有，必定会把它捆起来放在高处，收藏起来，说：‘暂且等待日后再看’如此而已
    (Translated Text译文)书非借不能读也。
    这其实是说过去一个人由于受各种条件的限制，买不到（或买不起也有可能）自己喜爱的读物，只好或只能找各种渠道借书研读，因而分外珍惜这来之不易的机会，所以读起来格外用心等等。单纯按字面翻译是错误的。It would deeply impress one reading through the books borrowed with particular favour.
    """

    for i in cn_en_iter(test_text):
        print i[0],

    digg = Digg()
    digg.add_line(test_text)
