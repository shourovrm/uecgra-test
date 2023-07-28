# !/bin/sh

WORK_DIR=/work/global/pp482/uecgra-src/build
RPT_DIR=/work/global/pp482/uecgra-src/build/eeff_rpt
TEST_DIR=/work/global/pp482/uecgra-src/src/cgra/test
ASIC_DIR=/work/global/pp482/alloy-asic/build_uecgra

test_list=(fir bf fft latnrm susan)

for test in ${test_list[@]}
do
  BUILD_DIR=$WORK_DIR/build_${test}_eeff
  cd $WORK_DIR
  mkdir -p $BUILD_DIR && cd $BUILD_DIR
  pytest $TEST_DIR/StaticCGRA_RGALS_test.py -k ${test}_dvfs_eeff.json -vxs --tb=short 2>&1 | tee perf_$test
  cd $ASIC_DIR/*-pymtl-vcd/outputs
  ln -s $BUILD_DIR/StaticCGRA_RGALS_wrapper__d2c16ea9f701a1e2.verilator1.vcd run.vcd
  cd ../..
  cd *-synopsys-vcat-tb/
  sh run-step.sh
  cd ../*-synopsys-vcs-gl/
  sh run-step.sh
  cd ../*-synopsys-ptpx-gl/
  sh run-step.sh
  cp -r reports $RPT_DIR/${test}
  cd ../*-pymtl-vcd/outputs/
  mv run.vcd run_${test}_eeff.vcd
done
