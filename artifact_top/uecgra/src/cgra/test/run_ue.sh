# !/bin/sh

WORK_DIR=/work/global/pp482/uecgra-src/build-ue-eopt
TEST_DIR=/work/global/pp482/uecgra-src/src/cgra/test

test_list=(fir bf fft latnrm susan)

for test in ${test_list[@]}
do
  BUILD_DIR=$WORK_DIR/build_$test
  mkdir -p $BUILD_DIR && cd $BUILD_DIR
  pytest $TEST_DIR/StaticCGRA_RGALS_test.py -k ${test}_dvfs_eeff.json -vxs --tb=short --clock-time=1.33 2>&1 | tee perf_$test
  cd -
done
