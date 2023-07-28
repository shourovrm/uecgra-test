# !/bin/sh

WORK_DIR=/work/global/pp482/uecgra-src/build-e
TEST_DIR=/work/global/pp482/uecgra-src/src/cgra/test

test_list=(fir bf fft latnrm susan)

for test in ${test_list[@]}
do
  BUILD_DIR=$WORK_DIR/build_$test
  mkdir -p $BUILD_DIR && cd $BUILD_DIR
  pytest $TEST_DIR/StaticCGRA_test.py::StaticCGRA_Trans_Tests::test_$test -vxs --tb=short 2>&1 | tee perf_$test
  cd -
done
