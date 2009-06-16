#include "prng.h"
#include "lossycount.h"
#include <iostream>

size_t RunExact(uint32_t thresh, std::vector<uint32_t>& exact);

template<class T>
void generate_data(T* data,size_t number,uint32_t u32DomainSize,double dSkew);

int main(int argc, char **argv) {
    size_t stNumberOfPackets = 10000000; // 样本数
    double dPhi = 0.0001; //统计频率大于dPhi的元素,这里取万分之一
    uint32_t u32DomainSize = 1048575; //样本取值范围
    
    std::vector<uint32_t> exact(u32DomainSize + 1, 0);//精确统计,以便于做对比
    
    //生成 Zipf 分布的数据 
    std::vector<uint32_t> data;
    generate_data(&data,stNumberOfPackets,u32DomainSize,1.0);

    //将测试数据分为20段运行 每运行一段 输出一次统计数据
    size_t stRuns = 20;
    size_t stRunSize = data.size() / stRuns;
    size_t stStreamPos = 0;

    LCL_type* lcl = LCL_Init(dPhi);
    for (size_t run = 1; run <= stRuns; ++run) {
        for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i) {
            exact[data[i]]+=1;
        }


        for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i) {
            LCL_Update(lcl,data[i],1);
        }


        uint32_t thresh = static_cast<uint32_t>(floor(dPhi * run * stRunSize));
        if (thresh == 0) thresh = 1;
        
        std::cout<<"Thresh is "<<thresh<<std::endl;
        
        size_t hh = RunExact(thresh, exact);
        std::cout << "Run: " << run << ", Exact: " << hh << std::endl;

        std::map<uint32_t, uint32_t> res;
        
        res = LCL_Output(lcl,thresh);
        std::cout << "LCL: " << run << ", Count: " << res.size() << std::endl;

		stStreamPos += stRunSize;
    }

    LCL_Destroy(lcl);

    printf("\n");

    return 0;
}

size_t RunExact(uint32_t thresh, std::vector<uint32_t>& exact)
{
	size_t hh = 0;

	for (size_t i = 0; i < exact.size(); ++i)
		if (exact[i] >= thresh) ++hh;

	return hh;
}

template<class T>
void generate_data(T* data,size_t number,uint32_t u32DomainSize,double dSkew){
    prng_type * prng;
    prng=prng_Init(44545,2);
    int64_t a = (int64_t) (prng_int(prng)% MOD);
    int64_t b = (int64_t) (prng_int(prng)% MOD);
    prng_Destroy(prng);
	Tools::Random r = Tools::Random(0xF4A54B);
	Tools::PRGZipf zipf = Tools::PRGZipf(0, u32DomainSize, dSkew, &r);
    size_t stCount = 0;
    for (int i = 0; i < number; ++i)
    {
        ++stCount;
        if (stCount % 500000 == 0)
            std::cout <<"Generate Data " << stCount << std::endl;
        uint32_t v = zipf.nextLong();

        uint32_t value = hash31(a, b, v) & u32DomainSize;
        data->push_back(value);
    }

}

