// cgt.h -- header file for Combinatorial Group Testing, Graham Cormode
// 2002,2003

#ifndef CGT_h
#define CGT_h

#include "prng.h"

#define CGTitem_t uint32_t
//#define CGTitem_t int

typedef struct CGT_type{
  int tests;
  int logn;
  int gran;
  int buckets;
  int subbuckets;
  int count;
  int ** counts;
  int *testa, *testb;
  CGTitem_t bitmask,initoff;
} CGT_type;

extern CGT_type * CGT_Init(int, int, int, int);
extern void CGT_Update(CGT_type *, CGTitem_t, int); 
extern std::map<uint32_t, uint32_t> CGT_Output(CGT_type *, int);
extern void CGT_Destroy(CGT_type *);
extern int CGT_Size(CGT_type *);

#endif

