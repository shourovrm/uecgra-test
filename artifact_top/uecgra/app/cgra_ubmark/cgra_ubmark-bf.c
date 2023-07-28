//========================================================================
// cgra_ubmark-bf.c
//========================================================================

#include "common.h"
#include "cgra_ubmark-bf.dat"

//------------------------------------------------------------------------
// latnrm
//------------------------------------------------------------------------

__attribute__ ((noinline))
void bf( unsigned long data[], unsigned long S[], unsigned long P[] )
{
  int i;
  unsigned long l, r, temp;

  l = data[0];
  r = data[1];

  for(i = 0; i < niters; i++) {
    // BF_ENC( r, l, s, p[i] )
    r ^= P[i];
    r ^= ((( S[        (l>>24L)      ] +
             S[0x0100+((l>>16L)&0xff)])^
             S[0x0200+((l>> 8L)&0xff)])+
             S[0x0300+((l     )&0xff)])&0xffffffff;
    temp = r;
    r = l;
    l = temp;
  }

  data[1] = l & 0xFFFFFFFF;
  data[0] = r & 0xFFFFFFFF;
}

//------------------------------------------------------------------------
// verify_results
//------------------------------------------------------------------------

void verify_results( unsigned long data[], unsigned long ref_data[] )
{
  for (int i = 0; i < 2; i++)
    if ( data[i] != ref_data[i] )
      test_fail( i, data[i], ref_data[i] );

  test_pass();
}

//------------------------------------------------------------------------
// main
//------------------------------------------------------------------------

int main( int argc, char* argv[] )
{
  test_stats_on();
  bf( data, S, P );
  test_stats_off();

  verify_results( data, ref_data );

  return 0;
}
