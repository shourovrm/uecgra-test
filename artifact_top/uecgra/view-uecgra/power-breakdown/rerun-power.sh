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
suffices=(dvfs dvfs_eeff)
test_list=(fir bf fft latnrm susan)

run_pymtl() {
  test_name=$1
  suffix=$2
  cd ../*-pymtl-vcd/src/cgra/test
  mkdir -p build && cd build
  rm -rf ./*
  pytest ../StaticCGRA_RGALS_test.py -k ${test}_${suffix}.json -vxs --tb=short --clock-time=${clock_time} 2>&1 | tee perf_$test
  cd ../../../../outputs
  cp ../src/cgra/test/build/*.verilator1.vcd run.vcd
  cd ../
}

for suffix in ${suffices}
do
for test in ${test_list[@]}
do
  run_pymtl $test $suffix

  cd ../*-synopsys-vcat-tb/
  sh run-step.sh
  cp outputs/testbench.v tb_${test}_${suffix}.v

  cd ../*-synopsys-vcs-gl/
  sh run-step.sh > ${test}_${suffix}_vcs.log
  mv verilog.dump $test_${suffix}.vcd

  cd ../*-synopsys-ptpx-gl/
  sh run-step.sh

  cd ../*-power-breakdown/

  mkdir -p pwr_rpts_${suffix}/${test}/
  find ../*-synopsys-ptpx-gl/reports/ ! -name *.activity.pre.rpt -exec cp -t pwr_rpts_${suffix}/${test}/ {} +

  cd ../*-pymtl-vcd/outputs/
  mv run.vcd run_${test}_${suffix}.vcd

  cd ../../*-synopsys-ptpx-gl/
done
done

date +%Y-%m%d-%H%M-%S > .time_end
