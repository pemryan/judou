#include "gk.h"

GK::GK(double e) : eps(e), M(0), n(0), k((int) ceil(1.0 / (2.0 * eps)))
{
	t = new Tuple[1000000];
}

GK::~GK()
{
	delete[] t;
}

int GK::band(int i)
{
	int alpha;
	int p = (int)floor(2.0 * eps * (double) n);
	int lbound;
	int ubound;
	int threshold;
	double x;

	x = log(2.0 * eps * (double) n)/log(2.0);
	threshold = (int) ceil(x);

	if (t[i].delta == 0) return (threshold + 1);
	if (t[i].delta == p) return 0;

	for (alpha = 1; alpha <= threshold; ++alpha)
	{
		lbound = p - (1 << alpha) - (p % (1 << alpha));
		ubound = p - (1 << (alpha-1)) - (p % (1 << (alpha-1)));
		if ((lbound < t[i].delta) && (t[i].delta <= ubound)) break;
	}
	return alpha;
}

void GK::insert(double v)
{
	int i = 0;
	int j;

	++n;
	if ((n > 0) && ((n % k) == 0))
	{
		compress();
	}

	while ((i < M) && (v >= t[i].val)) ++i;
	/* make room for new tuple */
	if (i < M) {
		for (j = M - 1; j >= i; --j)
		{
			t[j+1].val = t[j].val;
			t[j+1].gap = t[j].gap;
			t[j+1].delta = t[j].delta;
		}
		/* insert new tuple */
		t[i].val = v;
		t[i].gap = 1;
		//t[i].delta = (int)(2.*eps*(double)n);
		t[i].delta = t[i+1].gap + t[i+1].delta - 1;
	}
	/* right boundary case */
	else {
		t[i].val = v;
		t[i].gap = 1;
		t[i].delta = 0;
	}
	/* left boundary case */
	if (i == 0) t[i].delta = 0;
	++M;
}

void GK::erase(int j)
{
	int i;

	t[j].val = t[j+1].val;
	t[j].gap += t[j+1].gap;
	t[j].delta = t[j+1].delta;
/*
	if ((t[j].gap + t[j].delta) > (2.*eps*(double)n))
		fprintf(stderr,"OVERFLOW!\n");
*/
	--M;
	i = j + 1;
	while (i < M)
	{
		t[i].val = t[i+1].val;
		t[i].gap = t[i+1].gap;
		t[i].delta = t[i+1].delta;
		++i;
	}
}

void GK::compress()
{
	int gstar;
	double threshold = 2.0 * eps * (double) n;
	double tstval;
	int i,j,k;

	for (i = M - 2; i > 0; --i)
	{
		/* let gstar = sum of g-values in ti and descendants */
		gstar=t[i].gap; j=i-1;
		while ((j > 0) && (band(j) < band(i)))
		{
			gstar += t[j].gap;
			j--;
		}
		tstval = gstar + t[i+1].gap + t[i+1].delta - 1.;
		if ((band(i) <= band(i+1)) && (tstval <= threshold))
		{
			/* delete descendants of ti and ti itself */
			//if (j > 0)
			{
				//fprintf(stdout,"Deleting %d elts.\n",i-j);

				if (i < M - 2)
				{
					for (k=j+1; k <= i; k++)
						erase(j+1);
				}
				else {
					for (k=j+1; k < i; k++)
						erase(j+1);
				}
				i=j+1;
			}
		}
	}
}

void GK::output(double phi)
{
	int r = phi * ((double) n);    /* phi-quantile */
	int rmin = 0, rmax;
	int i;

	for (i = 0; i < M; ++i)
	{
		rmin += t[i].gap;
		rmax = rmin + t[i].delta;
/*
		if ((rmax - r) > eps*(double)n) break;
*/
		if (
			((r-rmin) <= eps * (double) n) &&
			((rmax-r) <= eps * (double) n)
		) break;
	}
	
	fprintf(stdout, "%.2lf-quantile = %.0lf (i=%d)\n",phi,t[i].val,i);
}

std::map<uint32_t, uint32_t> GK::getHH(uint32_t thresh)
{
	std::map<uint32_t, uint32_t> res;

	for (size_t i = 0; i < M; ++i)
	{
		//std::cerr << t[i].val << " " << t[i].gap << " " << t[i].delta << std::endl;

		std::pair<std::map<uint32_t, uint32_t>::iterator, bool> it =
			res.insert(std::pair<uint32_t, uint32_t>(t[i].val, t[i].gap));

		if (it.second == false) it.first->second += t[i].gap;
	}

	std::map<uint32_t, uint32_t>::iterator it = res.begin(), it2;
	while (it != res.end())
	{
		if (it->second + (eps * n) < thresh)
		{
			it2 = it++;
			res.erase(it2);
		}
		else
		{
			++it;
		}
	}

	return res;
}

size_t GK::size()
{
	return 3 * sizeof(uint32_t) + 3 * M * sizeof(uint32_t);
}
