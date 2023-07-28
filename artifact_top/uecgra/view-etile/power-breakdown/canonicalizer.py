#=========================================================================
# canonicalizer.py
#=========================================================================
# Canonoicalize power numbers into energy.
#
# Author : Peitian Pan
# Date   : Sep 12, 2019

import argparse
import sys 
import json
from fnmatch import fnmatch

#-------------------------------------------------------------------------
# ArgumentParserWithCustomError
#-------------------------------------------------------------------------

class ArgumentParserWithCustomError(argparse.ArgumentParser):
  def error( self, msg = "" ):
    if ( msg ): print("\n ERROR: %s" % msg)
    print("")
    # Print help message.
    with open( sys.argv[0] ) as f:
      line = f.readline()
      while not line.startswith( '\"\"\"' ):
        line = f.readline()

      line = f.readline()
      while not line.startswith( '\"\"\"' ):
        print( line.rstrip('\n') )
        line = f.readline()

#-------------------------------------------------------------------------
# parse_cmdline
#-------------------------------------------------------------------------

def parse_cmdline():
  p = ArgumentParserWithCustomError( add_help=False )
  p.add_argument( '-h', '--help',      action='store_true'        )
  p.add_argument(       '--path-dict', default='path-dict.json'   )
  p.add_argument(       '-o',          default='tile_energy.json' )

  opts = p.parse_args()
  if opts.help: p.error()
  return opts

#-------------------------------------------------------------------------
# helpers
#-------------------------------------------------------------------------

def energy_converter(period):
  def converter(pwr):
    return pwr*period*1000.0
  return converter

def dyn_pwr(pwr_entries):
  pwr = 0.0
  for pwr_entry in pwr_entries:
    pwr += pwr_entry['int_pwr'] + pwr_entry['switch_pwr']
  return pwr

#-------------------------------------------------------------------------
# canonicalize
#-------------------------------------------------------------------------

def canonicalize(pwr_dict):
  energy_per_sram_rd = 3.228
  energy_per_sram_wr = 3.964

  to_E = energy_converter(1.33)

  op_order = [
    'mul', 'add', 'sll', 'srl', 'cp0', 'and', 'or', 'xor', 'eq', 'ne',
    'gt', 'geq', 'lt', 'leq', 'bps', 'stall',
  ]
  name_map = {
    'mul' : 'dpath/node/mul',
    'alu' : 'dpath/node/alu',
    'acc_reg' : 'dpath/acc_reg',
    'q_n' : 'in_q_n',
    'q_s' : 'in_q_s',
    'q_w' : 'in_q_w',
    'q_e' : 'in_q_e',
    'suppress' : 'N/A',
    'unsafe_gen' : 'N/A',
    'clk_switcher' : 'N/A',
    'sram' : 'N/A',
    'muxes' : '*mux*',
    'other' : 'other',
  }
  special_op = [ 'load', 'store' ]

  energy_dict = {op:{} for op in op_order + special_op}

  for op in op_order:
    _pwr_dict = pwr_dict[op]
    # leak
    energy_dict[op]['leak'] = to_E(_pwr_dict['top']['leak_pwr'])

    for module, name in name_map.items():
      energy_dict[op][module] = to_E(dyn_pwr(
        T[1] for T in _pwr_dict.items() if fnmatch(T[0], name)))

  # Do math for load and store operations
  for module_name in name_map.keys():
    energy_dict['load'][module_name] = 0.0
    energy_dict['store'][module_name] = 0.0

  energy_dict['load']['leak']  = to_E(pwr_dict['bps']['top']['leak_pwr'])
  energy_dict['load']['sram']  = energy_per_sram_rd
  energy_dict['load']['other'] = to_E(dyn_pwr([pwr_dict['bps']['top']]))

  energy_dict['store']['leak']  = to_E(pwr_dict['bps']['top']['leak_pwr'])
  energy_dict['store']['sram']  = energy_per_sram_wr
  energy_dict['store']['other'] = to_E(dyn_pwr([pwr_dict['bps']['top']]))

  return energy_dict

def main():
  opts = parse_cmdline()

  if opts.help:
    return

  path_dict = {}
  with open(opts.path_dict, "r") as pd:
    path_dict = json.load(pd)

  power_dict  = {}
  for op_name, path in path_dict.items():
    with open(path, "r") as pd:
      _power_dict = json.load(pd)
      power_dict[op_name] = _power_dict

  energy_dict = canonicalize(power_dict)

  with open(opts.o, "w") as out:
    json.dump(energy_dict, out, indent=2)

  print("Canonicalization succeeds!")

if __name__ == "__main__":
  main()
