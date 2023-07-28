#include "common.h"
#include "cgra_ubmark-dither.dat"

int dst[LEN];

int dither(int dest[], int src[], int len);

int main()
{
  test_stats_on();
  int res = dither(&dst[0], &src[0], LEN);
  test_stats_off();

  if(res == ref_result)
  {
    wprint(L"  [PASSED]\n");
    test_pass();
  }
  else
  {
    test_fail(0, res, ref_result);
    /* wprint(L"res = %d but ref = %d\n", res, ref_result); */
    /* wprint(L"  [FAILED]\n"); */
  }

  return 0;
}

__attribute__((noinline))
int dither(int dest[], int src[], int len)
{
  int i = 0;
  int error = 0;
  int dest_pixel = 0x00u;

  for(; i < len; i++) {
    /* dest_pixel = 0x00u; */

    int out = src[i] + error;

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
