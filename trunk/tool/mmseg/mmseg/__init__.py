#coding:utf-8

def seg_txt(text):
    import mmseg
    mmseg.dict_load_defaults()
    def _seg_txt(text):
        algor = mmseg.Algorithm(text)
        for tok in algor:
            yield tok.text

    r = _seg_txt(text)
    global seg_txt
    seg_txt = _seg_txt

    return r


if __name__ == "__main__":
    text = """　六大门派围攻光明顶的时候被周芷若的倚天剑刺了一下（重伤，周手下留情，另张喜欢上周，没夺倚天被偷袭）
    """
    from collections import defaultdict
    word_count = defaultdict(int)
    for word in seg_txt(text):
        print word,
