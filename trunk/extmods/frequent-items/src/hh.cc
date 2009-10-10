
/********************************************************************
Approximate frequent items in a data stream
G. Cormode 2002, 2003,2005

Last modified: 2005-08
*********************************************************************/

//#define PCAP
// you need to include libraries wpcap.lib ws2_32.lib to compile using PCAP.

#include "prng.h"
#include "cgt.h"
#include "lossycount.h"
#include "frequent.h"
#include "qdigest.h"
#include "ccfc.h"
#include "countmin.h"
#include "gk4.h"

#ifdef __GNUC__
#include <sys/time.h>
#include <time.h>
#endif

/******************************************************************/

#ifdef PCAP
#include <pcap.h>

#ifdef __GNUC__
#include <arpa/inet.h>
#endif

typedef struct ip_address{
    u_char byte1;
    u_char byte2;
    u_char byte3;
    u_char byte4;
}ip_address;

/* IPv4 header */
typedef struct ip_header{
    u_char  ver_ihl;        // Version (4 bits) + Internet header length (4 bits)
    u_char  tos;            // Type of service 
    u_short tlen;           // Total length 
    u_short identification; // Identification
    u_short flags_fo;       // Flags (3 bits) + Fragment offset (13 bits)
    u_char  ttl;            // Time to live
    u_char  proto;          // Protocol
    u_short crc;            // Header checksum
    ip_address  saddr;      // Source address
    ip_address  daddr;      // Destination address
    u_int   op_pad;         // Option + Padding
}ip_header;

/* UDP header*/
typedef struct udp_header{
    u_short sport;          // Source port
    u_short dport;          // Destination port
    u_short len;            // Datagram length
    u_short crc;            // Checksum
}udp_header;

typedef struct tcp_header{
	u_short sport;
	u_short dport;
}tcp_header;
#else
#ifdef _MSC_VER
#include <windows.h>
#endif
#endif

class Stats
{
public:
	Stats() : dU(0.0), dQ(0.0), dP(0.0), dR(0.0), dF(0.0), dF2(0.0) {}

	double dU, dQ;
	double dP, dR, dF, dF2;
	std::multiset<double> P, R, F, F2;
};

void usage()
{
	std::cerr
		<< "Usage: graham\n"
		<< "  -np   number of packets\n"
		<< "  -r    number of runs\n"
		<< "  -phi  phi\n"
		<< "  -d    depth\n"
		<< "  -g    granularity\n"
#ifdef PCAP
		<< "  -pf   pcap file name\n"
		<< "  -f    pcap filter\n"
#else
		<< "  -z    skew\n"
#endif
		<< std::endl;
}

void StartTheClock(uint64_t& s)
{
#ifdef _MSC_VER
	FILETIME ft;
    LARGE_INTEGER li;

	GetSystemTimeAsFileTime(&ft);
	li.LowPart = ft.dwLowDateTime;
	li.HighPart = ft.dwHighDateTime;
	s = (uint64_t) (li.QuadPart / 10000);
#else
	struct timeval tv;
	gettimeofday(&tv, 0);
	s = (1000 * tv.tv_sec) + (tv.tv_usec / 1000);
#endif
}

// returns milliseconds.
uint64_t StopTheClock(uint64_t s)
{
#ifdef _MSC_VER
    FILETIME ft;
    LARGE_INTEGER li;
    uint64_t t;

	GetSystemTimeAsFileTime(&ft);
	li.LowPart = ft.dwLowDateTime;
	li.HighPart = ft.dwHighDateTime;
	t = (uint64_t) (li.QuadPart / 10000);
	return t - s;
#else
	struct timeval tv;
	gettimeofday(&tv, 0);
	return (1000 * tv.tv_sec) + (tv.tv_usec / 1000) - s;
#endif
}

void CheckOutput(std::map<uint32_t, uint32_t>& res, uint32_t thresh, size_t hh, Stats& S, const std::vector<uint32_t>& exact)
{
	if (res.empty())
	{
		S.F.insert(0.0);
		S.F2.insert(0.0);
		S.P.insert(100.0);
		S.dP += 100.0;

		if (hh == 0)
		{
			S.R.insert(100.0);
			S.dR += 100.0;
		}
		else
			S.R.insert(0.0);

		return;
	}

	size_t correct = 0;
	size_t claimed = res.size();
	size_t falsepositives = 0;
	double e = 0.0, e2 = 0.0;

	std::map<uint32_t, uint32_t>::iterator it;
	for (it = res.begin(); it != res.end(); ++it)
	{
		if (exact[it->first] >= thresh)
		{
			++correct;
			uint32_t ex = exact[it->first];
			double diff = (ex > it->second) ? ex - it->second : it->second - ex;
			e += diff / ex;
		}
		else
		{
			++falsepositives;
			uint32_t ex = exact[it->first];
			double diff = (ex > it->second) ? ex - it->second : it->second - ex;
			e2 += diff / ex;
		}
	}

	if (correct != 0)
	{
		e /= correct;
		S.F.insert(e);
		S.dF += e;
	}
	else
		S.F.insert(0.0);

	if (falsepositives != 0)
	{
		e2 /= falsepositives;
		S.F2.insert(e2);
		S.dF2 += e2;
	}
	else
		S.F2.insert(0.0);

	double r = 100.0;
	if (hh != 0) r = 100.0 *((double) correct) / ((double) hh);

	double p = 100.0 *((double) correct) / ((double) claimed);

	S.R.insert(r);
	S.dR += r;
	S.P.insert(p);
	S.dP += p;
}

void PrintOutput(char* title, size_t size, const Stats& S, size_t u32NumberOfPackets)
{
	double p5th = -1.0, p95th = -1.0, r5th = -1.0, r95th = -1.0, f5th = -1.0, f95th = -1.0, f25th = -1.0, f295th = -1.0;
	size_t i5, i95;
	std::multiset<double>::const_iterator it;

	if (! S.P.empty())
	{
		it = S.P.begin();
		i5 = S.P.size() * 0.05;
		for (size_t i = 0; i < i5; ++i) ++it;
		p5th = *it;
		i95 = S.P.size() * 0.95;
		for (size_t i = 0; i < (i95 - i5); ++i) ++it;
		p95th = *it;
	}

	if (! S.R.empty())
	{
		it = S.R.begin();
		i5 = S.R.size() * 0.05;
		for (size_t i = 0; i < i5; ++i) ++it;
		r5th = *it;
		i95 = S.R.size() * 0.95;
		for (size_t i = 0; i < (i95 - i5); ++i) ++it;
		r95th = *it;
	}

	if (! S.F.empty())
	{
		it = S.F.begin();
		i5 = S.F.size() * 0.05;
		for (size_t i = 0; i < i5; ++i) ++it;
		f5th = *it;
		i95 = S.F.size() * 0.95;
		for (size_t i = 0; i < (i95 - i5); ++i) ++it;
		f95th = *it;
	}

	if (! S.F2.empty())
	{
		it = S.F2.begin();
		i5 = S.F2.size() * 0.05;
		for (size_t i = 0; i < i5; ++i) ++it;
		f25th = *it;
		i95 = S.F2.size() * 0.95;
		for (size_t i = 0; i < (i95 - i5); ++i) ++it;
		f295th = *it;
	}

	printf("%s\t%1.2f\t\t%d\t\t%1.2f\t%1.2f\t%1.2f\t%1.2f\t%1.2f\t%1.2f\t%1.2f\t%1.2f\t%1.2f\t%1.2f\t%1.2f\t%1.2f\n",
		title, u32NumberOfPackets / S.dU, size,
		S.dR / S.R.size(), r5th, r95th,
		S.dP / S.P.size(), p5th, p95th,
		S.dF / S.F.size(), f5th, f95th,
		S.dF2 / S.F2.size(), f25th, f295th
	);
}

size_t RunExact(uint32_t thresh, std::vector<uint32_t>& exact)
{
	size_t hh = 0;

	for (size_t i = 0; i < exact.size(); ++i)
		if (exact[i] >= thresh) ++hh;

	return hh;
}

/******************************************************************/

int main(int argc, char **argv) 
{
	size_t stNumberOfPackets = 10000000;
	size_t stRuns = 20;
	double dPhi = 0.001;
	uint32_t u32Depth = 4;
	uint32_t u32Granularity = 8;
#ifdef PCAP
	std::string sFilter = "ip and (tcp or udp)";
	std::string sPcapFile = "header_gs10";
#else
	double dSkew = 1.0;
#endif

	for (int i = 1; i < argc; ++i)
	{
		if (strcmp(argv[i], "-np") == 0)
		{
			i++;
			if (i >= argc)
			{
				std::cerr << "Missing number of packets." << std::endl;
				return -1;
			}
			stNumberOfPackets = atoi(argv[i]);
		}
		else if (strcmp(argv[i], "-r") == 0)
		{
			i++;
			if (i >= argc)
			{
				std::cerr << "Missing number of runs." << std::endl;
				return -1;
			}
			stRuns = atoi(argv[i]);
		}
		else if (strcmp(argv[i], "-d") == 0)
		{
			i++;
			if (i >= argc)
			{
				std::cerr << "Missing depth." << std::endl;
				return -1;
			}
			u32Depth = atoi(argv[i]);
		}
		else if (strcmp(argv[i], "-g") == 0)
		{
			i++;
			if (i >= argc)
			{
				std::cerr << "Missing granularity." << std::endl;
				return -1;
			}
			u32Granularity = atoi(argv[i]);
		}
		else if (strcmp(argv[i], "-phi") == 0)
		{
			i++;
			if (i >= argc)
			{
				std::cerr << "Missing phi." << std::endl;
				return -1;
			}
			dPhi = atof(argv[i]);
		}
#ifdef PCAP
		else if (strcmp(argv[i], "-pf") == 0)
		{
			i++;
			if (i >= argc)
			{
				std::cerr << "Missing pcap file name." << std::endl;
				return -1;
			}
			sPcapFile = std::string(argv[i]);
		}
		else if (strcmp(argv[i], "-f") == 0)
		{
			i++;
			if (i >= argc)
			{
				std::cerr << "Missing pcap filter." << std::endl;
				return -1;
			}
			sFilter = std::string(argv[i]);
		}
#else
		else if (strcmp(argv[i], "-z") == 0)
		{
			i++;
			if (i >= argc)
			{
				std::cerr << "Missing skew parameter." << std::endl;
				return -1;
			}
			dSkew = atof(argv[i]);
		}
#endif
		else
		{
			usage();
			return -1;
		}
	}

	uint32_t u32Width = 2.0 / dPhi;

	prng_type * prng;
	prng=prng_Init(44545,2);
	int64_t a = (int64_t) (prng_int(prng)% MOD);
	int64_t b = (int64_t) (prng_int(prng)% MOD);
	prng_Destroy(prng);

	uint32_t u32DomainSize = 1048575;
	std::vector<uint32_t> exact(u32DomainSize + 1, 0);
#ifdef PCAP
	//Open the capture file
	pcap_t *fp;
	char errbuf[PCAP_ERRBUF_SIZE];
	if ((fp = pcap_open_offline(sPcapFile.c_str(), errbuf)) == 0)
	{
		std::cerr << "Unable to open file." << std::endl;
		exit(1);
	}

    //compile the filter
	struct bpf_program fcode;
	if (pcap_compile(fp, &fcode, const_cast<char*>(sFilter.c_str()), 1, 0xffffff) < 0 )
    {
		std::cerr << "Unable to compile the packet filter. Check the syntax" << std::endl;
        exit(1);
    }

    //set the filter
    if (pcap_setfilter(fp, &fcode) < 0)
    {
		std::cerr << "Error setting the filter" << std::endl;
        exit(1);
    }

	struct pcap_pkthdr *header;
	const u_char *pkt_data;
	int res;
#endif
	Stats SFreq, SQD, SCGT, SLC, SLCD, SLCL, SLCU, SCMH, SCCFC, SGK4;

	QD_type* qd = QD_Init(dPhi * 0.8,20,-1);
	GK4<uint32_t> gk4(dPhi);
	CMH_type* cmh = CMH_Init(u32Width, u32Depth, 32, u32Granularity);
	CGT_type* cgt = CGT_Init(u32Width, u32Depth, 32, u32Granularity);
	CCFC_type* ccfc = CCFC_Init(u32Width, u32Depth, 32, u32Granularity);
	LC_type* lc = LC_Init(dPhi);
	LCD_type* lcd = LCD_Init(dPhi);
	LCL_type* lcl = LCL_Init(dPhi);
	LCU_type* lcu = LCU_Init(dPhi);
	freq_type* freq = Freq_Init(dPhi);

	std::vector<uint32_t> data;
#ifndef PCAP
	Tools::Random r = Tools::Random(0xF4A54B);
	Tools::PRGZipf zipf = Tools::PRGZipf(0, u32DomainSize, dSkew, &r);
#endif

	size_t stCount = 0;
#ifdef PCAP
	while((res = pcap_next_ex( fp, &header, &pkt_data)) >= 0 && stCount < stNumberOfPackets)
#else
	for (int i = 0; i < stNumberOfPackets; ++i)
#endif
	{
		++stCount;
		if (stCount % 500000 == 0)
			std::cerr << stCount << std::endl;
#ifdef PCAP
		ip_header *ih;
		udp_header *uh;
		tcp_header *th;
		u_int ip_len;
		u_short sport,dport;

	    //retireve the position of the ip header
		ih = (ip_header *) (pkt_data + 14); //length of ethernet header
		ip_len = (ih->ver_ihl & 0xf) * 4;

		if (ih->proto == 6)
		{
			th = (tcp_header *) ((u_char*)ih + ip_len);
		    sport = ntohs( th->sport );
			dport = ntohs( th->dport );
		}
		else if (ih->proto == 17)
		{
			uh = (udp_header *) ((u_char*)ih + ip_len);
		    sport = ntohs( uh->sport );
			dport = ntohs( uh->dport );
		}

		uint32_t v;
		memcpy(&v, &(ih->daddr), 4);
#else
		uint32_t v = zipf.nextLong();
#endif

		uint32_t value = hash31(a, b, v) & u32DomainSize;
		data.push_back(value);
	}

	size_t stRunSize = data.size() / stRuns;
	size_t stStreamPos = 0;
	uint64_t nsecs;

	for (size_t run = 1; run <= stRuns; ++run)
	{
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			exact[data[i]]++;
		}

		StartTheClock(nsecs);
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			Freq_Update(freq, data[i]);
		}
		SFreq.dU += StopTheClock(nsecs);

		StartTheClock(nsecs);
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			QD_Insert(qd, data[i], 1);
		}
		SQD.dU += StopTheClock(nsecs);

		StartTheClock(nsecs);
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			if (data[i]>0)
				CMH_Update(cmh,data[i],1);      
			else
				CMH_Update(cmh,-data[i],-1);
		}
		SCMH.dU += StopTheClock(nsecs);

		StartTheClock(nsecs);
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			if (data[i]>0)
			  CGT_Update(cgt,data[i],1);      
			else
			CGT_Update(cgt,-data[i],-1);
		}
		SCGT.dU += StopTheClock(nsecs);

		StartTheClock(nsecs);
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			LC_Update(lc,data[i]);
		}
		SLC.dU += StopTheClock(nsecs);

		StartTheClock(nsecs);
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			LCD_Update(lcd,data[i]);
		}
		SLCD.dU += StopTheClock(nsecs);

		StartTheClock(nsecs);
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			LCL_Update(lcl,data[i],1);
		}
		SLCL.dU += StopTheClock(nsecs);

		StartTheClock(nsecs);
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			LCU_Update(lcu, data[i]);
		}
		SLCU.dU += StopTheClock(nsecs);

		StartTheClock(nsecs);
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			if (data[i]>0)
				CCFC_Update(ccfc,data[i],1);      
			else
				CCFC_Update(ccfc,-data[i],-1);
		}
		SCCFC.dU += StopTheClock(nsecs);

		StartTheClock(nsecs);
		for (size_t i = stStreamPos; i < stStreamPos + stRunSize; ++i)
		{
			gk4.insert(data[i]);
		}
		SGK4.dU += StopTheClock(nsecs);

		uint32_t thresh = static_cast<uint32_t>(floor(dPhi * run * stRunSize));
		if (thresh == 0) thresh = 1;
		size_t hh = RunExact(thresh, exact);
		std::cerr << "Run: " << run << ", Exact: " << hh << std::endl;

		std::map<uint32_t, uint32_t> res;

		StartTheClock(nsecs);
		res = Freq_Output(freq,thresh);
		SFreq.dQ += StopTheClock(nsecs);
		CheckOutput(res, thresh, hh, SFreq, exact);

		StartTheClock(nsecs);
		QD_Compress(qd);
		SQD.dU += StopTheClock(nsecs);
		StartTheClock(nsecs);
		res = QD_FindHH(qd, thresh);
		SQD.dQ += StopTheClock(nsecs);
		CheckOutput(res, thresh, hh, SQD, exact);

		StartTheClock(nsecs);
		res = CMH_FindHH(cmh,thresh);
		SCMH.dQ += StopTheClock(nsecs);
		CheckOutput(res, thresh, hh, SCMH, exact);

		StartTheClock(nsecs);
		res = CGT_Output(cgt,thresh);
		SCGT.dQ+= StopTheClock(nsecs);
		CheckOutput(res, thresh, hh, SCGT, exact);

		StartTheClock(nsecs);
		res = LC_Output(lc,thresh);
		SLC.dQ += StopTheClock(nsecs);
		CheckOutput(res, thresh, hh, SLC, exact);
		  
		StartTheClock(nsecs);
		res = LCD_Output(lcd,thresh);
		SLCD.dQ += StopTheClock(nsecs);
		CheckOutput(res, thresh, hh, SLCD, exact);
		  
		StartTheClock(nsecs);
		res = LCL_Output(lcl,thresh);
		SLCL.dQ += StopTheClock(nsecs);
		CheckOutput(res, thresh, hh, SLCL, exact);

		StartTheClock(nsecs);
		res = LCU_Output(lcu,thresh);
		SLCU.dQ += StopTheClock(nsecs);
		CheckOutput(res, thresh, hh, SLCU, exact);

		StartTheClock(nsecs);
		res = CCFC_Output(ccfc,thresh);
		SCCFC.dQ += StopTheClock(nsecs);
		CheckOutput(res, thresh, hh, SCCFC, exact);

		StartTheClock(nsecs);
		res = gk4.getHH(thresh);
		SGK4.dQ += StopTheClock(nsecs);
		CheckOutput(res, thresh, hh, SGK4, exact);

		stStreamPos += stRunSize;
	}

	printf("\nMethod\tUpdates/ms\tSpace\t\tRecall\t5th\t95th\tPrecis\t5th\t95th\tFreq RE\t5th\t95th\n");

	PrintOutput("Freq", Freq_Size(freq), SFreq, stNumberOfPackets);
	PrintOutput("CMH", CMH_Size(cmh), SCMH, stNumberOfPackets);
	PrintOutput("CGT", CGT_Size(cgt), SCGT, stNumberOfPackets);
	PrintOutput("CCFC", CCFC_Size(ccfc), SCCFC, stNumberOfPackets);
	PrintOutput("LC", LC_Size(lc), SLC, stNumberOfPackets);
	PrintOutput("LCD", LCD_Size(lcd), SLCD, stNumberOfPackets);
	PrintOutput("SSH", LCL_Size(lcl), SLCL, stNumberOfPackets);
		// Yes, this is correct. L is for "lazy".
	PrintOutput("SSL", LCU_Size(lcu), SLCU, stNumberOfPackets);
		// Yes, this is correct, U here stands for "unary"
	PrintOutput("QD", QD_Size(qd), SQD, stNumberOfPackets);
	PrintOutput("GK4", gk4.size(), SGK4, stNumberOfPackets);

	CMH_Destroy(cmh);
	CGT_Destroy(cgt);
	LC_Destroy(lc);
	LCD_Destroy(lcd);
	LCL_Destroy(lcl);  
	LCU_Destroy(lcu);
	CCFC_Destroy(ccfc);

	printf("\n");

	return 0;
}
