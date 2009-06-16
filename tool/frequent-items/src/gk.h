#ifndef GK_h
#define GK_h

#include "prng.h"

class GK
{
public:
	GK(double e);
	~GK();

	void insert(double v);
	void output(double phi);
	std::map<uint32_t, uint32_t> getHH(uint32_t thresh);
	size_t size();

private:
	int band(int i);
	void erase(int j);
	void compress();

	class Tuple
	{
	public:
		double val;		/* value of elt */
		int gap;		/* rmin(vi) - rmin(v_{i-1}) */
		int delta;		/* rmax(vi) - rmin(vi) */
	};

	double eps;			/* error constraint */
	int M;				/* memory size */
	int n;				/* number of elements */
	int k;
	Tuple* t;
};

#endif