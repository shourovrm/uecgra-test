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
           stream_cp0 stream_and stream_or stream_xor stream_eq \
           stream_ne stream_gt stream_geq stream_lt stream_leq \
           stream_bps stall )

run_pymtl(){
  test_name=$1
  cd ../*-pymtl-vcd/src/cgra/test
  mkdir -p build_asic_uetile && cd build_asic_uetile
  rm -rf ./*
  pytest ../TileStatic_RGALS_test.py::TileStatic_RGALS_Tests::test_${test_name} -svx
  cd ../../../../outputs
  ln -fs ../src/cgra/test/build_asic_uetile/TileStatic_RGALS_wrapper*.sv design.v
  ln -fs ../src/cgra/test/build_asic_uetile/TileStatic_RGALS_wrapper*.vcd run.vcd
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
  cp outputs/power_breakdown.json power_jsons/${test}.json
done

python super_plot.py --path-dict path-dict.json
# python ue_e_beta.py --factor 2 --e-dict path-dict.json --ue-dict path-dict.json \
#                     --e-prefix /work/global/yo96/alloy-asic/build-tile-32b-28nm-500M/10-power-breakdown \
#                     --ue-prefix /work/global/pp482/alloy-asic/build_uetile/10-power-breakdown
python canonicalizer.py
mv tile_energy.json energy_ue.json

# Post

date +%Y-%m%d-%H%M-%S > .time_end
