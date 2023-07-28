"""
==========================================================================
super_plot.py
==========================================================================
plot the super stacked bar plot for different operations.

Author : Yanghui Ou
  Date : Aug 18, 2019

"""
import argparse
import sys
import json

from matplotlib.cm import get_cmap

from utils import *
from color_scheme import get_tile_breakdown_color_dict
from plot_stack import plot_stack

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
  p.add_argument( '-v', '--verbose',   action='store_true'          )
  p.add_argument( '-h', '--help',      action='store_true'          )
  p.add_argument(       '--path-dict', default=''                   )
  p.add_argument(       '--plot',      default='power_stack_op.pdf' )

  opts = p.parse_args()
  if opts.help: p.error()
  return opts

#-------------------------------------------------------------------------
# plot_stack
#-------------------------------------------------------------------------
# Creates a stacked bar plot based on input json files.

def join_data( jpath_dict={} ):

  nbars = len( jpath_dict )
  data_dict = {}
  for bar_name, jpath in jpath_dict.items():
    with open( jpath ) as f:
      data = json.load( f )
      data_dict[ bar_name ] = data

  bar_names = []

  plt_dict = {}

  def sum_mux_pwr( data ):
    pwr = 0.0
    for k, v in data.items():
      if k.lower().find( 'mux' ) >= 0:
        pwr += data[k]['switch_pwr'] + data[k]['int_pwr']
    return pwr

  plt_dict[ 'leak'   ] = []
  plt_dict[ 'mul'    ] = []
  plt_dict[ 'alu'    ] = []
  plt_dict[ 'acc'    ] = []
  plt_dict[ 'in_q_n' ] = []
  plt_dict[ 'in_q_s' ] = []
  plt_dict[ 'in_q_w' ] = []
  plt_dict[ 'in_q_e' ] = []
  plt_dict[ 'muxes'  ] = []
  plt_dict[ 'other'  ] = []

  # Create name map
  mul_path = 'dpath/node/mul'
  alu_path = 'dpath/node/alu'
  acc_path = 'dpath/acc_reg'
  q_n_path = 'in_q_n'
  q_s_path = 'in_q_s'
  q_w_path = 'in_q_w'
  q_e_path = 'in_q_e'

  for bname, data in data_dict.items():
    bar_names.append( bname )
    plt_dict[ 'leak'   ].append( data[ 'top' ][ 'leak_pwr' ] )
    plt_dict[ 'mul'    ].append( data[ mul_path ]['switch_pwr'] + data[ mul_path ]['int_pwr']   )
    plt_dict[ 'alu'    ].append( data[ alu_path ]['switch_pwr'] + data[ alu_path ]['int_pwr']   )
    plt_dict[ 'acc'    ].append( data[ acc_path ]['switch_pwr'] + data[ acc_path ]['int_pwr']   )
    plt_dict[ 'in_q_n' ].append( data[ q_n_path ]['switch_pwr'] + data[ q_n_path ]['int_pwr']   )
    plt_dict[ 'in_q_s' ].append( data[ q_s_path ]['switch_pwr'] + data[ q_s_path ]['int_pwr']   )
    plt_dict[ 'in_q_w' ].append( data[ q_w_path ]['switch_pwr'] + data[ q_w_path ]['int_pwr']   )
    plt_dict[ 'in_q_e' ].append( data[ q_e_path ]['switch_pwr'] + data[ q_e_path ]['int_pwr']   )
    plt_dict[ 'muxes'  ].append( sum_mux_pwr( data )                                            )
    plt_dict[ 'other'  ].append( data[ 'other' ][ 'switch_pwr' ] + data[ 'other' ][ 'int_pwr' ] )

  total_mul = data_dict[ 'mul' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'mul' ][ 'top' ][ 'int_pwr' ]
  total_add = data_dict[ 'add' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'add' ][ 'top' ][ 'int_pwr' ]
  total_sll = data_dict[ 'sll' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'sll' ][ 'top' ][ 'int_pwr' ]
  total_srl = data_dict[ 'srl' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'srl' ][ 'top' ][ 'int_pwr' ]
  total_cp0 = data_dict[ 'cp0' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'cp0' ][ 'top' ][ 'int_pwr' ]
  total_and = data_dict[ 'and' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'and' ][ 'top' ][ 'int_pwr' ]
  total_or  = data_dict[ 'or'  ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'or'  ][ 'top' ][ 'int_pwr' ]
  total_xor = data_dict[ 'xor' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'xor' ][ 'top' ][ 'int_pwr' ]
  total_eq  = data_dict[ 'eq'  ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'eq'  ][ 'top' ][ 'int_pwr' ]
  total_ne  = data_dict[ 'ne'  ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'ne'  ][ 'top' ][ 'int_pwr' ]
  total_gt  = data_dict[ 'gt'  ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'gt'  ][ 'top' ][ 'int_pwr' ]
  total_geq = data_dict[ 'geq' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'geq' ][ 'top' ][ 'int_pwr' ]
  total_lt  = data_dict[ 'lt'  ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'lt'  ][ 'top' ][ 'int_pwr' ]
  total_leq = data_dict[ 'leq' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'leq' ][ 'top' ][ 'int_pwr' ]
  total_bps = data_dict[ 'bps' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'bps' ][ 'top' ][ 'int_pwr' ]
  total_stall = data_dict[ 'stall' ][ 'top' ][ 'switch_pwr' ] + data_dict[ 'stall' ][ 'top' ][ 'int_pwr' ]

  print( f'alpha_mul = {total_mul/total_mul}' )
  print( f'alpha_add = {total_add/total_mul}' )
  print( f'alpha_sll = {total_sll/total_mul}' )
  print( f'alpha_srl = {total_srl/total_mul}' )
  print( f'alpha_cp0 = {total_cp0/total_mul}' )
  print( f'alpha_and = {total_and/total_mul}' )
  print( f'alpha_or  = {total_or /total_mul}')
  print( f'alpha_xor = {total_xor/total_mul}')
  print( f'alpha_eq  = {total_eq /total_mul}')
  print( f'alpha_ne  = {total_ne /total_mul}')
  print( f'alpha_gt  = {total_gt /total_mul}')
  print( f'alpha_geq = {total_geq/total_mul}')
  print( f'alpha_lt  = {total_lt /total_mul}')
  print( f'alpha_leq = {total_leq/total_mul}')
  print( f'alpha_bps = {total_bps/total_mul}')
  print( f'alpha_stall = {total_stall/total_mul}')

  return bar_names, plt_dict

#-------------------------------------------------------------------------
# plot_stack
#-------------------------------------------------------------------------

def main():
  opts = parse_cmdline()

  if opts.help:
    return

  # Parse the path dictionary
  with open( opts.path_dict ) as f:
    jpath_dict = json.load( f )

  bar_names, plt_dict = join_data( jpath_dict )

  if opts.plot:
    if opts.verbose: print( f'Saving stack plot to {opts.plot}' )

    color_dict = get_tile_breakdown_color_dict("tab20")

    plot_stack( plt_dict, color_dict, ylabel='power', bar_names=bar_names, outdir=opts.plot )

main()

