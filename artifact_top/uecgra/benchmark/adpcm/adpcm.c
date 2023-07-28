#include <stdlib.h>
#include <stdio.h>
#include "mibench-adpcmdec-src.dat"
#include "mibench-adpcmdec-ref.dat"

#define INDEX_MIN 0
#define INDEX_MAX 88

#define VALPRED_MIN -32768
#define VALPRED_MAX  32767

// Intel ADPCM step variation table
static int indexTable[16] = {
  -1, -1, -1, -1, 2, 4, 6, 8,
  -1, -1, -1, -1, 2, 4, 6, 8,
};

static short stepsizeTable[89] = {
  7, 8, 9, 10, 11, 12, 13, 14, 16, 17,
  19, 21, 23, 25, 28, 31, 34, 37, 41, 45,
  50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
  130, 143, 157, 173, 190, 209, 230, 253, 279, 307,
  337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
  876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066,
  2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358,
  5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
  15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767
};

int mibench_adpcmdec_scalar(char indata[], short outdata[],
                             int len, int valprev, int idx);

int main()
{
  short *dest = (short*) malloc(sizeof(short) * len);

  int res = mibench_adpcmdec_scalar(&src[0], &dest[0], len, 0, 0);

  printf("res = %d\n", res);
  for(int i = 0; i < len; i++)
    if(dest[i] != ref[i])
    {
      printf("dst[%d](%d) != ref[%d](%d)\n", i, dest[i], i, ref[i]);
      printf("  [FAILED]\n");
      return 0;
    }
  printf("  [PASSED]\n");

  return 0;
}

int mibench_adpcmdec_scalar(char indata[], short outdata[],
                             int len, int valprev, int idx)
{

  printf("Inside");
  int delta       = 0;                    // Current adpcm output value
  int sign        = 0;                    // Current adpcm sign bit
  int inputbuffer = 0;                    // Place to keep the next 4-bit value
  int vpdiff      = 0;                    // Current change to valpred
  int valpred     = valprev;              // Predicted value
  int index       = idx;                  // Current step change index
  int step        = stepsizeTable[index]; // Stepsize
  int bufferstep  = 0;                    // Toggle between inputbuffer/input

  // Decode input
  for(int i = 0; i < len ; i++)
  {
    //------------------------------------------------------------------
    // Step 1 - get the delta value
    //------------------------------------------------------------------

    /* if ( bufferstep ) { */
    /*   delta = inputbuffer & 0xf; */
    /* } */
    /* else { */
    /*   inputbuffer = indata[i/2]; */
    /*   delta       = (inputbuffer >> 4) & 0xf; */
    /* } */
    if ( bufferstep == 0x1 ) {
      delta = inputbuffer;
    }
    else {
      inputbuffer = indata[i];
      delta       = inputbuffer;
      /* inputbuffer = indata[i >> 1]; */
      /* delta       = (inputbuffer >> 4); */
    }
    bufferstep = bufferstep ^ 0x1;

    //------------------------------------------------------------------
    // Step 2 - Find new index value (for later)
    //------------------------------------------------------------------

    index += indexTable[delta];
    // This cannot be efficiently mapped on the CGRA. I have to do some
    // approximation to make this work... 
    /* if ( index < INDEX_MIN ) index = INDEX_MIN; */
    /* if ( index > INDEX_MAX ) index = INDEX_MAX; */
    /* index = index & 0x3F; */

    //------------------------------------------------------------------
    // Step 3 - Separate sign and magnitude
    //------------------------------------------------------------------

    /* sign  = delta; */
    /* sign  = delta & 8; */
    /* delta = delta & 7; */

    //------------------------------------------------------------------
    // Step 4 - Compute difference and new predicted value
    // Computes 'vpdiff = (delta+0.5)*step/4', but see comment
    // in adpcm_coder.
    //------------------------------------------------------------------

    /* vpdiff = step; */
    /* vpdiff = step >> 3; */
    /* if ( delta & 4 ) vpdiff += step; */
    /* if ( delta & 2 ) vpdiff += step>>1; */
    /* if ( delta & 1 ) vpdiff += step>>2; */

    /* if ( sign ) */
    /*   valpred -= vpdiff; */
    /* else */
    /*   valpred += vpdiff; */

    if ( delta != 0 )
      valpred -= step;
    else
      valpred += step;

    //------------------------------------------------------------------
    // Step 5 - clamp output value
    //------------------------------------------------------------------

    /* if ( valpred > VALPRED_MAX ) */
    /*   valpred = VALPRED_MAX; */
    /* else if ( valpred < VALPRED_MIN ) */
    /*   valpred = VALPRED_MIN; */

    //------------------------------------------------------------------
    // Step 6 - Update step value
    //------------------------------------------------------------------

    step = stepsizeTable[index];

    //------------------------------------------------------------------
    // Step 7 - Output value
    //------------------------------------------------------------------

    outdata[i] = valpred;
  }
  return step;
}
