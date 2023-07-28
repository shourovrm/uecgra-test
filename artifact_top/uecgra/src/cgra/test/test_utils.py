"""
==========================================================================
test_utils.py
==========================================================================
Utility function for the ue-cgra project.

Author : Yanghui Ou
  Date : Aug 17, 2019

"""
import os
import sys
import json

from pymtl3 import *

from cgra.ConfigMsg import ConfigMsg
from cgra.ConfigMsg_RGALS import ConfigMsg_RGALS
from cgra.enums import CfgMsg as CFG
from clock.enums import CLK_FAST, CLK_SLOW, CLK_NOMINAL

#-------------------------------------------------------------------------
# mk_cfg
#-------------------------------------------------------------------------
# Helper function for making configuration message. For now we don't
# consider bypass at the moment.

_op_dict = {
  'cp0' : CFG.CP0,
  'cp1' : CFG.CP1,
  'add' : CFG.ADD,
  'sub' : CFG.SUB,
  'sll' : CFG.SLL,
  'srl' : CFG.SRL,
  'and' : CFG.AND,
  'or'  : CFG.OR,
  'xor' : CFG.XOR,
  'eq'  : CFG.EQ,
  'ne'  : CFG.NE,
  'gt'  : CFG.GT,
  'geq' : CFG.GEQ,
  'lt'  : CFG.LT,
  'leq' : CFG.LEQ,
  'mul' : CFG.MUL,
  'phi' : CFG.PHI,
  'nop' : CFG.NOP,
}

_src_dict = {
  'n'    : CFG.SRC_NORTH,
  's'    : CFG.SRC_SOUTH,
  'w'    : CFG.SRC_WEST,
  'e'    : CFG.SRC_EAST,
  'self' : CFG.SRC_SELF,
}

_dst_dict = {
  'n'    : CFG.DST_NORTH,
  's'    : CFG.DST_SOUTH,
  'w'    : CFG.DST_WEST,
  'e'    : CFG.DST_EAST,
  'self' : CFG.DST_SELF,
  'none' : CFG.DST_NONE,
}

_clk_dict = {
  'sprint'  : CLK_FAST,
  'rest'    : CLK_SLOW,
  'nominal' : CLK_NOMINAL,
}

def mk_cfg( op, src_a, src_b, dsts,
            bps_src='self', bps_dsts=['none'],
            bps_alt_src='self', bps_alt_dsts=['none'],
            dvfs='nominal', is_sync=True ):
  if is_sync:
    cfg = ConfigMsg()
  else:
    cfg = ConfigMsg_RGALS()
    assert dvfs.lower() in _clk_dict
    cfg.clk_self = _clk_dict[ dvfs.lower() ]

  cfg.opcode = CFG.OP_Q_TYPE

  assert op.lower() in _op_dict
  cfg.func = _op_dict[ op.lower() ]

  assert src_a.lower() in _src_dict
  cfg.src_opd_a = _src_dict[ src_a.lower() ]

  assert src_b.lower() in _src_dict
  cfg.src_opd_b = _src_dict[ src_b.lower() ]

  for dst in dsts:
    assert dst.lower() in _dst_dict
    cfg.dst_compute |= _dst_dict[ dst.lower() ]

  assert bps_src.lower() in _src_dict
  cfg.src_bypass = _src_dict[ bps_src.lower() ]

  for dst in bps_dsts:
    assert dst.lower() in _dst_dict
    cfg.dst_bypass |= _dst_dict[ dst.lower() ]

  assert bps_alt_src.lower() in _src_dict
  cfg.src_altbps = _src_dict[ bps_alt_src.lower() ]

  for dst in bps_alt_dsts:
    assert dst.lower() in _dst_dict
    cfg.dst_altbps |= _dst_dict[ dst.lower() ]

  return cfg

# NOTE: we don't support dst to be a list for branches
def mk_br_cfg( src_data, src_bool, dst_true, dst_false,
               bps_src='self', bps_dsts=['none'],
               bps_alt_src='self', bps_alt_dsts=['none'],
               dvfs='nominal', is_sync=True ):
  if is_sync:
    cfg = ConfigMsg()
  else:
    cfg = ConfigMsg_RGALS()
    assert dvfs.lower() in _clk_dict
    cfg.clk_self = _clk_dict[ dvfs.lower() ]

  cfg.opcode = CFG.OP_B_TYPE

  assert src_data.lower() in _src_dict
  cfg.src_opd_a = _src_dict[ src_data.lower() ]

  assert src_bool.lower() in _src_dict
  cfg.src_opd_b = _src_dict[ src_bool.lower() ]

  assert dst_true.lower() in _dst_dict
  cfg.dst_compute = _dst_dict[ dst_true.lower() ]

  assert dst_false.lower() in _dst_dict
  cfg.func = _dst_dict[ dst_false.lower() ]

  assert bps_src.lower() in _src_dict
  cfg.src_bypass = _src_dict[ bps_src.lower() ]

  for dst in bps_dsts:
    assert dst.lower() in _dst_dict
    cfg.dst_bypass |= _dst_dict[ dst.lower() ]

  assert bps_alt_src.lower() in _src_dict
  cfg.src_altbps = _src_dict[ bps_alt_src.lower() ]

  for dst in bps_alt_dsts:
    assert dst.lower() in _dst_dict
    cfg.dst_altbps |= _dst_dict[ dst.lower() ]

  return cfg

#-------------------------------------------------------------------------
# json_to_cfgs
#-------------------------------------------------------------------------
# Decode a json file to a list of configs.

def json_to_cfgs( fpath, ncols=2, nrows=2, is_sync=True ):

  ntiles = ncols * nrows
  cfgs = [ mk_cfg(
    'nop', 'self', 'self', ['self'], 'self', ['none'],
    'self', ['none'], 'nominal', is_sync )
    for _ in range(ntiles) ]

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )
  abs_path = os.path.join( this_dir, fpath )

  if not os.path.isfile( abs_path ):
    abs_path = os.path.join( this_dir, "cfgs/" + fpath )

  with open( abs_path, 'r' ) as jf:
    data = json.load( jf )
    for cfg in data:
      tid = cfg['y'] * ncols + cfg['x']

      if 'bps_src' in cfg: bps_src = cfg['bps_src']
      else:                bps_src = 'self'
      if 'bps_dst' in cfg: bps_dst = cfg['bps_dst']
      else:                bps_dst = [ 'none' ]

      if 'bps_alt_src' in cfg: bps_alt_src = cfg['bps_alt_src']
      else:                    bps_alt_src = 'self'
      if 'bps_alt_dst' in cfg: bps_alt_dst = cfg['bps_alt_dst']
      else:                    bps_alt_dst = [ 'none' ]

      assert 'op' in cfg
      if cfg[ 'op' ].lower() == 'br':
        cfgs[ tid ] = mk_br_cfg(
          cfg['src_data' ],
          cfg['src_bool' ],
          cfg['dst_true' ],
          cfg['dst_false'],
          bps_src,
          bps_dst,
          bps_alt_src,
          bps_alt_dst,
          cfg['dvfs'],
          is_sync,
        )
      else:
        cfgs[ tid ] = mk_cfg(
          cfg['op'],
          cfg['src_a'],
          cfg['src_b'],
          cfg['dst'],
          bps_src,
          bps_dst,
          bps_alt_src,
          bps_alt_dst,
          cfg['dvfs'],
          is_sync,
        )

  return cfgs

def test_noob():
  cfgs = json_to_cfgs( 'fir.json', 8, 8 )
  for i in range( 64 ):
    print( f'{i:2}: {cfgs[i]}')

def to_vcd_cycle_time(clock_time):
    t = int(float(clock_time)*1000.0)
    if t % 2 != 0:
        t += 1
    return t
