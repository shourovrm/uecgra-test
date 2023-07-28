//========================================================================
// cgra_ubmark-latnrm.c
//========================================================================

#include "common.h"
#include "cgra_ubmark-latnrm.dat"

//------------------------------------------------------------------------
// latnrm
//------------------------------------------------------------------------

__attribute__ ((noinline))
void latnrm( int input, int coefficient[], int internal_state[] )
{
  int i;
  int left = 0, right = 0, top = 0, bottom = 0;
  int q_coef, k_coef;

  top = input;
  q_coef = coefficient[0];
  for ( i = 0; i < niters; i++ ) {
    k_coef = coefficient[ 2*i ];
    left = top;
    right = internal_state[i];
    internal_state[i] = bottom;
    top = q_coef * left - k_coef * right;
    bottom = q_coef * right + k_coef * left;
    q_coef = coefficient[ 2*i+1 ];
  }
}

//------------------------------------------------------------------------
// verify_results
//------------------------------------------------------------------------

void verify_results( int in_state[], int ref_in_state[] )
{
  for (int i = 0; i < 2*ORDER; i++)
    if ( in_state[i] != ref_in_state[i] )
      test_fail( i, in_state[i], ref_in_state[i] );

  test_pass();
}

//------------------------------------------------------------------------
// main
//------------------------------------------------------------------------

int main( int argc, char* argv[] )
{
  test_stats_on();
  latnrm( input, coefficient, internal_state );
  test_stats_off();

  verify_results( internal_state, ref_internal_state );

  return 0;
}
