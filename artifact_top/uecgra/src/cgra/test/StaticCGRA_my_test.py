import sys
sys.setrecursionlimit( 2000 )

import random
from random import randint

import pytest

from pymtl3 import *
from pymtl3.stdlib.test import TestSrcCL, TestSinkCL
from pymtl3.passes.yosys import TranslationImportPass, ImportConfigs

from .test_utils import json_to_cfgs, to_vcd_cycle_time
from ..enums import CfgMsg as CFG, TileDirection as TD
from ..StaticCGRA import StaticCGRA
from ..ConfigMsg import ConfigMsg

random.seed(0xfaceb00c)
class TestHarness( Component ):

  def construct( s, Type, CfgMsgType, ncols=2, nrows=2, cfg_msgs = [],
                 src_n_msgs=[], src_s_msgs=[], src_w_msgs=[], src_e_msgs=[],
                 sink_n_msgs=[], sink_s_msgs=[], sink_w_msgs=[], sink_e_msgs=[],
                 imms=None, fifo_depth=2, skip_check=False ):

    # Local parameter

    ntiles = nrows * ncols

    # Components

    s.src_n = [ TestSrcCL( Type, src_n_msgs[i] ) for i in range( ncols ) ]
    s.src_s = [ TestSrcCL( Type, src_s_msgs[i] ) for i in range( ncols ) ]
    s.src_w = [ TestSrcCL( Type, src_w_msgs[i] ) for i in range( nrows ) ]
    s.src_e = [ TestSrcCL( Type, src_e_msgs[i] ) for i in range( nrows ) ]

    s.dut = StaticCGRA( Type, CfgMsgType, ncols, nrows, fifo_depth=fifo_depth )

    if not skip_check:
      s.sink_n = [ TestSinkCL( Type, sink_n_msgs[i] ) for i in range( ncols ) ]
      s.sink_s = [ TestSinkCL( Type, sink_s_msgs[i] ) for i in range( ncols ) ]
      s.sink_w = [ TestSinkCL( Type, sink_w_msgs[i] ) for i in range( nrows ) ]
      s.sink_e = [ TestSinkCL( Type, sink_e_msgs[i] ) for i in range( nrows ) ]
    else:
      s.sink_n = [ TestSinkCL( Type, sink_n_msgs[i], cmp_fn=lambda a, b: True ) for i in range( ncols ) ]
      s.sink_s = [ TestSinkCL( Type, sink_s_msgs[i], cmp_fn=lambda a, b: True ) for i in range( ncols ) ]
      s.sink_w = [ TestSinkCL( Type, sink_w_msgs[i], cmp_fn=lambda a, b: True ) for i in range( nrows ) ]
      s.sink_e = [ TestSinkCL( Type, sink_e_msgs[i], cmp_fn=lambda a, b: True ) for i in range( nrows ) ]

    s.cfg_en = InPort( Bits1 )

    # Connect dut to src/sink

    for i in range( ncols ):
      connect( s.src_n[i].send, s.dut.recv_n[i]  )
      connect( s.dut.send_n[i], s.sink_n[i].recv )

      connect( s.src_s[i].send, s.dut.recv_s[i]  )
      connect( s.dut.send_s[i], s.sink_s[i].recv )

    for i in range( nrows ):
      connect( s.src_w[i].send, s.dut.recv_w[i]  )
      connect( s.dut.send_w[i], s.sink_w[i].recv )

      connect( s.src_e[i].send, s.dut.recv_e[i]  )
      connect( s.dut.send_e[i], s.sink_e[i].recv )

    # Configure CGRA

    if not imms:
      imms = [ Type(0) for _ in range( ntiles ) ]

    for i in range( ntiles ):
      connect( s.cfg_en, s.dut.cfg_en[i] )

    @s.update
    def up_configs():
      for i in range( ntiles ):
        s.dut.cfg[i] = cfg_msgs[i]
        s.dut.imm[i] = imms[i]

  def configure( s ):
    s.cfg_en = b1(1)
    s.tick()
    s.cfg_en = b1(0)

  def done( s ):
    src_n_done = all([ x.done() for x in s.src_n ])
    src_s_done = all([ x.done() for x in s.src_s ])
    src_w_done = all([ x.done() for x in s.src_w ])
    src_e_done = all([ x.done() for x in s.src_e ])

    sink_n_done = all([ x.done() for x in s.sink_n ])
    sink_s_done = all([ x.done() for x in s.sink_s ])
    sink_w_done = all([ x.done() for x in s.sink_w ])
    sink_e_done = all([ x.done() for x in s.sink_e ])

    return src_n_done and src_s_done and src_w_done and src_e_done and \
           sink_n_done and sink_s_done and sink_w_done and sink_e_done

  def line_trace( s ):
    return s.dut.line_trace()

def mk_cfg( op, src_a, src_b, dst ):
  cfg = ConfigMsg()
  if op.lower() == 'cp0':
    cfg.func = CFG.CP0
  elif op.lower() == 'cp1':
    cfg.func = CFG.CP1
  elif op.lower() == 'add':
    cfg.func = CFG.ADD
  elif op.lower() == 'sll':
    cfg.func = CFG.SLL
  elif op.lower() == 'srl':
    cfg.func = CFG.SRL
  elif op.lower() == 'and':
    cfg.func = CFG.AND
  elif op.lower() == 'mul':
    cfg.func = CFG.MUL
  elif op.lower() == 'nop':
    cfg.func = CFG.NOP
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
  cfg.src_altbps = CFG.SRC_SELF
  cfg.dst_altbps = CFG.DST_NONE

  return cfg


#-------------------------------------------------------------------------
# Test cases - PyMTL simulation
#-------------------------------------------------------------------------

class StaticCGRA_Tests:
  def test_elaborate( s ):
    dut = StaticCGRA( Bits16, ConfigMsg )
    dut.elaborate()

  def test(s):
    ncols = 2;
    nrows = 2

    # cfg_msgs = [
    #   mk_cfg( 'cp0', 'WEST', 'SELF',  'EAST'  ),
    #   mk_cfg( 'cp0', 'WEST', 'SELF',  'NORTH' ),
    #   mk_cfg( 'cp0', 'WEST', 'SELF',  'EAST'  ),
    #   mk_cfg( 'add', 'WEST', 'SOUTH', 'EAST'  ),
    # ]

    cfg_msgs = json_to_cfgs('cfg_vvadd_2x2.json')
    #cfg_msgs = json_to_cfgs('fiir.json')

    src_n_msgs = [[] for _ in range(2)]
    src_s_msgs = [[] for _ in range(2)]
    src_w_msgs = [
      [b16(14), b16(10)],
      [b16(26), b16(20)],
    ]
    src_e_msgs = [[] for _ in range(2)]

    sink_n_msgs = [[] for _ in range(2)]
    sink_s_msgs = [[] for _ in range(2)]
    sink_w_msgs = [[] for _ in range(2)]
    sink_e_msgs = [
      [],
      [b16(40), b16(30)]
    ]

    th = TestHarness(Bits16, ConfigMsg, ncols, nrows, cfg_msgs,
                     src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                     sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs)
    s.run_sim(2, th)
class StaticCGRA_Trans_Tests( StaticCGRA_Tests ):

  # PyMTL magic clock is 750MHz
  vcd_timescale = "1ps"
  # vcd_cycle_time = 1332

  def run_sim( s, n_iter, th, max_cycles=200, clock_time="1.33", silent_timeout=False, vl_trace=True ):
    print()
    th.elaborate()
    th.dut.yosys_translate_import = True
    th.dut.yosys_import = ImportConfigs(
      vl_trace = vl_trace, vl_Wno_list=['UNOPTFLAT', 'UNSIGNED'],
      vl_trace_timescale  = StaticCGRA_Trans_Tests.vcd_timescale,
      vl_trace_cycle_time = to_vcd_cycle_time(clock_time),
    )
    print(f"Vcd cycle time = {to_vcd_cycle_time(clock_time)}")
    th = TranslationImportPass()( th )
    th.elaborate()
    th.apply( SimulationPass )
    th.sim_reset()
    th.configure()
    ncycles = 0
    th.tick()
    ncycles += 1

    while not th.done() and ncycles < max_cycles:
      th.tick()
      ncycles += 1

    if not silent_timeout:
      assert ncycles < max_cycles

    ncycles = ncycles * (float(clock_time)/1.33)

    print(f"Number of iterations = {n_iter}")
    print(f"Number of nominal cycles = {ncycles}")
    print("Throughput: {} iters/nominal cycle".format(n_iter/float(ncycles)))

