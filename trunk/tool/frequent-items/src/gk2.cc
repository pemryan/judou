#include "gk2.h"

GK2::GK2(double e) : eps(e), n(0), k((int) ceil(1.0 / (2.0 * eps)))
{
}

void GK2::insert(uint32_t v)
{
	++n;
	if ((n > 0) && ((n % k) == 0))
	{
		compress();
	}

	std::list<Tuple>::iterator it = t.begin();

	while ((it != t.end()) && (v >= it->val)) ++it;

	if (it != t.end())
	{
		Tuple tuple(v, 1, it->gap + it->delta - 1);
		if (it == t.begin()) tuple.delta = 0;
		t.insert(it, tuple);
	}
	else
	{
		Tuple tuple(v, 1, 0);
		t.push_back(tuple);
	}
}

void GK2::compress()
{
	int gstar;
	double threshold = 2.0 * eps * (double) n;
	double tstval;
	int i,j,k;

	std::list<Tuple>::iterator it, it2, it3, it4;

	for (i = t.size() - 2; i > 0; --i)
	{
		it = t.begin();
		for (j = 0; j < i; ++j) ++it;

		/* let gstar = sum of g-values in ti and descendants */
		gstar=it->gap;
		j=i-1;
		it2 = it; --it2;

		while ((j > 0) && (band(it2) < band(it)))
		{
			gstar += it2->gap;
			--j;
			--it2;
		}

		it3 = it; ++it3;
		tstval = gstar + it3->gap + it3->delta - 1.;
		if ((band(it) <= band(it3)) && (tstval <= threshold))
		{
			/* delete descendants of ti and ti itself */
			//if (j > 0)
			{
				//fprintf(stdout,"Deleting %d elts.\n",i-j);

				if (i < t.size() - 2)
				{
					it3 = it2; ++it3;
					for (k=j+1; k <= i; k++)
					{
						it4 = it3; ++it4;
						it4->gap += it3->gap;
						it4 = it3; ++it3;
						t.erase(it4);
					}
				}
				else
				{
					it3 = it2; ++it3;
					for (k=j+1; k < i; k++)
					{
						it4 = it3; ++it4;
						it4->gap += it3->gap;
						it4 = it3; ++it3;
						t.erase(it4);
					}
				}
				i=j+1;
			}
		}
	}
}

int GK2::band(std::list<Tuple>::iterator it)
{
	int alpha;
	int p = (int) floor(2.0 * eps * (double) n);
	int lbound;
	int ubound;
	int threshold;
	double x;

	x = log(2.0 * eps * (double) n)/log(2.0);
	threshold = (int) ceil(x);

	if (it->delta == 0) return (threshold + 1);
	if (it->delta == p) return 0;

	for (alpha = 1; alpha <= threshold; ++alpha)
	{
		lbound = p - (1 << alpha) - (p % (1 << alpha));
		ubound = p - (1 << (alpha-1)) - (p % (1 << (alpha-1)));
		if ((lbound < it->delta) && (it->delta <= ubound)) break;
	}
	return alpha;
}

std::map<uint32_t, uint32_t> GK2::getHH(uint32_t thresh)
{
	std::map<uint32_t, uint32_t> res;

	for (std::list<Tuple>::iterator it = t.begin(); it != t.end(); ++it)
	{
		//std::cerr << it->val << " " << it->gap << " " << it->delta << std::endl;

		std::pair<std::map<uint32_t, uint32_t>::iterator, bool> p =
			res.insert(std::pair<uint32_t, uint32_t>(it->val, it->gap));

		if (p.second == false) p.first->second += it->gap;
	}

	std::map<uint32_t, uint32_t>::iterator it = res.begin(), it2;
	while (it != res.end())
	{
		if (it->second  + (eps * n) < thresh)
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

size_t GK2::size()
{
	return 2 * sizeof(uint32_t) + t.size() *  5 * sizeof(uint32_t);
}
