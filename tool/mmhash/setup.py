from distutils.core import setup, Extension

setup(
        name = 'mmhash',
        version = '1.1',
        ext_modules = [
            Extension('mmhash', ['mmhash.cpp'],
                extra_compile_args=['-O3', '-pipe',
                '-fomit-frame-pointer']),
            ],
        description="MurmurHash2 http://murmurhash.googlepages.com/",
)
