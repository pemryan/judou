all: multi_pattern_search.so


multi_pattern_search.so: search.cpp  search_py.cpp acsmx2.c 
	gcc -O3 -fPIC -shared -o  $@  -lboost_python -lpython2.5 -I/usr/include/python2.5 $^ 

install:multi_pattern_search.so
	cp multi_pattern_search.so /usr/lib/python2.5/site-packages/

