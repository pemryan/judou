from distutils.core import setup, Extension

setup(
        name = 'mmhash',
        version = '1.2',
        ext_modules = [
            Extension('mmhash', ['mmhash.cpp'],
                extra_compile_args=['-O3', '-pipe',
                '-fomit-frame-pointer']),
            ],
        description="MurmurHash2 http://murmurhash.googlepages.com/",
        long_description="""
import mmhash
print mmhash.get_hash(str(range(1000)))
-1624558063
print mmhash.get_unsigned_hash(str(range(1000)))
2670409233
        """
)
