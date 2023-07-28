"""
==========================================================================
utils.py
==========================================================================
Utility function for power breakdown.

Author : Yanghui Ou
  Date : Aug 18, 2019

"""
import re
import json
from dataclasses import dataclass

#-------------------------------------------------------------------------
# PowerRecord
#-------------------------------------------------------------------------
# A helper class to hold power information.

@dataclass
class PowerRecord:
  int_pwr    : float = 0.0
  switch_pwr : float = 0.0
  leak_pwr   : float = 0.0
  total_pwr  : float = 0.0
  percentage : float = 0.0

  # Helper function for json conversion
  def to_dict( self ):
    return {
      'int_pwr'    : self.int_pwr,
      'switch_pwr' : self.switch_pwr,
      'leak_pwr'   : self.leak_pwr,
      'total_pwr'  : self.total_pwr,
      'percentage' : self.percentage,
    }

  def get_dynamic( self ):
    return self.int_pwr + self.switch_pwr

#-------------------------------------------------------------------------
# _hier_level
#-------------------------------------------------------------------------
# Count the number of leading spaces of a line.
# TODO: assert mod == 0?

def _hier_level( line, tab_width=2 ):
  return  ( len( line ) - len( line.lstrip() ) ) // tab_width

#-------------------------------------------------------------------------
# _get_total_power
#-------------------------------------------------------------------------
# Extract the total power information.

def _get_total_power( line ):
  line_lst  = line.split()
  inst_name = line_lst[0]
  pwr_record = PowerRecord(
    int_pwr    = float( line_lst[1] ),
    switch_pwr = float( line_lst[2] ),
    leak_pwr   = float( line_lst[3] ),
    total_pwr  = float( line_lst[4] ),
    percentage = float( line_lst[5] ),
  )
  return inst_name, pwr_record

#-------------------------------------------------------------------------
# _get_other_power
#-------------------------------------------------------------------------
# Compute other power. This is python3 dependent since it requires the
# dictionary to be ordered.

def _get_other_power( pwr_dict ):
  sum_int    = 0.0
  sum_switch = 0.0
  sum_leak   = 0.0
  sum_total  = 0.0
  sum_pcent  = 0.0

  for inst_name, record in pwr_dict.items():
    if inst_name != 'top':
      sum_int    += record.int_pwr
      sum_switch += record.switch_pwr
      sum_leak   += record.leak_pwr
      sum_total  += record.total_pwr
      sum_pcent  += record.percentage

  other_int    = pwr_dict[ 'top' ].int_pwr    - sum_int
  other_switch = pwr_dict[ 'top' ].switch_pwr - sum_switch
  other_leak   = pwr_dict[ 'top' ].leak_pwr   - sum_leak
  other_total  = pwr_dict[ 'top' ].total_pwr  - sum_total
  other_pcent  = pwr_dict[ 'top' ].percentage - sum_pcent

  return PowerRecord(
    int_pwr    = other_int,
    switch_pwr = other_switch,
    leak_pwr   = other_leak,
    total_pwr  = other_total,
    percentage = other_pcent,
  )

#-------------------------------------------------------------------------
# _get_inst_name
#-------------------------------------------------------------------------
# Get the instance name of a line

def _get_inst_name( line ):
  return line.split()[0]

#-------------------------------------------------------------------------
# _find_match_item
#-------------------------------------------------------------------------
# Iteratate throught the dictionary and try to find the matching item.

def _find_match_item( line, cur_dir, regex_lst=[] ):
  line_lst = line.split()
  inst_name = '/'.join( cur_dir )
  for re_path in regex_lst:
    # If current design has the same hierachy level, try match the re
    matched = False
    if len( cur_dir ) == len( re_path ):
      matched = True
      for name, regex in zip( cur_dir, re_path ):
        if not regex.match( name ):
          matched = False
          break

    if matched:
      # print( f'Found match : {inst_name}' )
      record = PowerRecord(
        int_pwr    = float( line_lst[2] ),
        switch_pwr = float( line_lst[3] ),
        leak_pwr   = float( line_lst[4] ),
        total_pwr  = float( line_lst[5] ),
        percentage = float( line_lst[6] ),
      )
      return inst_name, record

  return None

#-------------------------------------------------------------------------
# pwr_dict_to_json
#-------------------------------------------------------------------------
# Convert the dictionary of power records into a json dictionary.

def pwr_dict_to_json( pwr_dict ):
  return { inst_name : record.to_dict() for inst_name, record in pwr_dict.items() }

#-------------------------------------------------------------------------
# hier_rpt_to_json
#-------------------------------------------------------------------------
# Extract power information from hierachy report and dump into a json.

def hier_rpt_to_json( rpt_path, items_to_find=[] ):

  # Pre-process the dictionary by compiling the regex
  regex_lst = []
  for expr in items_to_find:
    re_path = [ re.compile( name ) for name in expr.split( '/' ) ]
    regex_lst.append( re_path )

  # Extract power information from the report
  pwr_dict = {}
  with open( rpt_path, 'r' ) as rpt:
    line = rpt.readline()

    # Adavance to the actual data region
    while line and not line.startswith( 'Hierarchy' ):
      line = rpt.readline()
    line = rpt.readline()
    line = rpt.readline()

    # Get total power information
    top_name, top_pwr = _get_total_power( line )
    pwr_dict[ 'top' ] = top_pwr
    line = rpt.readline()

    cur_dir  = []
    prev_lvl = 0
    while line and line.startswith( ' ' ):

      cur_lvl = _hier_level( line )
      # Entering new directory
      if cur_lvl > prev_lvl:
        assert cur_lvl - prev_lvl == 1
        cur_dir.append( _get_inst_name( line ) )

      # Jump back to previous directory
      elif cur_lvl < prev_lvl:
        for i in range( prev_lvl - cur_lvl + 1 ):
          cur_dir.pop()
        cur_dir.append( _get_inst_name( line ) )

      # Same hier level, change design name
      else:
        cur_dir.pop()
        cur_dir.append( _get_inst_name( line ) )

      # print( f'{prev_lvl},{cur_lvl}, {cur_dir}' )

      res = _find_match_item( line, cur_dir, regex_lst )
      if res:
        inst_name = res[0]; record = res[1]
        pwr_dict[ inst_name ] = record

      line = rpt.readline()
      prev_lvl = cur_lvl

    pwr_dict[ 'other' ] = _get_other_power( pwr_dict )
    return pwr_dict

if __name__ == '__main__':
  with open( 'search_list.json' ) as f:
    search_lst = json.load( f )
  hier_rpt_to_json( 'Tile.pwr.hier.rpt', search_lst )
