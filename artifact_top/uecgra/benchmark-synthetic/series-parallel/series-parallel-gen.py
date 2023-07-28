#=========================================================================
# series-parallel-gen.py
#=========================================================================
# Dump JSON configuration file for the serial-parallel kernel pattern.
#
# -h --help                Display help message
#
# --nrows                  Number of CGRA rows
# --ncols                  Number of CGRA cols
# --prologue               Number of operations before entering the parallel region
# --body                   Number of operations in the longer parallel region
# --epilogue               Number of operations after leaving the parallel region
# --prologue_clk           {"nominal", "fast", "slow"}
# --body_clk               {"nominal", "fast", "slow"}
# --epilogue_clk           {"nominal", "fast", "slow"}
# --ops                    {"cp0", "add", "mul"}
#
# Author : Peitian Pan
# Date   : Aug 19, 2019

import argparse
import json
import sys
from itertools import product

# Command line argument parser

class ArgParser(argparse.ArgumentParser):
  def error(s, msg = ""):
    if msg: print("\n" + " ERROR: " + msg)
    print("")
    file = open(sys.argv[0])
    for lineno, line in enumerate(file):
      if line[0] != '#':
        sys.exit(msg != '')
      if (lineno == 2) or (lineno >= 4):
        print(line[1:].rstrip('\n'))

# Parser the given command line options

def parse_cmd():
  p = ArgParser(add_help = False)

  p.add_argument("-h", "--help", action = "store_true")
  p.add_argument("--nrows", default = 8, type = int)
  p.add_argument("--ncols", default = 8, type = int)
  p.add_argument("--prologue", default = 1, type = int)
  p.add_argument("--body", default = 1, type = int)
  p.add_argument("--epilogue", default = 1, type = int)
  p.add_argument("--prologue_clk", default = "nominal", choices = ["nominal", "fast", "slow"])
  p.add_argument("--body_clk", default = "nominal", choices = ["nominal", "fast", "slow"])
  p.add_argument("--epilogue_clk", default = "nominal", choices = ["nominal", "fast", "slow"])
  p.add_argument("--ops", default = "add", choices = ["cp0", "add", "mul"])

  opts = p.parse_args()
  if opts.help:
    p.error()
  return opts

# Map series-parallel pattern to a CGRA of the given size

def simple_map(opts):
  nrows, ncols, ops = opts.nrows, opts.ncols, opts.ops
  npro, nbody, nepi = opts.prologue, opts.body, opts.epilogue
  pro_clk, body_clk, epi_clk = opts.prologue_clk, opts.body_clk, opts.epilogue_clk

  assert (nbody % 2) == 1, "only odd number of nodes in the body are allowed!"
  assert (nbody + 3) // 2 <= ncols and (npro + nepi) <= nrows, \
      f"cannot map series-parallel pattern with the given parameters to {nrows}x{ncols} CGRA"

  cfgs = [ {
    'x':x, 'y':y, 'op':'cp0', 'src_a':'self', 'src_b':'self', 'dst':['self'], 'dvfs':'nominal',
  } for y, x in product(range(nrows), range(ncols))]
  cur_x, cur_y = 0, nrows-1

  # Map prologue
  assert npro >= 1
  while npro:
    cfgs[cur_x+cur_y*ncols] = {
      'x':cur_x, 'y':cur_y, 'op':ops, 'src_a':'N', 'src_b':'N', 'dst':['S'], 'dvfs':pro_clk,
    }
    # The last node in the prologue domain has two destinations ( two parallel regions )
    if npro == 1:
      cfgs[cur_x+cur_y*ncols]['dst'] = ['S', 'E']
    cur_y, npro = cur_y - 1, npro - 1

  # Map short parallel region
  cfgs[cur_x+cur_y*ncols] = {
    'x':cur_x, 'y':cur_y, 'op':ops, 'src_a':'N', 'src_b':'N', 'dst':['E'], 'dvfs':'nominal',
  }
  cur_x, cur_y = cur_x + 1, cur_y + 1

  # Map body along x-plus direction
  nbody_x_plus = (nbody - 1) // 2
  while nbody_x_plus:
    cfgs[cur_x+cur_y*ncols] = {
      'x':cur_x, 'y':cur_y, 'op':ops, 'src_a':'W', 'src_b':'W', 'dst':['E'], 'dvfs':body_clk,
    }
    cur_x, nbody_x_plus = cur_x + 1, nbody_x_plus - 1

  # Map body turning point
  cfgs[cur_x+cur_y*ncols] = {
    'x':cur_x, 'y':cur_y, 'op':ops, 'src_a':'W', 'src_b':'W', 'dst':['S'], 'dvfs':body_clk,
  }
  cur_y = cur_y - 1

  # Map body along x-minus direction
  nbody_x_minus = (nbody - 1) // 2
  while nbody_x_minus:
    cfgs[cur_x+cur_y*ncols] = {
      'x':cur_x, 'y':cur_y, 'op':ops,
      'src_a':'N' if nbody_x_minus == ((nbody - 1) // 2) else 'E',
      'src_b':'N' if nbody_x_minus == ((nbody - 1) // 2) else 'E',
      'dst':['W'],
      'dvfs':body_clk,
    }
    cur_x, nbody_x_minus = cur_x - 1, nbody_x_minus - 1

  # Map epilogue
  n_epilogue = nepi
  assert nepi >= 1
  while nepi:
    cfgs[cur_x+cur_y*ncols] = {
      'x':cur_x, 'y':cur_y, 'op':ops,
      'src_a':'W' if nepi == n_epilogue else 'N',
      'src_b':'E' if (nepi == n_epilogue) and (nbody > 1) else 'N',
      'dst':['E'] if (nepi == 1) and ((nbody == 1) or (n_epilogue > 1)) else ['S'],
      'dvfs':epi_clk,
    }
    cur_y, nepi = cur_y - 1, nepi - 1

  if (nbody == 1) or (n_epilogue > 1):
    cur_x, cur_y = cur_x + 1, cur_y + 1

  # Route the result of the last node to the east side of CGRA
  nroute = ncols - cur_x
  while nroute:
    cfgs[cur_x+cur_y*ncols] = {
      'x':cur_x, 'y':cur_y, 'op':'cp0',
      'src_a':'W' if (nbody == 1) or (n_epilogue > 1) else 'N',
      'src_b':'self',
      'dst':['E'],
      'dvfs':epi_clk,
    }
    cur_x, nroute = cur_x + 1, nroute - 1
    if not nroute:
      cur_x -= 1

  return cur_x, cur_y, cfgs

# Main

if __name__ == "__main__":
  opts = parse_cmd()
  nrows, ncols, ops = opts.nrows, opts.ncols, opts.ops
  npro, nbody, nepi = opts.prologue, opts.body, opts.epilogue
  pro_clk, body_clk, epi_clk = opts.prologue_clk, opts.body_clk, opts.epilogue_clk

  # Generate configurations
  exit_x, exit_y, cfgs = simple_map(opts)
  assert exit_y >= 0 and exit_x == (opts.ncols - 1), \
      f"script failed to map the pattern to a/an {nrows}x{ncols} CGRA!"

  # Dump JSON configurations
  filename = f"cfg_series_parallel_{nrows}x{ncols}_{ops}_{npro}_{pro_clk}_{nbody}_{body_clk}_{nepi}_{epi_clk}.json"

  with open(filename, "w") as output:
    json.dump(cfgs, output, sort_keys = True, indent = 4, separators=(',', ':'))
