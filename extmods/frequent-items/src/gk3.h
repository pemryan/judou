#ifndef GK3_h
#define GK3_h

#include "prng.h"

class GK3
{
public:
	GK3(double e);
	~GK3();

	void insert(uint32_t v);
	std::map<uint32_t, uint32_t> getHH(uint32_t thresh);
	size_t size();

private:
	int band(int i);
	void erase(int j);
	void compress();
	void flush();

	class Tuple
	{
	public:
		uint32_t val;   /* value of elt */
		int gap;		/* rmin(vi) - rmin(v_{i-1}) */
		int delta;		/* rmax(vi) - rmin(vi) */
	};

	double eps;			/* error constraint */
	int M;				/* memory size */
	int n;				/* number of elements */
	int k;
	Tuple* t;
	std::vector<uint32_t> buf;
};

#endif