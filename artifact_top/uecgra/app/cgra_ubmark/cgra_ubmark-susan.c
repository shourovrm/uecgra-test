//========================================================================
// cgra_ubmark-susan.c
//========================================================================

#include "common.h"
#include "cgra_ubmark-susan.dat"

//------------------------------------------------------------------------
// susan
//------------------------------------------------------------------------

__attribute__ ((noinline))
int susan( int *ip, int *dpt, int *cp )
{
  int bright, total = 0;
  int tmp, area = 0;

  for( int i = 0; i < niters; i++ ) {
    bright = total + *ip++;
    tmp = *dpt++ * *(cp-bright);
    area += tmp;
    total += tmp * bright;
  }
  return total;
}

//------------------------------------------------------------------------
// verify_results
//------------------------------------------------------------------------

void verify_results( int total, int ref_total )
{
  if(total != ref_total)
    test_fail( 0, total, ref_total );

  test_pass();
}

//------------------------------------------------------------------------
// main
//------------------------------------------------------------------------

int main( int argc, char* argv[] )
{
  int total;
  int *ip  = (int*) ip_array;
  int *dpt = (int*) dpt_array;
  int *cp  = (int*) &(cp_array[NITERS]);

  test_stats_on();
  total = susan( ip, dpt, cp );
  test_stats_off();

  verify_results( total, ref_total );

  return 0;
}
