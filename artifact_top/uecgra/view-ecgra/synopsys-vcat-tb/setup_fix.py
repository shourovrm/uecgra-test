#=========================================================================
# setup_fix.py
#=========================================================================
# Hack into the vcat-generated testbench to fix setup violations in GL
# This script takes in a json spec file about how to fix violations.
# The spec file should be parsed as a dict that maps signal names to
# a list of pairs of (num_of_occurrence, time), where num_of_occurrence
# is the occurrence of the signal to be fixed, and time will be added to
# the delay value of that occurrence.
#
# Author: Peitian Pan
# Date:   Oct 24, 2019

import argparse
import json
import os

def parse_cml():
    p = argparse.ArgumentParser()
    p.add_argument('--fix-spec')
    p.add_argument('--clock-time')
    p.add_argument('--testbench')
    opts = p.parse_args()
    return opts

def is_target(splt, spec, occur):
    return splt[1] in spec and occur in map(lambda x: x[0], spec[splt[1]])

def mutate_target(splt, spec, occur, clock_time):
    delta = list(filter(lambda x: x[0] == occur, spec[splt[1]]))
    assert len(delta) == 1
    splt[0] = f'#{float(splt[0][1:]) + delta[0][1]*clock_time}'

def main():
    opts = parse_cml()
    spec_path = opts.fix_spec
    clock_time = float(opts.clock_time)
    tb_path = opts.testbench

    print(f'Reading fix spec file {spec_path} with clock time {clock_time} ns...')

    with open(spec_path, 'r') as fd:
        spec = json.load(fd)

    tb = []
    with open(tb_path, 'r') as fd:
        occur = -1
        in_block = False
        for _line in fd.readlines():
            line = _line
            if _line.startswith('initial begin'):
                occur = 0
                in_block = True
            elif in_block and _line.startswith('end'):
                in_block = False
            elif in_block:
                line_splt = _line.split()
                if is_target(line_splt, spec, occur):
                    mutate_target(line_splt, spec, occur, clock_time)
                    line = f"    {' '.join(line_splt)}"+'\n'
                occur += 1
            tb.append(line)

    with open(tb_path+'.tmp', 'w') as fd:
        fd.write(''.join(tb))

    os.rename(tb_path+'.tmp', tb_path)

    print('Vcat setup fix finished!')

main()
