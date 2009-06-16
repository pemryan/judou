from distutils.core import setup, Extension

setup(
        name = 'cztext',
        version = '1.0',
        ext_modules = [
            Extension('cztext', ['cztext.cpp'],
                extra_compile_args=['-O3', '-pipe',
                '-fomit-frame-pointer']),
            ],
)
