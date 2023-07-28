#=========================================================================
# json_utils.py
#=========================================================================
# Utility functions that parse configs and clock selections from an input
# json file.
#
# Author : Peitian Pan, Yanghui Ou
# Date   : Aug 17, 2019

import json

from cgra.ConfigMsg import ConfigMsg
from cgra.enums import CfgMsg as CFG

#-------------------------------------------------------------------------
# mk_cfg
#-------------------------------------------------------------------------
# Helper function for making configuration message. For now we don't
# consider bypass at the moment.

north = 0
south = 1
west  = 2
east  = 3
self  = 4
none  = 5

def mk_cfg( op, src_a, src_b, dst ):
  cfg = ConfigMsg()
  if op.lower() == 'cp0':
    cfg.opcode = CFG.CP0
  elif op.lower() == 'cp1':
    cfg.opcode = CFG.CP1
  elif op.lower() == 'add':
    cfg.opcode = CFG.ADD
  elif op.lower() == 'sll':
    cfg.opcode = CFG.SLL
  elif op.lower() == 'srl':
    cfg.opcode = CFG.SRL
  elif op.lower() == 'and':
    cfg.opcode = CFG.AND
  elif op.lower() == 'mul':
    cfg.opcode = CFG.MUL
  elif op.lower() == 'nop':
    cfg.opcode = CFG.NOP
  else:
    raise AssertionError

  if src_a.lower() == 'north':
    cfg.src_opd_a = CFG.SRC_NORTH
  elif src_a.lower() == 'south':
    cfg.src_opd_a = CFG.SRC_SOUTH
  elif src_a.lower() == 'west':
    cfg.src_opd_a = CFG.SRC_WEST
  elif src_a.lower() == 'east':
    cfg.src_opd_a = CFG.SRC_EAST
  elif src_a.lower() == 'self':
    cfg.src_opd_a = CFG.SRC_SELF
  else:
    raise AssertionError

  if src_b.lower() == 'north':
    cfg.src_opd_b = CFG.SRC_NORTH
  elif src_b.lower() == 'south':
    cfg.src_opd_b = CFG.SRC_SOUTH
  elif src_b.lower() == 'west':
    cfg.src_opd_b = CFG.SRC_WEST
  elif src_b.lower() == 'east':
    cfg.src_opd_b = CFG.SRC_EAST
  elif src_b.lower() == 'self':
    cfg.src_opd_b = CFG.SRC_SELF
  else:
    raise AssertionError

  if dst.lower() == 'north':
    cfg.dst_compute = CFG.DST_NORTH
  elif dst.lower() == 'south':
    cfg.dst_compute = CFG.DST_SOUTH
  elif dst.lower() == 'west':
    cfg.dst_compute = CFG.DST_WEST
  elif dst.lower() == 'east':
    cfg.dst_compute = CFG.DST_EAST
  elif dst.lower() == 'self':
    cfg.dst_compute = CFG.DST_SELF
  else:
    raise AssertionError

  cfg.src_bypass = CFG.SRC_SELF
  cfg.dst_bypass = CFG.DST_NONE

  return cfg


def parse_cfgs_from_json( in_file ):
  """Return a list of config messages to be passed to CGRA tiles."""
  with open(in_file) as config_file:
    cfgs = json.load(config_file)
    nrows, ncols = max(t['y'] for t in cfgs)+1, max(t['x'] for t in cfgs)+1
    ntiles = nrows * ncols

    # Initialize all cfg messages as `NOP`
    cfg_msgs = [mk_cfg('nop', 'self', 'self', 'self') for _ in range(ntiles)]

    # Overwrite non-nop configurations
    for cfg in cfgs:
      cfg_msgs[ncols * cfg['y'] + cfg['x']] = \
          mk_cfg(cfg['op'], cfg['src_a'], cfg['src_b'], cfg['dst'])

    return cfg_msgs


def parse_clks_from_json( in_file ):
  """Return a list of clk-selection messages to be passed to CGRA tiles."""
  with open(in_file) as clksel_file:
    clks = json.load(clksel_file)
    nrows, ncols = max(t['y'] for t in clks)+1, max(t['x'] for t in clks)+1
    ntiles = nrows * ncols

    # Initialize all clock selections to the nominal clock
    clk_msgs = [2 for _ in range(ntiles)]

    # Overwrite non-nominal configurations
    for clk in clks:
      clk_msgs[ncols * clk['y'] + clk['x']] = \
          0 if clk['dvfs'] == 'fast' else 1 if clk['dvfs'] == 'slow' else 2

    return clk_msgs
