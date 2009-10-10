//frequent.h -- simple frequent items routine
// see Misra&Gries 1982, Demaine et al 2002, Karp et al 2003
// implemented by Graham Cormode, 2002,2003

#ifndef FREQUENT_h
#define FREQUENT_h

#include "prng.h"

typedef struct itemlist ITEMLIST;
typedef struct group GC_GROUP;

struct group 
{
  int diff;
  ITEMLIST *items;
  GC_GROUP *previousg, *nextg;
};

struct itemlist 
{
  int item;
  GC_GROUP *parentg;
  ITEMLIST *previousi, *nexti;
  ITEMLIST *nexting, *previousing;
  
};

typedef struct freq_type{

  ITEMLIST **hashtable;
  GC_GROUP *groups;
  int k;
  int tblsz;
  int64_t a,b;
} freq_type;


extern freq_type * Freq_Init(float);
extern void Freq_Destroy(freq_type *);
extern void Freq_Update(freq_type *, int);
extern int Freq_Size(freq_type *);
extern std::map<uint32_t, uint32_t> Freq_Output(freq_type *,int);

#endif

