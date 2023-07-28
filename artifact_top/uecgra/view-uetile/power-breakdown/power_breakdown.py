"""
==========================================================================
power_breakdown.py
==========================================================================
Collect power breakdown information from hierarchy power report.

 -v, --verbose     : enable verbose mode.
 -h, --help        : show help.
     --report      : path for the hierachy power report.
     --search-dict : path for the search dictionary whose keys are designs
                     to search for and values are the hierachy leavel.
     --plot        : path to dump the stack plot. The script will do
                     nothing if this option if left empty.
     --dump-json   : path to dump the collected data. Do nothing if left
                     empty.

Author : Yanghui Ou
  Date : Aug 18, 2019

"""
import argparse
import json
import sys

from utils import pwr_dict_to_json, hier_rpt_to_json
from color_scheme import scheme_gen
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
  p.add_argument( '-v', '--verbose',   action='store_true' )
  p.add_argument( '-h', '--help',      action='store_true' )
  p.add_argument(       '--report'                         )
  p.add_argument(       '--search-dict'                    )
  p.add_argument(       '--plot',      default=''          )
  p.add_argument(       '--dump-json', default=''          )

  opts = p.parse_args()
  if opts.help: p.error()
  return opts

#-------------------------------------------------------------------------
# _pwr_dict_to_plt_dict
#-------------------------------------------------------------------------
# Convert data in pwr_dict into a dictionary for plot. Here we also sums
# up all the dynamic power for muxes. ALl data processing should happen
# here.

def _pwr_dict_to_plt_dict( pwr_dict ):
  plt_dict = {}
  # Create name map
  mul_path = 'dpath/node/mul'
  alu_path = 'dpath/node/alu'
  acc_path = 'dpath/acc_reg'
  q_n_path = 'in_qs__0'
  q_s_path = 'in_qs__1'
  q_w_path = 'in_qs__2'
  q_e_path = 'in_qs__3'
  unsafe_gen_path = 'suppress/unsafe_gen'
  clk_switcher_path = 'clk_switcher'

  sup_pwr  = sum(map(lambda x: pwr_dict[f"suppress/suppressors__{x}"].get_dynamic(), range(4)), 0.0)

  # Append a 0 to the data set to add an empty bar to the plot so that the
  # plot looks better.
  plt_dict[ 'leak'         ] = [ pwr_dict['top'     ].leak_pwr,               0.0 ]
  plt_dict[ 'mul'          ] = [ pwr_dict[ mul_path ].get_dynamic(),          0.0 ]
  plt_dict[ 'alu'          ] = [ pwr_dict[ alu_path ].get_dynamic(),          0.0 ]
  plt_dict[ 'acc'          ] = [ pwr_dict[ acc_path ].get_dynamic(),          0.0 ]
  plt_dict[ 'in_q_n'       ] = [ pwr_dict[ q_n_path ].get_dynamic(),          0.0 ]
  plt_dict[ 'in_q_s'       ] = [ pwr_dict[ q_s_path ].get_dynamic(),          0.0 ]
  plt_dict[ 'in_q_w'       ] = [ pwr_dict[ q_w_path ].get_dynamic(),          0.0 ]
  plt_dict[ 'in_q_e'       ] = [ pwr_dict[ q_e_path ].get_dynamic(),          0.0 ]
  plt_dict[ 'suppress'     ] = [ sup_pwr,                                     0.0 ]
  plt_dict[ 'unsafe_gen'   ] = [ pwr_dict[ unsafe_gen_path ].get_dynamic(),   0.0 ]
  plt_dict[ 'clk_switcher' ] = [ pwr_dict[ clk_switcher_path ].get_dynamic(), 0.0 ]
  plt_dict[ 'muxes'        ] = [ 0.0,                                         0.0 ]
  plt_dict[ 'other'        ] = [ pwr_dict['other'   ].get_dynamic(),          0.0 ]

  for k, v in pwr_dict.items():
    if k.find( 'mux' ) >= 0:
      plt_dict[ 'muxes' ][0] += v.get_dynamic()

  return plt_dict

#-------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------

def main():
  opts = parse_cmdline()

  if opts.help:
    return

  if opts.verbose:
    print( f'Loading search dictionary {opts.search_dict}...' )

  # Parse the search dictionary
  with open( opts.search_dict ) as f:
    search_dict = json.load( f )

  if opts.verbose:
    print( 'Designs to search for are:')
    for path in search_dict:
      print( f'  {path.ljust(12) }' )

    print( f'Opening hierarchy report {opts.report}' )

  # Parse the power hierachy report
  pwr_dict = hier_rpt_to_json( opts.report, search_dict )
  jdict    = pwr_dict_to_json( pwr_dict )
  if opts.dump_json:
    with open( opts.dump_json, 'w' ) as f:
      if opts.verbose: print( f'Writing parsed data to {opts.dump_json}' )
      json.dump( jdict, f, indent=2 )

  if opts.plot:
    if opts.verbose: print( f'Saving stack plot to {opts.plot}' )
    plt_dict = _pwr_dict_to_plt_dict( pwr_dict )
    color_dict = scheme_gen( "tab20", plt_dict )
    plot_stack( plt_dict, color_dict, ylabel='power',outdir=opts.plot )

main()
