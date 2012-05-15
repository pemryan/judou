# -*- coding: utf-8
import os
import segment

class PySegment:
    FRQ_DB = 'frq.db'

    def init(self):
        self.dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        frq_db = os.path.join(self.dir, self.FRQ_DB)
        self._cut = segment.get_cutter(frq_db)

    def process(self, text):
        return ' '.join(list(self._cut.parse(text.decode('utf-8'))))

    def clean(self):
        pass

    def exit(self):
        pass

    def add_user_word(self, w, pos):
        pass

pyseg = PySegment()
