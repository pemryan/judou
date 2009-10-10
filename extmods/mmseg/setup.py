#coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
from  setuptools import   find_packages
from distutils.core import Extension,setup
setup(
    name='mmseg',
    description="MMseg中文分词 Chinese Seg On MMSeg Algorithm",
    version='1.1.7',
    author_email="zsp007@gmail.com",
    packages = find_packages(),
package_data={
"mmseg.data":["*.dic"],
},
long_description="""
from mmseg import seg_txt
for i in seg_txt("最主要的更动是：张无忌最后没有选定自己的配偶。"):
    print i
""",
ext_modules =[
    Extension(
    "mmseg",
"""
mmseg/mmseg_cpp/algor.cpp  mmseg/mmseg_cpp/dict.cpp  mmseg/mmseg_cpp/memory.cpp  mmseg/mmseg_cpp/mmseg.cpp
""".split(),
    extra_compile_args=["-O3"],
    depends="""
mmseg/mmseg_cpp/algor.h  mmseg/mmseg_cpp/dict.h    mmseg/mmseg_cpp/rules.h
mmseg/mmseg_cpp/word.h
mmseg/mmseg_cpp/chunk.h  mmseg/mmseg_cpp/memory.h  mmseg/mmseg_cpp/token.h
    """.split(),
    )
],
)


