#include <stdio.h>
#include <stdlib.h>
#include "dither-src.dat"

int dither(byte_t dest[], byte_t src[], int error_in[], int error_out[], int len);

int main()
{
  byte_t *dst    = (byte_t*) malloc(sizeof(byte_t)*len);
  int *error_in  = (int*) malloc(sizeof(int)*(len+2));
  int *error_out = (int*) malloc(sizeof(int)*(len+1));

  for(int i = 0; i < len+2; i++)
    error_in[i] = 0;

  int res = dither(&dst[0], &src[0], &error_in[0], &error_out[0], len);

  printf("res = %d\n", res);
  return 0;
}

int dither(byte_t dest[], byte_t src[], int error_in[], int error_out[], int len)
{
  int i = 0;
  int error = 0;
  byte_t dest_pixel = 0x00u;

  for(; i < len; i++) {
    /* dest_pixel = 0x00u; */

    int error_offset
      = ( 1 * error_in[ i ] )
      + ( 3 * error         );

    int out = src[i] + ( error_offset >> 4 );

    // Only process pixel if it is non-white
    /* if(src[i] != 0x00u) { */
    /*   if (out > 127) */
    /*     dest_pixel = 0xffu; */
    /*   error = out - dest_pixel; */
    /* } */
    /* else { */
    /*   dest_pixel = 0x00u; */
    /*   error = 0; */
    /* } */
    /* if((src[i] != 0) && (out > 127)) { */
    /*   dest_pixel = 0xffu; */
    /*   error = out - dest_pixel; */
    /* } else if((src[i] != 0) && (out <= 127)) { */
    /*   dest_pixel = 0; */
    /*   error = out; */
    /* } else { */
    /*   dest_pixel = 0; */
    /*   error = 0; */
    /* } */

    if(out > 127) {
      dest_pixel = 0xffu;
      error = out - dest_pixel;
    } else {
      dest_pixel = 0;
      error = out;
    }

    /* error_out[i+1] = error; */
    dest[i] = dest_pixel;
  }
  return error;
}
