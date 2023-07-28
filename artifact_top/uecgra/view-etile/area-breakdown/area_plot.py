"""
==========================================================================
plt_area_breakdown.py
==========================================================================
Collect area breakdown information from signoff area report.

Author : Yanghui Ou
  Date : Aug 20, 2019

"""
from __future__ import print_function
import argparse
import os
import sys
import re
import json
import numpy as np
import matplotlib.pyplot as plt

from dataclasses import dataclass
from color_scheme import get_tile_breakdown_color_dict

#-------------------------------------------------------------------------
# AreaRecord
#-------------------------------------------------------------------------
# A helper class to hold area information.

@dataclass
class AreaRecord:
  abs_total : float = 0.0

  # Helper function for json conversion
  def to_dict( self ):
    return {
      'abs_total' : self.abs_total,
    }

#-------------------------------------------------------------------------
# _hier_level
#-------------------------------------------------------------------------
# Count the number of leading spaces of a line.

def _hier_level( line, tab_width=2 ):
  line_lst  = line.split()
  return line_lst[1].split('/')[-1], int(line_lst[0])

#-------------------------------------------------------------------------
# _get_total_area
#-------------------------------------------------------------------------
# Extract the total power information.

def _get_total_area( line ):
  line_lst  = line.split()
  area_record = AreaRecord(
    abs_total = float( line_lst[3] ),
  )
  return area_record

#-------------------------------------------------------------------------
# _get_other_area
#-------------------------------------------------------------------------
# Compute other area. This is python3 dependent since it requires the
# dictionary to be ordered.

def _get_other_area( area_dict ):
  sum_abs_total = 0.0

  # FIXME: for area report, conb and non_comb does not add up to total.
  for inst_name, record in area_dict.items():
    if inst_name != 'top':
      sum_abs_total += record.abs_total

  other_abs_total = area_dict[ 'top' ].abs_total - sum_abs_total

  return AreaRecord(
    abs_total = other_abs_total,
  )

#-------------------------------------------------------------------------
# _find_match_item
#-------------------------------------------------------------------------
# Iteratate throught the dictionary and try to find the matching item.

def _find_match_item( line, regex_dict={} ):
  inst_name, level = _hier_level( line )
  line_lst = line.split()
  for compiled_re, hier_lvl in regex_dict.items():
    if compiled_re.match( inst_name ) and level == hier_lvl:
      record = AreaRecord(
        abs_total = float( line_lst[3] ),
      )
      return inst_name, record
  return None

#-------------------------------------------------------------------------
# _area_dict_to_json
#-------------------------------------------------------------------------
# Convert the dictionary of power records into a json dictionary.

def _area_dict_to_json( area_dict ):
  return { inst_name : record.to_dict() for inst_name, record in area_dict.items() }

#-------------------------------------------------------------------------
# _hier_rpt_to_json
#-------------------------------------------------------------------------
# Extract power information from hierachy report and dump into a json.

def _hier_rpt_to_json( rpt_path, items_to_find={} ):

  # Pre-process the dictionary by compiling the regex
  regex_dict = {}
  for expr, hier_lvl in items_to_find.items():
    compiled_re = re.compile( expr )
    regex_dict[ compiled_re ] = hier_lvl

  # Extract area information from the report
  area_dict = {}
  with open( rpt_path, 'r' ) as rpt:
    line = rpt.readline()

    # Get design name
    while line and not line.startswith( '0' ):
      line = rpt.readline()
    design_name = line.split()[1]

    # Get total area information
    area_dict[ 'top' ] = _get_total_area( line )
    line = rpt.readline()

    while line:
      res = _find_match_item( line, regex_dict )
      if res:
        inst_name = res[0]; record = res[1]
        area_dict[ inst_name ] = record
      line = rpt.readline()

    area_dict[ 'other' ] = _get_other_area( area_dict )
    return _area_dict_to_json( area_dict )

#-------------------------------------------------------------------------
# plot_stack
#-------------------------------------------------------------------------

def parse_cmdline():
  ...

#-------------------------------------------------------------------------
# plot_stack
#-------------------------------------------------------------------------
# Creates a stacked bar plot based on input json files.

def plot_stack( jpath={} ):

  nbars = 2
  with open( jpath ) as f:
    data = json.load( f )

  print( data )

  # Add a dummy column to look better
  bar_names  = [ 'Elastic Tile', '' ]
  mul_area   = [ data['mul'     ]['abs_total'], 0.0 ]
  alu_area   = [ data['alu'     ]['abs_total'], 0.0 ]
  acc_area   = [ data['acc_reg' ]['abs_total'], 0.0 ]
  q_n_area   = [ data['in_q_n'  ]['abs_total'], 0.0 ]
  q_s_area   = [ data['in_q_s'  ]['abs_total'], 0.0 ]
  q_w_area   = [ data['in_q_w'  ]['abs_total'], 0.0 ]
  q_e_area   = [ data['in_q_e'  ]['abs_total'], 0.0 ]
  other_area = [ data['other'   ]['abs_total'], 0.0 ]

  bar_names  = np.array( bar_names )
  mul_area   = np.array( mul_area   )
  alu_area   = np.array( alu_area   )
  q_n_area   = np.array( q_n_area   )
  q_s_area   = np.array( q_s_area   )
  q_w_area   = np.array( q_w_area   )
  q_e_area   = np.array( q_e_area   )
  other_area = np.array( other_area )

  ind = np.arange( nbars )
  width = 0.1

  fig = plt.figure()

  cdict = get_tile_breakdown_color_dict("tab20")

  bottom_mul = [ 0, 0 ]
  bar_mul = plt.bar( ind, mul_area, width, bottom=bottom_mul,
      color=cdict['mul'], edgecolor=cdict['mul'])

  bottom_alu = bottom_mul + mul_area
  bar_alu = plt.bar( ind, alu_area, width, bottom=bottom_alu,
      color=cdict['alu'], edgecolor=cdict['alu'])

  bottom_acc = bottom_alu + alu_area
  bar_acc = plt.bar( ind, acc_area, width, bottom=bottom_acc,
      color=cdict['acc'], edgecolor=cdict['acc'])

  bottom_q_n = bottom_acc + acc_area
  bar_q_n = plt.bar( ind, q_n_area, width, bottom=bottom_q_n,
      color=cdict['in_q_n'], edgecolor=cdict['in_q_n'])

  bottom_q_s = bottom_q_n + q_n_area
  bar_q_s = plt.bar( ind, q_s_area, width, bottom=bottom_q_s,
      color=cdict['in_q_s'], edgecolor=cdict['in_q_s'])

  bottom_q_w = bottom_q_s + q_s_area
  bar_q_w = plt.bar( ind, q_w_area, width, bottom=bottom_q_w,
      color=cdict['in_q_w'], edgecolor=cdict['in_q_w'])

  bottom_q_e = bottom_q_w + q_w_area
  bar_q_e = plt.bar( ind, q_e_area, width, bottom=bottom_q_e,
      color=cdict['in_q_e'], edgecolor=cdict['in_q_e'])

  bottom_other = bottom_q_e + q_e_area
  bar_other = plt.bar( ind, other_area, width, bottom=bottom_other,
      color=cdict['other'], edgecolor=cdict['other'])

  plt.ylabel( 'area' )
  plt.xticks( ind, bar_names )
  plt.legend(
    ( bar_mul[0], bar_alu[0], bar_acc[0], bar_q_n[0], bar_q_s[0], bar_q_w[0], bar_q_e[0], bar_other[0] )[::-1],
    ( 'mul',      'alu',      'acc',      'in_q_n',      'in_q_s',      'in_q_w',      'in_q_e',      'other' )[::-1]
  )
  fig.savefig( 'area_stack.pdf' )

if __name__ == '__main__':

  search_dict = {
    'in_q_*'     : 1,
    'acc_reg'    : 2,
    'alu'        : 3,
    'mul'        : 3,
  }

  jdict = _hier_rpt_to_json( f'inputs/signoff.area.rpt', search_dict )
  with open( 'area_breakdown.json', 'w' ) as f:
    json.dump( jdict, f, indent=2 )

  plot_stack( 'area_breakdown.json' )
