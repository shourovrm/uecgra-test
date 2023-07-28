//========================================================================
// cgra_ubmark-fft.c
//========================================================================

#include "common.h"
#include "cgra_ubmark-fft.dat"

//------------------------------------------------------------------------
// fft_inner
//------------------------------------------------------------------------
// The inner most loop of FFT

__attribute__ ((noinline))
void fft_inner( int j, int G, int data_real[], int data_imag[],
                int Wr, int Wi )
{
  int k, temp_real, temp_imag;

  for ( k = 0; k < G; k++ ) {
    temp_real = Wr * data_real[ 2*j*G + G + k ] - 
                Wi * data_imag[ 2*j*G + G + k ];
    temp_imag = Wi * data_real[ 2*j*G + G + k ] + 
                Wr * data_imag[ 2*j*G + G + k ];
    data_real[ 2*j*G + G + k ] = 
                data_real[ 2*j*G + k ] - temp_real;
    data_real[ 2*j*G + k ] += temp_real;
    data_imag[ 2*j*G + G + k ] = 
                data_real[ 2*j*G + k ] - temp_imag;
    data_imag[ 2*j*G + k ] += temp_imag;
  }
}

//------------------------------------------------------------------------
// verify_results
//------------------------------------------------------------------------

void verify_results( int data_real[], int ref_data_real[],
                     int data_imag[], int ref_data_imag[] )
{
  wprint(L"Verifying data_real...\n");
  for (int i = 0; i < NPOINTS; i++)
    if ( data_real[i] != ref_data_real[i] )
      test_fail( i, data_real[i], ref_data_real[i] );

  wprint(L"Verifying data_imag...\n");
  for (int i = 0; i < NPOINTS; i++)
    if ( data_imag[i] != ref_data_imag[i] )
      test_fail( i, data_imag[i], ref_data_imag[i] );

  wprint(L"  [ passed ]");
  test_pass();
}

//------------------------------------------------------------------------
// main
//------------------------------------------------------------------------

int main( int argc, char* argv[] )
{
  test_stats_on();
  fft_inner( 0, buttersPerGroup, data_real, data_imag, Wr, Wi );
  test_stats_off();

  verify_results( data_real, ref_data_real, data_imag, ref_data_imag );

  return 0;
}
