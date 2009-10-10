#ifndef __MULTI_PATTERN_SEARCH_1HF02R9FH1__
#define __MULTI_PATTERN_SEARCH_1HF02R9FH1__

#include <vector>
#include <string>
#include <map>
extern "C" {
#include "acsmx2.h"
}
using namespace std;



struct KeyWord {
    string keyword;
    unsigned count;
    KeyWord(char* k):count(0),keyword(k) {
    }
};



typedef vector<KeyWord> vec_key;
typedef vector<KeyWord*> vec_key_ptr;
typedef vector<pair<string,unsigned> > vec_str_count;


int match_recall(void * id, int index, void *data);
int exist_recall(void * id, int index, void *data);
void acsm_free(ACSM_STRUCT2 * acsm);


class Search {
    vec_key _keywords;// 待查找关键字
    ACSM_STRUCT2* _compiled;// 编译后的关键字
    bool _has_compile;

public:
    Search() {
        _has_compile=false;
        _compiled=0;
    }

    ~Search() {
        acsm_free(_compiled);
    }

    void add_keyword(char* word) {
        _has_compile=false;
        _keywords.push_back(KeyWord(word));
    }
    void clear() {
        _has_compile=false;
        _keywords.clear();
    }
    int scan(char* content,int recall(void * id, int index, void *data),void *data) {
        compile();
        size_t length=strlen(content);
        int state=0;
        return acsmSearch2(
            _compiled,//编译后的关键字
            (unsigned char **) &content,// 内容(返回的时候, 会修改)
            length,                     // 内容的长度
            recall,       // 回调函数int (*Match) (void * id, int index, void *data),
            data,                  // 回调函数的第三个参数
            &state
        );				// 用于保存引擎的状态
    }
    bool exist(char* sub) {
        return bool(scan(
                   sub,
                   exist_recall,
                   &sub
               ));
    }

    vec_str_count count(char* content) {
        vec_key_ptr count;
        scan(content,match_recall,&count);
        vec_str_count result;
        for (vec_key_ptr::iterator i=count.begin();i!=count.end();++i) {
            result.push_back(make_pair((*i)->keyword,(*i)->count));
            (*i)->count=0;
        }
        return result;
    }

private:
    void compile() {
        if (_has_compile)return;

        acsm_free(_compiled);

        _compiled=acsmNew2();
        _compiled->acsmFormat = ACF_SPARSE;
        _compiled->acsmFSA    = FSA_DFA;

        for (vec_key::iterator i=_keywords.begin();i!=_keywords.end();++i) {
            acsmAddPattern2(
                _compiled,
                (unsigned char*)((*i).keyword.c_str()),
                (*i).keyword.length(),
                false ,           // bool not nocase
                0,                // int offset
                0,                // int depth
                static_cast<void *>(&(*i)),	// void * id
                0               // int iid;
            );
        }

        acsmCompile2(_compiled);

        _has_compile=true;
    }
};
#endif //__MULTI_PATTERN_SEARCH_1HF02R9FH1__
