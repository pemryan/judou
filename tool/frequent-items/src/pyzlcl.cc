#include "lossycount.h"
#include <boost/python.hpp>
#include <boost/python/list.hpp>
#include <boost/python/tuple.hpp>
#include <iostream>
#include <string>
#include <vector>
/*
extern LCL_type * LCL_Init(float fPhi);
extern void LCL_Destroy(LCL_type *);
extern void LCL_Update(LCL_type *, LCLitem_t, int);
extern unsigned LCL_Size(LCL_type *);
extern int LCL_PointEst(LCL_type *, LCLitem_t);
extern int LCL_PointErr(LCL_type *, LCLitem_t);
extern std::map<uint32_t, uint32_t> LCL_Output(LCL_type *,int);
*/
namespace { 
using namespace boost::python;
/*
vector<string> word_vec(char* c,unsigned win_width){
    vector<string> str;
    unsigned pos=0;
    unsigned pre_pos=0;
    unsigned window_length=0;
    while(c[pos++]){
        str.push_back(string(pre_pos,pos));  
    }
    return str;
} 
*/
class Lcl{
    LCL_type* _lcl;
    public:
        Lcl(float phi):
            _lcl(LCL_Init(phi))
        {
        }
        
        void destroy(){
            LCL_Destroy(_lcl);
        }
        
        void update(LCLitem_t item,int value=1){
            LCL_Update(_lcl,item,value);
        }

        unsigned capacity(){
            return LCL_Size(_lcl); 
        }
        
        LCLweight_t est(LCLitem_t k){
            return LCL_PointEst(_lcl,k);
        }        
        LCLweight_t err(LCLitem_t k){
            return LCL_PointErr(_lcl,k);
        } 

        list output(LCLweight_t thresh){
            list res;

            for (int i=1;i<=_lcl->size;++i)
            {
                LCLCounter& counters = _lcl->counters[i];
                if (counters.count>=thresh)
                    res.append(
                        make_tuple(counters.item, counters.count)
                    );
            }

            return res;
        }

};

BOOST_PYTHON_MODULE(pyzlcl)
{
    class_<Lcl>("Lcl",init<float>())
        .def("update",&Lcl::update)
        .def("err",&Lcl::err)
        .def("output",&Lcl::output)
        .def("est",&Lcl::est)
        .def("__del__",&Lcl::destroy)
        .def("capacity",&Lcl::capacity);


}
}
