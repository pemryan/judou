#ifndef GK4_h
#define GK4_h

#include "prng.h"

template <class T> class Tuple
{
public:
	// constructors
	Tuple() { val = 0; gap = 0; delta = 0; }
	Tuple(const T& v, const int& g, const int& d) { val = v; gap = g; delta = d; }
	Tuple(const Tuple &t) { val = t.val; gap = t.gap; delta = t.delta; }
	
	void addGap(int g) { gap += g; }
	void setDelta(int d) { delta = d; }

	// return values
	T getVal() const { return val; }
	int getGap() const { return gap; }
	int getDelta() const { return delta; }
	int getSpread() const { return gap+delta-1; }

private:
	T val;
	int gap;
	int delta;
};

template <class T> class TupleComparator
{
public:
	bool operator() (Tuple<T> *t1, Tuple<T> *t2) const
	{
		return (t1->getVal() < t2->getVal());
	}
};

/************************************************************************/
/* Quantile Summary Class						*/
/************************************************************************/
template <class T> class GK4
{
public:
	GK4(double);

	size_t size() const;

	void insert(const T &);
	Tuple<T> *output(double phi);
	std::map<uint32_t, uint32_t> getHH(uint32_t thresh);

private:
	void flush();
	void compress();

	double eps;			// error constant
	int k;
	int M;				// space usage
	int n;				// #stream items
	int bcurrent;		// current bucket
	int rmin;			// current bound on rank
	typename std::list<Tuple<T> *>::iterator compCursor;
	std::list<Tuple<T> *> buf;		// buffer of incoming values
	std::list<Tuple<T> *> t;			// linked list of tuples
};

template <class T> GK4<T>::GK4(double e)
{
	eps = e;
	k = (int) ceil(1./(2.*eps));
	n = M = bcurrent = 0;
	compCursor = t.end();
}

template <class T> void GK4<T>::insert(const T &v)
{
	Tuple<T> *newtup = new Tuple<T>(v, 1, -1);
	buf.push_back(newtup);
	++bcurrent;

	if ((bcurrent % k) == 0) flush();
	compress();
}

template <class T> void GK4<T>::flush()
{
	typename std::list<Tuple<T> *>::reverse_iterator pos, next;

	M += buf.size(); n += buf.size();
	buf.sort(TupleComparator<T>());
	t.merge(buf, TupleComparator<T>());

	// adjust delta-values
	for (pos=t.rbegin(); pos != t.rend(); ++pos)
	{
		if ((*pos)->getDelta() == -1)
		{
			if (
				(compCursor != t.end()) &&
				((*pos)->getVal() <= (*compCursor)->getVal())
			) ++rmin;

			if ((pos == t.rbegin()) || (pos == --t.rend()))
				(*pos)->setDelta(0);
			else
			{
				next = pos; --next;
				(*pos)->setDelta((*next)->getSpread());
			}
		}
	}
}

template <class T> void GK4<T>::compress()
{
	typename std::list<Tuple<T> *>::iterator pos;
	double threshold, tstval;
	int rmax, segsize;
	int i;

	if (M < 3) return;
	if (compCursor == t.end())
	{
		--compCursor; --compCursor;
		rmin=n-1-(*compCursor)->getGap();
		--compCursor;
		//cout << "Starting compress from " << **compCursor << endl;
	}
	segsize = (int) ceil(eps*(double)M);
	for (i=0; (i < segsize) && (compCursor != t.begin()); ++i)
	{
		pos=compCursor; ++pos;
		rmax = rmin + (*compCursor)->getDelta();
		rmin -= (*compCursor)->getGap();
		//cout << "n=" << n << " rmax=" << rmax << " lmax=" << lmax << " eps=" << eps << endl;

		//cout << "Testing " << **compCursor << endl;
		threshold = eps * n;
		tstval = (*compCursor)->getGap() + (*pos)->getSpread();
		//cout << "tstval = " << tstval << ", threshold = " << threshold << endl;
		if (tstval <= threshold)
		{
			//cout << "Deleting " << **compCursor << endl;
			(*pos)->addGap((*compCursor)->getGap());
			pos=compCursor; --pos;
			t.erase(compCursor);
			compCursor=pos;
			--M;
		}
		else
			--compCursor;
	}
	if (compCursor == t.begin()) compCursor=t.end();
}

template <class T> Tuple<T> *GK4<T>::output(double phi)
{
	typename std::list<Tuple<T> *>::const_iterator pos;
	int r = (int)(phi*((double)n));
	int rmin=0, rmax;
	int threshold;
	double l;
	int i;

	if (M == 0) {
		buf.sort(TupleComparator<T>());
		pos=buf.begin();
		for (i=0; i < buf.size()/2; ++i) ++pos;
		return *pos;
	}

	for (pos=t.begin(); pos != t.end(); ++pos) {
		rmin += (*pos)->getGap();
		rmax = rmin + (*pos)->getDelta();
		threshold = (int) ceil((eps * n)/2.0);
		if (((r-rmin) <= threshold) && ((rmax-r) <= threshold)) break;
	}
	return *pos;
}

template <class T> std::map<uint32_t, uint32_t> GK4<T>::getHH(uint32_t thresh)
{
	flush();
	compress();

	std::map<uint32_t, uint32_t> res;
	typename std::list<Tuple<T> *>::const_iterator pos;

	for (pos=t.begin(); pos != t.end(); ++pos)
	{
		std::pair<std::map<uint32_t, uint32_t>::iterator, bool> p =
			res.insert(std::pair<uint32_t, uint32_t>((*pos)->getVal(), (*pos)->getGap()));

		if (p.second == false) p.first->second += (*pos)->getGap();
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

template <class T> size_t GK4<T>::size() const
{
	return 2 * M * sizeof(int) + M * sizeof(T) + 4 * sizeof(int);
}

#endif

