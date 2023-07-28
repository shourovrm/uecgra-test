#! /bin/bash
#=========================================================================
# rerun-power.sh
#=========================================================================
# Hacky script to rerun tests of all operators and get the final stack
# plot. Set the directory correctly and just run the script.
#
# Author : Yanghui Ou
#   Date : Aug 23, 2019

# Pre

date +%Y-%m%d-%H%M-%S > .time_start

# Commands

test_list=(stream_mul stream_add stream_sub stream_sll stream_srl \
           stream_cp0 stream_and stream_or  stream_xor stream_eq \
           stream_ne  stream_gt  stream_geq stream_lt  stream_leq \
           stream_bps stall )

run_pymtl(){
  test_name=$1
  cd ../*-pymtl-vcd/src/cgra/test
  mkdir -p build && cd build
  rm -rf ./*
  pytest ../TileStatic_test.py::TileStaticV_Tests::test_${test_name} -v --tb=short
  cd ../../../../outputs
  ln -fs ../src/cgra/test/build/*.sv design.v
  ln -fs ../src/cgra/test/build/*.vcd run.vcd
  cd ../
}

for test in ${test_list[@]}
do
  run_pymtl $test

  cd ../*-synopsys-vcat-tb
  sh run-step.sh

  cd ../*-synopsys-vcs-gl
  sh run-step.sh

  cd ../*-synopsys-ptpx-gl
  sh run-step.sh

  cd ../*-power-breakdown
  sh run-step.sh
  mkdir -p power_jsons
  mv outputs/power_breakdown.json power_jsons/${test}.json
done

python super_plot.py --path-dict path-dict.json
python canonicalizer.py
mv tile_energy.json energy_e.json

# Post

date +%Y-%m%d-%H%M-%S > .time_end
