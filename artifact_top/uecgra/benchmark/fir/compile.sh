clang -emit-llvm -O3 -fno-unroll-loops -o fir.bc -c fir.c
llvm-dis-12 fir.bc -o fir.ll
