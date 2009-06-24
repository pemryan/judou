#
CC            = gcc
CXX           = g++
CFLAGS        = -O3 -fPIC -shared -pipe -g -Wall
CXXFLAGS      = -O3 -fPIC -shared -pipe -g -Wall
PYTHON        = python2.5
INCPATH       = -I/usr/include/$(PYTHON)
LIB           = -lboost_python -l$(PYTHON)


all: multi_pattern_search.so


multi_pattern_search.so: search.cpp  search_py.cpp acsmx2.c 
	$(CC) $(CFLAGS) -o  $@  $(LIB) $(INCPATH)  $^


install:multi_pattern_search.so
	cp multi_pattern_search.so /usr/lib/$(PYTHON)/site-packages/

uninstall: multi_pattern_search.so
	rm /usr/lib/$(PYTHON)/site-packages/multi_pattern_search.so

clean:
	rm -f  multi_pattern_search.so

