"""
==========================================================================
energy_sim.py
==========================================================================

 -v, --verbose : enable verbose mode.
 -h, --help    : show help.
 -o, --output  : output path for the energy breakdown json.
     --config  : path for the configuration json.
     --ntokens : number of tokens, 32 by default.
     --ncols   : number of columns of the CGRA, 8 by default.
     --nrows   : number of rows of the CGRA, 8 by default.
     --ld-nom  : number of SRAM banks configured to perform load and
                 operate at nominal voltage and frequency, 0 by default.
     --ld-slow : number of SRAM banks configured to perform load and
                 operate at slow voltage and frequency, 0 by default.
     --ld-fast : number of SRAM banks configured to perform load and
                 operate at fast voltage and frequency, 0 by default.
     --ld-nom  : number of SRAM banks configured to perform store and
                 operate at nominal voltage and frequency, 0 by default.
     --ld-slow : number of SRAM banks configured to perform store and
                 operate at slow voltage and frequency, 0 by default.
     --ld-fast : number of SRAM banks configured to perform store and
                 operate at fast voltage and frequency, 0 by default.

Author : Yanghui Ou
  Date : Sep 2, 2019

"""
import argparse
import json
import sys
from dataclasses import dataclass

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
# Data
#-------------------------------------------------------------------------

e_mul        = 2.694 # pJ/mul
e_sram_read  = 5.126 # pJ/read
e_sram_write = 6.413 # pJ/write

# ration of each operation w.r.t. mul for elastic tile
alpha = {
  'mul' : 1.000,
  'add' : 0.525,
  'sll' : 0.458,
  'srl' : 0.430,
  'cp0' : 0.419,
  'cp1' : 0.419,
  'and' : 0.525,
  'or'  : 0.535,
  'xor' : 0.571,
  'eq'  : 0.377,
  'ne'  : 0.378,
  'gt'  : 0.413,
  'geq' : 0.412,
  'lt'  : 0.412,
  'leq' : 0.411,
  'bps' : 0.186,
  'phi' : 0.419,
  'br'  : 0.419,
  'nop' : 0.000,
}

# ration between ue-tile and e-tile
beta = {
  'mul' : 1.328,
  'add' : 1.057,
  'sll' : 1.172,
  'srl' : 1.181,
  'cp0' : 1.196,
  'cp1' : 1.196,
  'and' : 1.057,
  'or'  : 1.066,
  'xor' : 1.089,
  'eq'  : 1.114,
  'ne'  : 1.115,
  'gt'  : 1.117,
  'geq' : 1.115,
  'lt'  : 1.117,
  'leq' : 1.115,
  'bps' : 1.473,
  'phi' : 1.196,
  'br'  : 1.196,
  'nop' : 1.000,
}

voltage = {
  'nominal' : 0.90,
  'slow'    : 0.61,
  'fast'    : 1.23,
}

t_clk = {
  'nominal' : 2.00,
  'slow'    : 6.00,
  'fast'    : 1.33,
}

#-------------------------------------------------------------------------
# Helpers
#-------------------------------------------------------------------------

@dataclass
class Tile:
  op   : str   = 'nop'
  bps  : bool  = False
  v    : float = voltage['nominal']
  f    : float = 1.0 / t_clk['nominal']
  e_e  : float = 0.0
  e_ue : float = 0.0

#-------------------------------------------------------------------------
# parse_cmdline
#-------------------------------------------------------------------------

def parse_cmdline():
  p = ArgumentParserWithCustomError( add_help=False )
  p.add_argument( '-v', '--verbose', action='store_true'       )
  p.add_argument( '-h', '--help',    action='store_true'       )
  p.add_argument(       '--config'                             )
  p.add_argument( '-o', '--output',  default='energy_sim.json' )
  p.add_argument(       '--ntokens', default=32                )
  p.add_argument(       '--ncols',   default=8                 )
  p.add_argument(       '--nrows',   default=8                 )
  # SRAMs
  p.add_argument(       '--ld-nom',  type=int, default=0       )
  p.add_argument(       '--ld-slow', type=int, default=0       )
  p.add_argument(       '--ld-fast', type=int, default=0       )
  p.add_argument(       '--st-nom',  type=int, default=0       )
  p.add_argument(       '--st-slow', type=int, default=0       )
  p.add_argument(       '--st-fast', type=int, default=0       )

  opts = p.parse_args()
  if opts.help: p.error()
  return opts

#-------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------

def main():
  opts = parse_cmdline()

  if opts.help:
    return

  ncols = opts.ncols
  nrows = opts.nrows
  ntiles = ncols * nrows

  ntokens = int(opts.ntokens)

  v_e = voltage['nominal']

  cgra  = [ Tile() for _ in range(ntiles) ]
  edict = {}

  # Load config data
  with open( opts.config, 'r' ) as f:
    cfg_lst = json.load( f )

    for t in cfg_lst:

      assert 'x' in t; assert 'y' in t; assert 'op' in t
      tid = t['y'] * ncols + t['x']
      cgra[tid].op = t['op'].lower()

      # Add bypass energy
      if 'bps_dst' in t:
        if not 'none' in [ x.lower() for x in t['bps_dst'] ]:
          cgra[tid].bps = True

      if 'dvfs' in t:
        cgra[tid].v = voltage[ t['dvfs'] ]
        cgra[tid].f = 1.0 / t_clk[ t['dvfs'] ]

      op   = cgra[tid].op
      v_ue = cgra[tid].v
      bps  = cgra[tid].bps

      # ECGRA energy - everything is nominal
      e_e = e_mul * alpha[ op ] * ntokens
      if bps:
        e_e += e_mul * alpha[ 'bps' ] * ntokens

      # UECGRA energy - with dvfs and UE overhead
      e_ue = e_mul * alpha[ op ] * beta[ op ] * (v_ue**2)/(v_e**2) * ntokens
      if bps:
        e_ue += e_mul * alpha[ 'bps' ] * beta[ 'bps' ] * (v_ue**2)/(v_e**2) * ntokens

      cgra[tid].e_e  = e_e
      cgra[tid].e_ue = e_ue

  # Save energy breakdown
  e_dict  = {}
  ue_dict = {}

  for y in range(nrows):
    for x in range(ncols):
      tid = y * ncols + x
      e_dict [f'tile_{x}_{y}'] = cgra[tid].e_e
      ue_dict[f'tile_{x}_{y}'] = cgra[tid].e_ue

  # Compute sram energy
  e_sram_ld = ( opts.ld_nom + opts.ld_slow + opts.ld_fast ) * e_sram_read
  e_sram_st = ( opts.st_nom + opts.st_slow + opts.st_fast ) * e_sram_write

  e_dict['sram_ld'] = e_sram_ld * ntokens
  e_dict['sram_st'] = e_sram_st * ntokens

  ue_sram_ld_nom  = opts.ld_nom  * e_sram_read
  ue_sram_ld_slow = opts.ld_slow * e_sram_read * (voltage['slow']**2)/(v_e**2)
  ue_sram_ld_fast = opts.ld_fast * e_sram_read * (voltage['fast']**2)/(v_e**2)

  ue_sram_st_nom  = opts.st_nom  * e_sram_write
  ue_sram_st_slow = opts.st_slow * e_sram_write * (voltage['slow']**2)/(v_e**2)
  ue_sram_st_fast = opts.st_fast * e_sram_write * (voltage['fast']**2)/(v_e**2)

  ue_dict['sram_ld_nominal'] = ue_sram_ld_nom  * ntokens
  ue_dict['sram_ld_slow'   ] = ue_sram_ld_slow * ntokens
  ue_dict['sram_ld_fast'   ] = ue_sram_ld_fast * ntokens
  ue_dict['sram_st_nominal'] = ue_sram_st_nom  * ntokens
  ue_dict['sram_st_slow'   ] = ue_sram_st_slow * ntokens
  ue_dict['sram_st_fast'   ] = ue_sram_st_fast * ntokens

  with open( opts.output, 'w' ) as f:
    res = {
      'ecgra_energy'  : e_dict,
      'uecgra_energy' : ue_dict,
    }
    json.dump( res, f, indent=2 )

  # Report total energy
  total_e  = 0.0
  total_ue = 0.0
  for tile in cgra:
    total_e  += tile.e_e
    total_ue += tile.e_ue

  total_e += e_sram_ld * ntokens
  total_e += e_sram_st * ntokens

  total_ue += ue_sram_ld_nom  * ntokens
  total_ue += ue_sram_ld_slow * ntokens
  total_ue += ue_sram_ld_fast * ntokens
  total_ue += ue_sram_st_nom  * ntokens
  total_ue += ue_sram_st_slow * ntokens
  total_ue += ue_sram_st_fast * ntokens

  print(f'UECGRA energy for {ntokens} tokens: {total_ue:.3f} pJ ({total_ue/ntokens:.3f} pJ/token).')
  print(f'ECGRA  energy for {ntokens} tokens: {total_e:.3f} pJ ({total_e/ntokens:.3f} pJ/token).')
  print(f'Energy efficiency ratio (UECGRA/ECGRA): {total_e/total_ue:.3f}.')

main()
