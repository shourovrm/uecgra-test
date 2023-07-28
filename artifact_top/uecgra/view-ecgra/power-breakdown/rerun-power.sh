# !/bin/bash
#=========================================================================
# rerun-power.sh
#=========================================================================
# Re-run power analysis for CGRA apps. Collect all power reports to pwr_rpts
#
# Author: Peitian Pan
# Date  : Oct 20, 2019

date +%Y-%m%d-%H%M-%S > .time_start

clock_time=5.0
test_list=(fir bf fft latnrm susan)

run_pymtl() {
  test_name=$1
  cd ../*-pymtl-vcd/src/cgra/test
  mkdir -p build && cd build
  rm -rf ./*
  pytest ../StaticCGRA_test.py::StaticCGRA_Trans_Tests::test_${test} -xvs --tb=short --clock-time=${clock_time} 2>&1 | tee perf_$test
  cd ../../../../outputs
  cp ../src/cgra/test/build/*.verilator1.vcd run.vcd
  cp ../src/cgra/test/build/perf_${test} .
  cd ../
}

for test in ${test_list[@]}
do
  run_pymtl $test

  cd ../*-synopsys-vcat-tb/
  sh run-step.sh

  cd ../*-synopsys-vcs-gl/
  sh run-step.sh > ${test}_vcs.log
  mv verilog.dump ${test}.vcd

  cd ../*-synopsys-ptpx-gl/
  sh run-step.sh

  cd ../*-power-breakdown/

  mkdir -p pwr_rpts/${test}/
  find ../*-synopsys-ptpx-gl/reports/ ! -name *.activity.pre.rpt -exec cp -t pwr_rpts/${test}/ {} +

  cd ../*-pymtl-vcd/outputs/
  mv run.vcd run_${test}_eeff.vcd

  cd ../../*-synopsys-ptpx-gl/
done

date +%Y-%m%d-%H%M-%S > .time_end
