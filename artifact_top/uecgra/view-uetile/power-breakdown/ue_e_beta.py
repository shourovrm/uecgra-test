#=========================================================================
# ue_e_beta.py
#=========================================================================
# Calculate the beta parameter for each operation
#
# Author : Peitian Pan
# Date   : Sep 2, 2019

import argparse
import sys 
import json

from utils import *
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
  p.add_argument(       '--e-prefix',  default='.'                  )
  p.add_argument(       '--e-dict',    default=''                   )
  p.add_argument(       '--ue-prefix', default='.'                  )
  p.add_argument(       '--ue-dict',   default=''                   )
  p.add_argument(       '--factor',    default=1, type=float        )

  opts = p.parse_args()
  if opts.help: p.error()
  return opts

#-------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------

def main():
  opts = parse_cmdline()

  if opts.help: return

  beta = {}

  # Parse the UE dictionary
  with open( opts.ue_prefix + '/' + opts.ue_dict ) as f:
    ue_dict = json.load( f )

  # Parse the E dictionary
  with open( opts.e_prefix + '/' + opts.e_dict ) as f:
    e_dict = json.load( f )

  # Calculate Beta parameter for each op
  for key, val in ue_dict.items():
    assert key in e_dict

    with open( opts.ue_prefix + '/' + val ) as f:
      data = json.load( f )
      ue_power = data['top']['total_pwr']

    with open( opts.e_prefix + '/' + e_dict[key] ) as f:
      data = json.load( f )
      e_power = data['top']['total_pwr']

    beta[key] = (ue_power/e_power)*opts.factor

  with open( "ue_e_beta.json", "w" ) as f:
    json.dump( beta, f )

  print(beta)

main()
