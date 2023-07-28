"""
==========================================================================
StaticCGRA_test.py
==========================================================================
Test cases for the elastic static CGRA.

Author : Yanghui Ou
  Date : August 10, 2019

"""
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

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

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

#-------------------------------------------------------------------------
# mk_cfg
#-------------------------------------------------------------------------
# Helper function for making configuration message. For now we don't
# consider bypass at the moment.

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

  def run_sim( s, n_iter, th, max_cycles=100, clock_time="1.33", vl_trace=True ):
    print()
    th.elaborate()
    th.apply( SimulationPass )
    th.sim_reset()
    th.configure()
    ncycles = 0
    print( f'{ncycles:3}:{th.line_trace()}' )
    th.tick()
    ncycles += 1

    while not th.done() and ncycles < max_cycles:
      print( f'{ncycles:3}:{th.line_trace()}' )
      th.tick()
      ncycles += 1

    print( f'{ncycles:3}:{th.line_trace()}' )
    assert ncycles < max_cycles

  def test_elaborate( s ):
    dut = StaticCGRA( Bits16, ConfigMsg )
    dut.elaborate()

  def test_vvadd_2x2( s ):
    ncols = 2; nrows = 2

    # cfg_msgs = [
    #   mk_cfg( 'cp0', 'WEST', 'SELF',  'EAST'  ),
    #   mk_cfg( 'cp0', 'WEST', 'SELF',  'NORTH' ),
    #   mk_cfg( 'cp0', 'WEST', 'SELF',  'EAST'  ),
    #   mk_cfg( 'add', 'WEST', 'SOUTH', 'EAST'  ),
    # ]

    cfg_msgs = json_to_cfgs( 'fft.json' )

    src_n_msgs = [ [] for _ in range(2) ]
    src_s_msgs = [ [] for _ in range(2) ]
    src_w_msgs = [
      [ b16(1), b16(10) ],
      [ b16(2), b16(20) ],
    ]
    src_e_msgs = [ [] for _ in range(2) ]

    sink_n_msgs = [ [] for _ in range(2) ]
    sink_s_msgs = [ [] for _ in range(2) ]
    sink_w_msgs = [ [] for _ in range(2) ]
    sink_e_msgs = [
      [],
      [ b16(3), b16(30) ]
    ]

    th = TestHarness( Bits16, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs )
    s.run_sim( 2, th )

  def test_1d_conv_2x6( s ):
    ncols = 6; nrows = 2

    cfg_msgs = [
      mk_cfg( 'CP0', 'SELF',  'SELF',  'SELF'  ), # 0  - do nothing
      mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ), # 1  - pass data
      mk_cfg( 'CP0', 'WEST',  'SELF',  'EAST'  ), # 2  - pass data
      mk_cfg( 'ADD', 'WEST',  'NORTH', 'EAST'  ), # 3  - add
      mk_cfg( 'CP0', 'WEST',  'SELF',  'EAST'  ), # 4  - pass data
      mk_cfg( 'ADD', 'WEST',  'NORTH', 'EAST'  ), # 5  - add - exit point
      mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ), # 6  - pass data
      mk_cfg( 'MUL', 'WEST',  'NORTH', 'SOUTH' ), # 7  - mul
      mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ), # 8  - pass data
      mk_cfg( 'MUL', 'WEST',  'NORTH', 'SOUTH' ), # 9  - mul
      mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ), # 10 - pass data
      mk_cfg( 'MUL', 'WEST',  'NORTH', 'SOUTH' ), # 11 - mul
    ]

    src_n_msgs = [
      [ b16(1), b16(2) ], # a0
      [ b16(1), b16(1) ], # b0
      [ b16(2), b16(3) ], # a1
      [ b16(1), b16(1) ], # b1
      [ b16(3), b16(4) ], # a2
      [ b16(1), b16(1) ], # b2
    ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [
      [ b16(6), b16(9) ],
      [ ]
    ]

    th = TestHarness( Bits16, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs )
    th.set_param( 'top.dut.construct', mul_ncycles=0 )
    s.run_sim( 2, th )

  def test_1d_conv_8x8( s ):
    ncols = 8; nrows = 8
    ntiles = ncols * nrows

    # By default, configured to do nothing
    cfg_msgs = [  mk_cfg( 'nop', 'self', 'self', 'self' ) for _ in range(ntiles) ]

    # Configure used tiles
    cfg_msgs[49] = mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ) # pass data
    cfg_msgs[50] = mk_cfg( 'CP0', 'WEST',  'SELF',  'EAST'  ) # pass data
    cfg_msgs[51] = mk_cfg( 'ADD', 'WEST',  'NORTH', 'EAST'  ) # add
    cfg_msgs[52] = mk_cfg( 'CP0', 'WEST',  'SELF',  'EAST'  ) # pass data
    cfg_msgs[53] = mk_cfg( 'ADD', 'WEST',  'NORTH', 'EAST'  ) # add - exit point
    cfg_msgs[54] = mk_cfg( 'CP0', 'WEST',  'SELF',  'EAST'  ) # pass data
    cfg_msgs[55] = mk_cfg( 'CP0', 'WEST',  'SELF',  'EAST'  ) # pass data

    cfg_msgs[56] = mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ) # pass data
    cfg_msgs[57] = mk_cfg( 'MUL', 'WEST',  'NORTH', 'SOUTH' ) # mul
    cfg_msgs[58] = mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ) # pass data
    cfg_msgs[59] = mk_cfg( 'MUL', 'WEST',  'NORTH', 'SOUTH' ) # mul
    cfg_msgs[60] = mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ) # pass data
    cfg_msgs[61] = mk_cfg( 'MUL', 'WEST',  'NORTH', 'SOUTH' ) # mul

    src_n_msgs = [
      [ b16(1), b16(2) ] * 50 , # a0
      [ b16(1), b16(1) ] * 50 , # b0
      [ b16(2), b16(3) ] * 50 , # a1
      [ b16(1), b16(1) ] * 50 , # b1
      [ b16(3), b16(4) ] * 50 , # a2
      [ b16(1), b16(1) ] * 50 , # b2
      [],
      [],
    ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [
      [],
      [],
      [],
      [],
      [],
      [],
      [ b16(6), b16(9) ] * 50,
      []
    ]

    th = TestHarness( Bits16, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs )
    s.run_sim( 100, th, max_cycles=500 )

  def test_32b_1d_conv_8x8( s ):
    ncols = 8; nrows = 8
    ntiles = ncols * nrows
    nmsgs = 100

    # By default, configured to do nothing
    cfg_msgs = [  mk_cfg( 'nop', 'self', 'self', 'self' ) for _ in range(ntiles) ]

    # Configure used tiles
    cfg_msgs[49] = mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ) # pass data
    cfg_msgs[50] = mk_cfg( 'CP0', 'WEST',  'SELF',  'EAST'  ) # pass data
    cfg_msgs[51] = mk_cfg( 'ADD', 'WEST',  'NORTH', 'EAST'  ) # add
    cfg_msgs[52] = mk_cfg( 'CP0', 'WEST',  'SELF',  'EAST'  ) # pass data
    cfg_msgs[53] = mk_cfg( 'ADD', 'WEST',  'NORTH', 'EAST'  ) # add - exit point
    cfg_msgs[54] = mk_cfg( 'CP0', 'WEST',  'SELF',  'EAST'  ) # pass data
    cfg_msgs[55] = mk_cfg( 'CP0', 'WEST',  'SELF',  'EAST'  ) # pass data

    cfg_msgs[56] = mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ) # pass data
    cfg_msgs[57] = mk_cfg( 'MUL', 'WEST',  'NORTH', 'SOUTH' ) # mul
    cfg_msgs[58] = mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ) # pass data
    cfg_msgs[59] = mk_cfg( 'MUL', 'WEST',  'NORTH', 'SOUTH' ) # mul
    cfg_msgs[60] = mk_cfg( 'CP0', 'NORTH', 'SELF',  'EAST'  ) # pass data
    cfg_msgs[61] = mk_cfg( 'MUL', 'WEST',  'NORTH', 'SOUTH' ) # mul

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for _ in range( nmsgs ):
      a0 = b32( randint(0, 2**32-1) )
      a1 = b32( randint(0, 2**32-1) )
      a2 = b32( randint(0, 2**32-1) )
      b0 = b32( randint(0, 2**32-1) )
      b1 = b32( randint(0, 2**32-1) )
      b2 = b32( randint(0, 2**32-1) )
      res = a0*b0 + a1*b1 + a2*b2

      src_n_msgs[0].append( a0 )
      src_n_msgs[1].append( b0 )
      src_n_msgs[2].append( a1 )
      src_n_msgs[3].append( b1 )
      src_n_msgs[4].append( a2 )
      src_n_msgs[5].append( b2 )
      sink_e_msgs[6].append( res )

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs )
    s.run_sim( nmsgs, th, max_cycles=nmsgs+500 )

  def test_fir( s, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 100
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( 'fir.json', ncols, nrows )
    imms = [ b32(0) for _ in range( ntiles ) ]
    imms[35] = b32(1)
    imms[27] = b32(niter)

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter ):
      src_s_msgs[1].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[2].append( b32(randint(0, 2**32-1)) )

    sink_n_msgs[5].append( b32(sum(map(lambda x: x[0]*x[1], zip(src_s_msgs[1], src_s_msgs[2])))) )

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms )
    s.run_sim( niter, th, max_cycles=10*niter, clock_time=clock_time )

  def test_alt_fir( s, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 10
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( 'fir_alt.json', ncols, nrows )
    imms = [ b32(0) for _ in range( ntiles ) ]
    imms[13] = b32(1)
    imms[20] = b32(1)
    imms[28] = b32(1)
    imms[36] = b32(niter-1)

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter ):
      src_s_msgs[4].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[5].append( b32(randint(0, 2**32-1)) )

    sink_n_msgs[2].append( b32(sum(map(lambda x: x[0]*x[1], zip(src_s_msgs[4], src_s_msgs[5])))) )

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms )
    s.run_sim( niter, th, max_cycles=10*niter, clock_time=clock_time )

  def test_latnrm( s, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 100
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( 'latnrm.json', ncols, nrows )
    imms = [ b32(0) for _ in range( ntiles ) ]

    imms[11] = b32(42)
    imms[12] = b32(0)
    imms[17] = b32(1)
    imms[19] = b32(1)
    imms[20] = b32(0)
    imms[21] = b32(42)
    imms[27] = b32(1)
    imms[28] = b32(0)
    imms[29] = b32(42)
    imms[36] = b32(10000)
    imms[44] = b32(1)
    imms[45] = b32(niter)

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter ):
      src_s_msgs[1].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[2].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[4].append( b32(randint(0, 2**32-1)) )

    sink_n_msgs[4] = [b32(0) for _ in range(niter)]

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, skip_check=True )
    s.run_sim( niter, th, max_cycles=50*niter, clock_time=clock_time )

  def test_bf( s, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 32
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( 'bf.json', ncols, nrows )
    imms = [ b32(0) for _ in range( ntiles ) ]

    imms[4] = b32(1)
    imms[12] = b32(0)
    imms[13] = b32(1)
    imms[15] = b32(0)
    imms[20] = b32(-1)
    imms[26] = b32(4)
    imms[27] = b32(1)
    imms[28] = b32(10000)
    imms[29] = b32(-1)
    imms[34] = b32(niter-1)
    imms[35] = b32(-1)
    imms[36] = b32(1)
    imms[37] = b32(0)
    imms[38] = b32(1)
    imms[42] = b32(1)
    imms[43] = b32(0)
    imms[44] = b32(1)
    imms[50] = b32(1)
    imms[51] = b32(0)
    imms[52] = b32(-1)

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter ):
      src_s_msgs[1].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[2].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[3].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[5].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[6].append( b32(randint(0, 2**32-1)) )
      # src_s_msgs[1].append( b32((1<<8) | i) )
      # src_s_msgs[2].append( b32((2<<8) | i) )
      # src_s_msgs[3].append( b32((3<<8) | i) )
      # src_s_msgs[5].append( b32((5<<8) | i) )
      # src_s_msgs[6].append( b32((6<<8) | i) )

    sink_n_msgs[6].append( b32(0) )

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, skip_check=True )
    s.run_sim( niter, th, max_cycles=50*niter, clock_time=clock_time )

  def test_fft( s, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 100
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( 'fft.json', ncols, nrows )
    imms = [ b32(0) for _ in range( ntiles ) ]

    imms[5] = b32(1)
    imms[9] = b32(42)
    imms[10] = b32(42)
    imms[11] = b32(42)
    imms[12] = b32(0)
    imms[13] = b32(42)
    imms[14] = b32(niter)
    imms[17] = b32(42)
    imms[18] = b32(42)
    imms[20] = b32(42)
    imms[26] = b32(1)
    imms[27] = b32(0)
    imms[28] = b32(1)
    imms[30] = b32(1)
    imms[36] = b32(42)

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter ):
      src_s_msgs[1].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[3].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[4].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[7].append( b32(randint(0, 2**32-1)) )

    sink_n_msgs[1] = [  b32(0) for _ in range(niter) ]
    sink_n_msgs[2] = [  b32(0) for _ in range(niter) ]
    sink_n_msgs[5] = [  b32(0) for _ in range(niter) ]
    sink_n_msgs[6] = [  b32(0) for _ in range(niter) ]

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, skip_check=True )
    s.run_sim( niter, th, max_cycles=50*niter, clock_time=clock_time )

  def test_susan( s, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 100
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( 'susan.json', ncols, nrows )
    imms = [ b32(0) for _ in range( ntiles ) ]

    imms[11] = b32(1)
    imms[18] = b32(0)
    imms[20] = b32(0)
    imms[28] = b32(42)
    imms[30] = b32(42)
    imms[35] = b32(niter-1)
    imms[36] = b32(10000)
    imms[37] = b32(1)
    imms[38] = b32(42)
    imms[43] = b32(1)
    imms[44] = b32(0)
    imms[52] = b32(10000)
    imms[53] = b32(42)

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter ):
      src_s_msgs[3].append( b32(randint(1, 2**32-1)) )
      src_s_msgs[5].append( b32(randint(1, 2**32-1)) )
      src_s_msgs[6].append( b32(randint(0, 2**32-1)) )

    sink_n_msgs[1].append( b32(0) )

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, skip_check=True )
    s.run_sim( niter, th, max_cycles=20*niter, clock_time=clock_time )

  def test_llist( s, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 100
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( 'llist.json', ncols, nrows )
    imms = [ b32(0) for _ in range( ntiles ) ]

    imms[11] = b32(42)
    imms[18] = b32(4)
    imms[19] = b32(0xdeadbeef)
    imms[20] = b32(0)
    imms[21] = b32(-1)

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter - 1 ):
      src_s_msgs[2].append( b32(randint(0, 2**32-1)) )

    for i in range( niter - 1 ):
      src_s_msgs[3].append( b32(100) )
    src_s_msgs[3].append( b32(42) )

    sink_n_msgs[6].append( b32(42) )

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms )
                      # imms, skip_check=True )
    s.run_sim( niter, th, max_cycles=20*niter, clock_time=clock_time )

  def test_adpcm( s, request ):
    raise NotImplementedError
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 10
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( 'adpcm.json', ncols, nrows )
    imms = [ b32(0) for _ in range( ntiles ) ]

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter - 1 ):
      src_s_msgs[2].append( b32(randint(0, 2**32-1)) )

    for i in range( niter - 1 ):
      src_s_msgs[3].append( b32(100) )
    src_s_msgs[3].append( b32(42) )

    sink_n_msgs[6].append( b32(42) )

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms )
                      # imms, skip_check=True )
    s.run_sim( niter, th, max_cycles=20*niter, clock_time=clock_time )

  def test_dither( s, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 1000
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( 'dither.json', ncols, nrows )
    imms = [ b32(0) for _ in range( ntiles ) ]

    # > 127
    imms[18] = b32(127)
    # getptr for &src[0]
    imms[25] = b32(0)
    # Data input of BR: 0
    imms[28] = b32(0)
    # Generate constant 0xff
    imms[29] = b32(0xff)
    # induction var boundary
    imms[32] = b32(niter)
    # Phi node of induction variable
    imms[33] = b32(0)
    # Phi node of error
    imms[34] = b32(0)
    # Phi node of dest_pixel
    imms[36] = b32(0)
    # + 1
    imms[41] = b32(1)

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter ):
      src_s_msgs[1].append( b32(i) )

    error = 0
    for i in range( niter ):
      out = src_s_msgs[1][i] + error
      if out > 127:
        dest_pixel = 0xff
        error = out - dest_pixel
      else:
        dest_pixel = 0
        error = out
      sink_n_msgs[1].append( b32(dest_pixel) )

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms )
                      # imms, skip_check=True )
    s.run_sim( niter, th, max_cycles=20*niter, clock_time=clock_time )

  @pytest.mark.parametrize(
    "nbody", [ 2, 4, 6, 8 ]
  )
  def test_fifo_depth_sweep( s, nbody, request ):
    json_file = f"cfg_series_cyclic_8x8_add_1_nominal_{nbody}_nominal_1_nominal.json"
    fifo_depth = request.config.option.fifo_depth
    print(f"Config file used: {json_file}")
    print(f"FIFO depth: {fifo_depth}")
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 2000
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )
    imms = [ b32(0) for _ in range( ntiles ) ]
    src_idx = (nbody // 2) - 1

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter ):
      src_n_msgs[src_idx].append( b32(1) )
      sink_e_msgs[6].append( b32(0) )

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, fifo_depth=fifo_depth,
                      skip_check=True )
    s.run_sim( niter, th, max_cycles=350*niter, clock_time=clock_time, vl_trace=False )

  @pytest.mark.parametrize(
    "fifo_depth", [ 1, 2, 4, 8, 16 ]
  )
  def test_fifo_depth_chain( s, fifo_depth, request ):
    json_file = "chain.json"
    print(f"Config file used: {json_file}")
    print(f"FIFO depth: {fifo_depth}")
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 2000
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )
    imms = [ b32(0) for _ in range( ntiles ) ]
    src_idx = 0

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( niter ):
      src_n_msgs[src_idx].append( b32(1) )
      sink_e_msgs[6].append( b32(0) )

    th = TestHarness( Bits32, ConfigMsg, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, fifo_depth=fifo_depth,
                      skip_check=True )
    s.run_sim( niter, th, max_cycles=350*niter, clock_time=clock_time, vl_trace=False )

#-------------------------------------------------------------------------
# Translation import test
#-------------------------------------------------------------------------

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
