#include <stdio.h>

#define MODULUS 998244353
//#define MODULUS 17

#define ROOT 3
#define MAX_N 1024
//#define MAX_N 8


typedef long long ll;

ll power(ll base, ll exponent) {
    ll result = 1;
    while (exponent > 0) {
        if (exponent & 1) result = (result * base) % MODULUS;
        base = (base * base) % MODULUS;
        exponent >>= 1;
    }
    return result;
}

void nttKernel(ll *data, int len, ll *w_values, int i){
            for (int j = 0; j < len / 2; ++j) {
		// take the w values
		ll w = w_values[j];
		//calculate u and v values
		ll u = data[i + j];
		ll v = (data[i + j + len / 2] * w ) % MODULUS;

		//update the positions of the data array
	
 		data[i + j] = u + v < MODULUS ? u + v : u + v - MODULUS;
                data[i + j + len / 2] = u - v >= 0 ? u - v : u - v + MODULUS;
            }
}

void ntt(ll *data, int n, int invert) {
    // Bit-reverse the array
    for (int i = 1, j = 0; i < n; ++i) {
        int bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;

        if (i < j) {
            ll tmp = data[i];
            data[i] = data[j];
            data[j] = tmp;
        }
    }

    // NTT main loop
    for (int len = 2; len <= n; len <<= 1) {
        ll wlen = invert ? power(ROOT, (MODULUS - 1) / len) : power(ROOT, (MODULUS - 1) - (MODULUS - 1) / len);

 	// Array to store w values
	ll w_values[len / 2];

        ll w = 1;

        for (int j = 0; j < len / 2; ++j) {
	    //update the w values
	    w_values[j] = w;
	    w = (w * wlen) % MODULUS;
		   
	}

        for (int i = 0; i < n; i += len) {
	   
	    nttKernel(data,len,w_values,i);
       }
    }

    // If inverse, divide by n
    if (invert) {
        ll n_inv = power(n, MODULUS - 2);
        for (int i = 0; i < n; ++i)
            data[i] = (data[i] * n_inv) % MODULUS;
    }
}

int main() {
    ll data[MAX_N] = {1, 2, 3, 4, 5, 6, 7, 8};
    int n = 8;

    ntt(data, n, 0); // NTT

    printf("After NTT:\n");
    for (int i = 0; i < n; ++i) printf("%lld ", data[i]);

    ntt(data, n, 1); // inverse NTT

    printf("\nAfter inverse NTT:\n");
    for (int i = 0; i < n; ++i) printf("%lld ", data[i]);

    return 0;
}

