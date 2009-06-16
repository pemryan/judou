#ifndef GK2_h
#define GK2_h

#include "prng.h"

class GK2
{
public:
	GK2(double e);

	void insert(uint32_t v);
	void output(double phi);
	std::map<uint32_t, uint32_t> getHH(uint32_t thresh);
	size_t size();

private:
	class Tuple
	{
	public:
		Tuple(uint32_t v, int g, int d) : val(v), gap(g), delta(d) {}

		uint32_t val;
		int gap;		/* rmin(vi) - rmin(v_{i-1}) */
		int delta;		/* rmax(vi) - rmin(vi) */
	};

	int band(std::list<Tuple>::iterator it);
	void compress();

	double eps;			/* error constraint */
	int n;				/* number of elements */
	int k;
	std::list<Tuple> t;
};

#endif