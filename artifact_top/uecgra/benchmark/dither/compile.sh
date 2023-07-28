clang -emit-llvm -O3 -fno-unroll-loops -o dither.bc -c dither.c
llvm-dis dither.bc -o dither.ll
