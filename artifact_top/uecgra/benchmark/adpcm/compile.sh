clang -emit-llvm -O3 -fno-unroll-loops -o adpcm.bc -c adpcm.c
llvm-dis adpcm.bc -o adpcm.ll
