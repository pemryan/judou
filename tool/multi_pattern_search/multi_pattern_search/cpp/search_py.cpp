#include <boost/python.hpp>
#include <boost/python/dict.hpp>
#include "search.hpp"

using namespace boost::python;
/*
	void keyword(char* word)
	void clear()
	char_uint search(char* content,unsigned length=0)
*/
  
class SearchPy{
	Search _search;
public:
	SearchPy():_search(){

	}
	void add_keyword(char* word){
		_search.add_keyword(word);
	}
	void clear(){
		_search.clear();
	}
	bool exist(char* sub){
        return _search.exist(sub);
    }
	dict count(char* content){
		vec_str_count result=_search.count(content);
		dict k_c;
		for(vec_str_count::iterator i=result.begin();i!=result.end();++i)
			k_c.setdefault(i->first,i->second);
		return k_c;
	}
	
};
BOOST_PYTHON_MODULE(multi_pattern_search){

   class_<SearchPy>("MultiPatternSearch", init<>())
         .def("add_keyword", &SearchPy::add_keyword)
         .def("count", &SearchPy::count)
         .def("exist", &SearchPy::exist)
		 .def("clear", &SearchPy::clear)
	;

}
