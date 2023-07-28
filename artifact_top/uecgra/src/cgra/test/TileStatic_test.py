"""
==========================================================================
TileStatic_test.py
==========================================================================
Test cases for static elastic CGRA tile.

Author : Yanghui Ou
  Date : August 9, 2019

"""
import pytest
import random
from itertools import product
from random import randint

from pymtl3 import *
from pymtl3.stdlib.test import TestSrcCL, TestSinkCL
from pymtl3.passes.yosys import TranslationImportPass, ImportConfigs

from ..enums import CfgMsg as CFG, TileDirection as TD
from ..ConfigMsg import ConfigMsg
from ..TileStatic import TileStatic

random.seed( 0xfaceb00c )

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, Type, src_msgs, sink_msgs, cfg_msg, imm=0, done_cnt=0 ):

    # Done counter

    s.done_cnt = 0
    s.done_limit = done_cnt

    # Components

    s.src  = [ TestSrcCL( Type, src_msgs[i] ) for i in range(4) ]
    s.dut  = TileStatic( Type, ConfigMsg )
    s.sink = [ TestSinkCL( Type, sink_msgs[i] ) for i in range(4) ]

    s.cfg_en = InPort( Bits1 )
    s.imm    = InPort( Type  )

    # Connections

    for i in range(4):
      connect( s.src[i].send, s.dut.recv[i]  )
      connect( s.dut.send[i], s.sink[i].recv )

    connect( s.cfg_en, s.dut.cfg_en )

    @s.update
    def up_configure():
      s.dut.cfg = cfg_msg
      s.dut.imm = Type(imm)

  def configure( s ):
    s.cfg_en = b1(1)
    s.tick()
    s.cfg_en = b1(0)

  def done( s ):
    if s.done_limit:
      # Used for stall test
      if s.done_cnt == s.done_limit:
        return True
      else:
        s.done_cnt += 1
        return False
    else:
      # Used for source-sink tests
      done_flag = True
      for i in range(4):
        done_flag = done_flag and s.src[i].done() and s.sink[i].done()
      return done_flag

  def line_trace( s ):
    return s.dut.line_trace()

#-------------------------------------------------------------------------
# Helper function
#-------------------------------------------------------------------------

def mk_config_msg(
  opcode      = CFG.OP_Q_TYPE,
  func        = CFG.NOP,
  src_opd_a   = CFG.SRC_SELF,
  src_opd_b   = CFG.SRC_SELF,
  src_bypass  = CFG.SRC_SELF,
  src_altbps  = CFG.SRC_SELF,
  dst_compute = CFG.DST_SELF,
  dst_bypass  = CFG.DST_NONE,
  dst_altbps  = CFG.DST_NONE,
):
  msg = ConfigMsg()
  msg.opcode      = opcode
  msg.func        = func
  msg.src_opd_a   = src_opd_a
  msg.src_opd_b   = src_opd_b
  msg.src_bypass  = src_bypass
  msg.src_altbps  = src_altbps
  msg.dst_compute = dst_compute
  msg.dst_bypass  = dst_bypass
  msg.dst_altbps  = dst_altbps
  return msg

def mk_test_msgs( cfg, lst ):
  src_msgs  = [ [] for _ in range(4) ]
  sink_msgs = [ [] for _ in range(4) ]

  assert len( lst ) % 5 == 0
  opd_a_lst   = lst[0::5]
  opd_b_lst   = lst[1::5]
  src_bps_lst = lst[2::5]
  res_lst     = lst[3::5]
  dst_bps_lst = lst[4::5]

  for a in opd_a_lst:
    if cfg.src_opd_a == CFG.SRC_NORTH:
      src_msgs[ TD.NORTH ].append( a )
    elif cfg.src_opd_a == CFG.SRC_SOUTH:
      src_msgs[ TD.SOUTH ].append( a )
    elif cfg.src_opd_a == CFG.SRC_WEST:
      src_msgs[ TD.WEST ].append( a )
    elif cfg.src_opd_a == CFG.SRC_EAST:
      src_msgs[ TD.EAST ].append( a )

  for b in opd_b_lst:
    if cfg.src_opd_b == CFG.SRC_NORTH:
      src_msgs[ TD.NORTH ].append( b )
    elif cfg.src_opd_b == CFG.SRC_SOUTH:
      src_msgs[ TD.SOUTH ].append( b )
    elif cfg.src_opd_b == CFG.SRC_WEST:
      src_msgs[ TD.WEST ].append( b )
    elif cfg.src_opd_b == CFG.SRC_EAST:
      src_msgs[ TD.EAST ].append( b )

  if cfg.src_bypass != cfg.src_opd_a and cfg.src_bypass != cfg.src_opd_a:
    for bps in src_bps_lst:
      if cfg.src_bypass == CFG.SRC_NORTH:
        src_msgs[ TD.NORTH ].append( bps )
      elif cfg.src_bypass == CFG.SRC_SOUTH:
        src_msgs[ TD.SOUTH ].append( bps )
      elif cfg.src_bypass == CFG.SRC_WEST:
        src_msgs[ TD.WEST ].append( bps )
      elif cfg.src_bypass == CFG.SRC_EAST:
        src_msgs[ TD.EAST ].append( bps )

  for res in res_lst:
    if cfg.dst_compute == CFG.DST_NORTH:
      sink_msgs[ TD.NORTH ].append( res )
    elif cfg.dst_compute == CFG.DST_SOUTH:
      sink_msgs[ TD.SOUTH ].append( res )
    elif cfg.dst_compute == CFG.DST_WEST:
      sink_msgs[ TD.WEST ].append( res )
    elif cfg.dst_compute == CFG.DST_EAST:
      sink_msgs[ TD.EAST ].append( res )

  if cfg.dst_bypass != CFG.DST_NONE and cfg.dst_bypass != CFG.DST_SELF:
    for bps in dst_bps_lst:
      if cfg.dst_bypass == CFG.DST_NORTH:
        sink_msgs[ TD.NORTH ].append( bps )
      elif cfg.dst_bypass == CFG.DST_SOUTH:
        sink_msgs[ TD.SOUTH ].append( bps )
      elif cfg.dst_bypass == CFG.DST_WEST:
        sink_msgs[ TD.WEST ].append( bps )
      elif cfg.dst_bypass == CFG.DST_EAST:
        sink_msgs[ TD.EAST ].append( bps )

  return src_msgs, sink_msgs

def mk_branch_msgs( cfg, lst ):
  src_msgs  = [ [] for _ in range(4) ]
  sink_msgs = [ [] for _ in range(4) ]

  assert len( lst ) % 6 == 0
  data_lst    = lst[0::6]
  bool_lst    = lst[1::6]
  dst_t_lst   = lst[2::6]
  dst_f_lst   = lst[3::6]
  src_bps_lst = lst[4::6]
  dst_bps_lst = lst[5::6]

  src_data  = cfg.src_opd_a
  src_bool  = cfg.src_opd_b
  dst_true  = cfg.dst_compute
  dst_false = cfg.func

  for a in data_lst:
    if src_data == CFG.SRC_NORTH:
      src_msgs[ TD.NORTH ].append( a )
    elif src_data == CFG.SRC_SOUTH:
      src_msgs[ TD.SOUTH ].append( a )
    elif src_data == CFG.SRC_WEST:
      src_msgs[ TD.WEST ].append( a )
    elif src_data == CFG.SRC_EAST:
      src_msgs[ TD.EAST ].append( a )

  for b in bool_lst:
    if src_bool == CFG.SRC_NORTH:
      src_msgs[ TD.NORTH ].append( b )
    elif src_bool == CFG.SRC_SOUTH:
      src_msgs[ TD.SOUTH ].append( b )
    elif src_bool == CFG.SRC_WEST:
      src_msgs[ TD.WEST ].append( b )
    elif src_bool == CFG.SRC_EAST:
      src_msgs[ TD.EAST ].append( b )

  if cfg.src_bypass != cfg.src_opd_a and cfg.src_bypass != cfg.src_opd_a:
    for bps in src_bps_lst:
      if cfg.src_bypass == CFG.SRC_NORTH:
        src_msgs[ TD.NORTH ].append( bps )
      elif cfg.src_bypass == CFG.SRC_SOUTH:
        src_msgs[ TD.SOUTH ].append( bps )
      elif cfg.src_bypass == CFG.SRC_WEST:
        src_msgs[ TD.WEST ].append( bps )
      elif cfg.src_bypass == CFG.SRC_EAST:
        src_msgs[ TD.EAST ].append( bps )

  # TODO: figure this out
  for res in res_lst:
    if cfg.dst_compute == CFG.DST_NORTH:
      sink_msgs[ TD.NORTH ].append( res )
    elif cfg.dst_compute == CFG.DST_SOUTH:
      sink_msgs[ TD.SOUTH ].append( res )
    elif cfg.dst_compute == CFG.DST_WEST:
      sink_msgs[ TD.WEST ].append( res )
    elif cfg.dst_compute == CFG.DST_EAST:
      sink_msgs[ TD.EAST ].append( res )

  if cfg.dst_bypass != CFG.DST_NONE and cfg.dst_bypass != CFG.DST_SELF:
    for bps in dst_bps_lst:
      if cfg.dst_bypass == CFG.DST_NORTH:
        sink_msgs[ TD.NORTH ].append( bps )
      elif cfg.dst_bypass == CFG.DST_SOUTH:
        sink_msgs[ TD.SOUTH ].append( bps )
      elif cfg.dst_bypass == CFG.DST_WEST:
        sink_msgs[ TD.WEST ].append( bps )
      elif cfg.dst_bypass == CFG.DST_EAST:
        sink_msgs[ TD.EAST ].append( bps )

  return src_msgs, sink_msgs

#-------------------------------------------------------------------------
# Test cases - PyMTL simulation
#-------------------------------------------------------------------------

class TileStatic_Tests:

  def th_cls( s, *args, **kwargs ):
    return TestHarness( *args, **kwargs )

  def run_sim( s, th, max_cycles=100 ):
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

  #-----------------------------------------------------------------------
  # Basic tests - arithmetic
  #-----------------------------------------------------------------------

  def test_add( s ):
    cfg = mk_config_msg(
      func        = CFG.ADD,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps   res     bps_res
      b16(2), b16(3), None, b16(5), None,
      b16(7), b16(0), None, b16(7), None,
    ])
    th = s.th_cls( Bits16, src_msgs, sink_msgs, cfg )
    s.run_sim( th )

  def test_addi( s ):
    cfg = mk_config_msg(
      func        = CFG.ADD,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_SELF,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps   res     bps_res
      b16(2), None, None,   b16(3), None,
      b16(7), None, None,   b16(8), None,
    ])
    th = s.th_cls( Bits16, src_msgs, sink_msgs, cfg, imm=1 )
    s.run_sim( th )

  def test_cp0( s ):
    cfg = mk_config_msg(
      func        = CFG.CP0,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_SELF,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b     bps   res     bps_res
      b16(2), None, None, b16(2), None,
      b16(7), None, None, b16(7), None,
    ])
    th = s.th_cls( Bits16, src_msgs, sink_msgs, cfg )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_cp1( s, init ):
    cfg = mk_config_msg(
      func        = CFG.CP1,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a     b       bps   res     bps_res
      None, b32(4), None, b32(4), None,
      None, b32(3), None, b32(3), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'ncycles', [ 0, 2 ] )
  def test_mul( s, ncycles ):
    cfg = mk_config_msg(
      func        = CFG.MUL,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_SOUTH,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps   res     bps_res
      b16(2), b16(2), None, b16(4), None,
      b16(7), b16(1), None, b16(7), None,
    ])
    th = s.th_cls( Bits16, src_msgs, sink_msgs, cfg )
    th.set_param( 'top.dut.construct', mul_ncycles=ncycles )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_sub( s, init ):
    cfg = mk_config_msg(
      func        = CFG.SUB,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_SOUTH,
      dst_bypass  = CFG.DST_NONE,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps   res     bps_res
      b16(5), b16(3), None, b16(2), None,
      b16(7), b16(2), None, b16(5),  None,
    ])
    th = s.th_cls( Bits16, src_msgs, sink_msgs, cfg )
    th.set_param( f'top.sink[{TD.SOUTH}].construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_subi( s, init ):
    cfg = mk_config_msg(
      func        = CFG.SUB,
      src_opd_a   = CFG.SRC_EAST,
      src_opd_b   = CFG.SRC_SELF,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_WEST,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 3
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps   res   bps_res
      b32(5), None, None, b32(2), None,
      b32(7), None, None, b32(4), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink[{TD.WEST}].construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_sll( s, init ):
    cfg = mk_config_msg(
      func        = CFG.SLL,
      src_opd_a   = CFG.SRC_EAST,
      src_opd_b   = CFG.SRC_WEST,
      dst_compute = CFG.DST_SOUTH,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps   res      bps_res
      b32(5), b32(1), None, b32(10), None,
      b32(7), b32(2), None, b32(28), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_slli( s, init ):
    cfg = mk_config_msg(
      func        = CFG.SLL,
      src_opd_a   = CFG.SRC_EAST,
      src_opd_b   = CFG.SRC_SELF,
      dst_compute = CFG.DST_SOUTH,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 2
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b     bps   res      bps_res
      b32(5), None, None, b32(20), None,
      b32(7), None, None, b32(28), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )


  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_srl( s, init ):
    cfg = mk_config_msg(
      func        = CFG.SRL,
      src_opd_a   = CFG.SRC_EAST,
      src_opd_b   = CFG.SRC_WEST,
      dst_compute = CFG.DST_SOUTH,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a        b       bps   res     bps_res
      b32(8),  b32(1), None, b32(4), None,
      b32(16), b32(2), None, b32(4), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_srli( s, init ):
    cfg = mk_config_msg(
      func        = CFG.SRL,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_NORTH,
      dst_compute = CFG.DST_SOUTH,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 128
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps   res       bps_res
      None,   b32(6), None, b32(2),   None,
      None,   b32(2), None, b32(32),  None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_and( s, init ):
    cfg = mk_config_msg(
      func        = CFG.AND,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SOUTH,
      dst_compute = CFG.DST_NORTH,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a            b            bps   res         bps_res
      b32(0b101),  b32(0b100),  None, b32(0b100), None,
      b32(0),      b32(0xface), None, b32(0),     None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_andi( s, init ):
    cfg = mk_config_msg(
      func        = CFG.AND,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_NORTH,
      dst_compute = CFG.DST_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0xffff
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b                bps   res           bps_res
      None,   b32(0xdeadcafe), None, b32(0xcafe),  None,
      None,   b32(0xdeadbeef), None, b32(0xbeef),  None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_or( s, init ):
    cfg = mk_config_msg(
      func        = CFG.OR,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SOUTH,
      dst_compute = CFG.DST_NORTH,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a                b            bps   res              bps_res
      b32(0b101),      b32(0b010),  None, b32(0b111),      None,
      b32(0xb00c0000), b32(0xface), None, b32(0xb00cface), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_ori( s, init ):
    cfg = mk_config_msg(
      func        = CFG.OR,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_EAST,
      dst_compute = CFG.DST_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0xdead0000
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b                bps   res           bps_res
      None,   b32(0xcafe), None, b32(0xdeadcafe),  None,
      None,   b32(0xbeef), None, b32(0xdeadbeef),  None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_xor( s, init ):
    cfg = mk_config_msg(
      func        = CFG.XOR,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SOUTH,
      dst_compute = CFG.DST_NORTH,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a           b            bps   res        bps_res
      b32(0b101), b32(0b011), None, b32(0b110), None,
      b32(0b111), b32(0b010), None, b32(0b101), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_xori( s, init ):
    cfg = mk_config_msg(
      func        = CFG.XOR,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_EAST,
      dst_compute = CFG.DST_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0xffff0000
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b                bps   res              bps_res
      None,   b32(0x0001),     None, b32(0xffff0001), None,
      None,   b32(0xffffffff), None, b32(0x0000ffff), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  #-----------------------------------------------------------------------
  # Basic tests - boolean logic
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_eq( s, init ):
    cfg = mk_config_msg(
      func        = CFG.EQ,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SOUTH,
      dst_compute = CFG.DST_NORTH,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a           b            bps   res    bps_res
      b32(0b101), b32(0b011), None, b32(0), None,
      b32(0b111), b32(0b111), None, b32(1), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_eqi( s, init ):
    cfg = mk_config_msg(
      func        = CFG.EQ,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SELF,
      dst_compute = CFG.DST_NORTH,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 32
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a           b     bps   res    bps_res
      b32(33), None, None, b32(0), None,
      b32(32), None, None, b32(1), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  def test_bypass_eqi( s ):
    cfg = mk_config_msg(
      func        = CFG.EQ,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_EAST,
      dst_bypass  = CFG.DST_WEST,
    )
    imm = 32
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a        b     bps     res     bps_res
      b32(33), None, b32(0), b32(0), b32(0),
      b32(32), None, b32(1), b32(1), b32(1),
    ])
    th = TestHarness( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=0 )
    th.set_param( f'top.src[{TD.EAST}].construct', initial_delay=10 )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_ne( s, init ):
    cfg = mk_config_msg(
      func        = CFG.NE,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SOUTH,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a           b            bps   res    bps_res
      b32(0b101), b32(0b011), None, b32(1), None,
      b32(0b111), b32(0b111), None, b32(0), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_nei( s, init ):
    cfg = mk_config_msg(
      func        = CFG.NE,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 32
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a           b     bps   res    bps_res
      b32(33), None, None, b32(1), None,
      b32(32), None, None, b32(0), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_gt( s, init ):
    cfg = mk_config_msg(
      func        = CFG.GT,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SOUTH,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a           b            bps   res    bps_res
      b32(16), b32(10), None, b32(1), None,
      b32(20), b32(30), None, b32(0), None,
      b32(32), b32(32), None, b32(0), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_gti( s, init ):
    cfg = mk_config_msg(
      func        = CFG.GT,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_NORTH,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 32
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a     b        bps   res    bps_res
      None, b32(32), None, b32(0), None,
      None, b32(31), None, b32(1), None,
      None, b32(33), None, b32(0), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_geq( s, init ):
    cfg = mk_config_msg(
      func        = CFG.GEQ,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SOUTH,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a           b            bps   res    bps_res
      b32(16), b32(10), None, b32(1), None,
      b32(20), b32(30), None, b32(0), None,
      b32(32), b32(32), None, b32(1), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_geqi( s, init ):
    cfg = mk_config_msg(
      func        = CFG.GEQ,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_NORTH,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 32
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a     b        bps   res    bps_res
      None, b32(32), None, b32(1), None,
      None, b32(31), None, b32(1), None,
      None, b32(33), None, b32(0), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_lt( s, init ):
    cfg = mk_config_msg(
      func        = CFG.LT,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SOUTH,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a           b            bps   res    bps_res
      b32(16), b32(10), None, b32(0), None,
      b32(20), b32(30), None, b32(1), None,
      b32(32), b32(32), None, b32(0), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_lti( s, init ):
    cfg = mk_config_msg(
      func        = CFG.LT,
      src_opd_a   = CFG.SRC_SOUTH,
      src_opd_b   = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 32
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a        b     bps   res    bps_res
      b32(32), None, None, b32(0), None,
      b32(31), None, None, b32(1), None,
      b32(33), None, None, b32(0), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_leq( s, init ):
    cfg = mk_config_msg(
      func        = CFG.LEQ,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SOUTH,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 0
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a           b            bps   res    bps_res
      b32(16), b32(10), None, b32(0), None,
      b32(20), b32(30), None, b32(1), None,
      b32(32), b32(32), None, b32(1), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_leqi( s, init ):
    cfg = mk_config_msg(
      func        = CFG.LEQ,
      src_opd_a   = CFG.SRC_SOUTH,
      src_opd_b   = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      src_bypass  = CFG.SRC_SELF,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 32
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a        b     bps   res    bps_res
      b32(32), None, None, b32(1), None,
      b32(31), None, None, b32(1), None,
      b32(33), None, None, b32(0), None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.sink*.construct', initial_delay=init )
    s.run_sim( th )

  #-----------------------------------------------------------------------
  # Basic tests - other
  #-----------------------------------------------------------------------

  def test_elastic( s ):
    cfg = mk_config_msg(
      func        = CFG.ADD,
      src_opd_a   = CFG.SRC_WEST,
      src_opd_b   = CFG.SRC_SOUTH,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps   res     bps_res
      b16(2), b16(3), None, b16(5), None,
      b16(8), b16(1), None, b16(9), None,
    ])
    th = s.th_cls( Bits16, src_msgs, sink_msgs, cfg )
    th.set_param( 'top.src[1].construct',
      initial_delay=3,
      interval_delay=2,
    )
    s.run_sim( th )

  @pytest.mark.parametrize(
    'init, intv',
    list(product( [ 0, 1, 2, 4 ], [ 0, 1, 2, 4 ] )),
  )
  def test_bypass( s, init, intv ):
    cfg = mk_config_msg(
      func        = CFG.NOP,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_SELF,
      src_bypass  = CFG.SRC_NORTH,
      dst_compute = CFG.DST_NONE,
      dst_bypass  = CFG.DST_EAST,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b     bps     res   bps_res
      None,   None, b16(2), None, b16(2),
      None,   None, b16(7), None, b16(7),
      None,   None, b16(9), None, b16(9),
      None,   None, b16(4), None, b16(4),
    ])
    th = s.th_cls( Bits16, src_msgs, sink_msgs, cfg )
    th.set_param( 'top.src[0].construct',
      initial_delay=init,
      interval_delay=intv,
    )
    s.run_sim( th, max_cycles=200 )

  def test_bypass_opd( s ):
    cfg = mk_config_msg(
      func        = CFG.ADD,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_NORTH,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_SOUTH,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps   res     bps_res
      b16(1), b16(1), None, b16(2), b16(1),
      b16(7), b16(2), None, b16(9), b16(7),
      b16(9), b16(0), None, b16(9), b16(9),
      b16(4), b16(3), None, b16(7), b16(4),
    ])
    th = s.th_cls( Bits16, src_msgs, sink_msgs, cfg )
    s.run_sim( th )

  def test_bypass_mul( s ):
    cfg = mk_config_msg(
      func        = CFG.MUL,
      src_opd_a   = CFG.SRC_SOUTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_NORTH,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_SOUTH,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps     res      bps_res
      b16(0), b16(0), b16(1), b16(0),  b16(1),
      b16(4), b16(3), b16(7), b16(12), b16(7),
      b16(2), b16(2), b16(9), b16(4),  b16(9),
      b16(3), b16(2), b16(4), b16(6),  b16(4),
    ])
    th = s.th_cls( Bits16, src_msgs, sink_msgs, cfg )
    s.run_sim( th )

  def test_phi_opd( s ):
    cfg = mk_config_msg(
      func        = CFG.PHI,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps     res      bps_res
      b16(0), None,   None,   b16(0),  None,
      b16(4), None,   None,   b16(4),  None,
      b16(2), None,   None,   b16(2),  None,
      b16(3), None,   None,   b16(3),  None,
      None,   b16(0), None,   b16(0),  None,
      None,   b16(1), None,   b16(1),  None,
      None,   b16(2), None,   b16(2),  None,
      None,   b16(3), None,   b16(3),  None,
    ])
    th = s.th_cls( Bits16, src_msgs, sink_msgs, cfg )
    th.set_param( f'top.src[{TD.WEST}].construct', initial_delay=10 )
    s.run_sim( th )

  def test_phi_init( s ):
    cfg = mk_config_msg(
      func        = CFG.PHI,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )
    imm = 32
    src_msgs, sink_msgs = mk_test_msgs( cfg, [
    # a       b       bps     res       bps_res
      None,   None,   None,   b32(imm), None,
      None,   b32(0), None,   b32(0),   None,
      None,   b32(1), None,   b32(1),   None,
      None,   b32(2), None,   b32(2),   None,
      None,   b32(3), None,   b32(3),   None,
    ])
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=imm )
    th.set_param( f'top.src[{TD.WEST}].construct', initial_delay=10 )
    s.run_sim( th )

  @pytest.mark.parametrize( 'init', list(range(4)) )
  def test_branch( s, init ):
    cfg = mk_config_msg(
      opcode      = CFG.OP_B_TYPE,
      func        = CFG.DST_SOUTH, # dst_false
      src_opd_a   = CFG.SRC_NORTH, # src_data
      src_opd_b   = CFG.SRC_WEST,  # src_bool
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,  # dst_true
      dst_bypass  = CFG.DST_NONE,
    )
    src_msgs = [
     [ b32(5), b32(8) ], # North
     [], # South
     [ b32(0), b32(1) ], # West
     [], # East
    ]
    sink_msgs = [
     [], # North
     [ b32(5) ], # South
     [], # West
     [ b32(8) ], # East
    ]
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    th.set_param( f'top.sink[{TD.SOUTH}].construct', initial_delay=init )
    s.run_sim( th )

  def test_branch_delay_bypass( s ):
    cfg = mk_config_msg(
      opcode      = CFG.OP_B_TYPE,
      func        = CFG.DST_WEST, # dst_false
      src_opd_a   = CFG.SRC_NORTH, # src_data
      src_opd_b   = CFG.SRC_WEST,  # src_bool
      src_bypass  = CFG.SRC_WEST,
      dst_compute = CFG.DST_EAST,  # dst_true
      dst_bypass  = CFG.DST_SOUTH,
    )
    src_msgs = [
     [ b32(5), b32(8) ] * 5, # North
     [], # South
     [ b32(0), b32(1) ] * 5, # West
     [], # East
    ]
    sink_msgs = [
     [], # North
     [ b32(0), b32(1) ] * 5, # South
     [ b32(5) ] * 5, # West
     [ b32(8) ] * 5, # East
    ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, cfg )
    th.set_param( f'top.src[{TD.WEST}].construct', initial_delay=5, interval_delay=3 )
    th.set_param( f'top.sink[{TD.SOUTH}].construct', initial_delay=15 )
    s.run_sim( th )

  def test_branch_both_bypass( s ):
    cfg = mk_config_msg(
      opcode      = CFG.OP_B_TYPE,
      func        = CFG.DST_SOUTH, # dst_false
      src_opd_a   = CFG.SRC_EAST,  # src_data
      src_opd_b   = CFG.SRC_SOUTH, # src_bool
      dst_compute = CFG.DST_NORTH, # dst_true
      src_bypass  = CFG.SRC_NORTH,
      dst_bypass  = CFG.DST_WEST,
      src_altbps  = CFG.SRC_SOUTH,
      dst_altbps  = CFG.DST_EAST,
    )
    src_msgs = [
      [ b32(10) ],          # North - bypass
      [ b32(0),  b32(0)  ], # South - bool
      [],                   # West - not used
      [ b32(32), b32(16) ], # East - data
    ]
    sink_msgs = [
      [],                   # North - true
      [ b32(32), b32(16) ], # South - false
      [ b32(10) ],          # West - bps from west
      [ b32(0),  b32(0)  ], # East - bps opd from south
    ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, cfg )
    th.set_param( 'top.sink[1].construct', initial_delay=10 )
    s.run_sim( th )

  def test_simple_altbps( s ):
    cfg = mk_config_msg(
      src_altbps = CFG.SRC_NORTH,
      dst_altbps = CFG.DST_EAST,
    )
    src_msgs = [
     [ b32(5), b32(8) ] * 5, # North
     [], # South
     [], # West
     [], # East
    ]
    sink_msgs = [
     [], # North
     [], # South
     [], # West
     [ b32(5), b32(8) ] * 5, # East
    ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th )

  def test_both_bypass( s ):
    cfg = mk_config_msg(
      src_bypass = CFG.SRC_SOUTH,
      src_altbps = CFG.SRC_NORTH,
      dst_bypass = CFG.DST_WEST,
      dst_altbps = CFG.DST_EAST,
    )
    src_msgs = [
     [ b32(5), b32(8) ] * 5, # North
     [ b32(4) ] * 5, # South
     [], # West
     [], # East
    ]
    sink_msgs = [
     [], # North
     [], # South
     [ b32(4) ] * 5, # West
     [ b32(5), b32(8) ] * 5, # East
    ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th )

  def test_multi_both_bypass( s ):
    cfg = mk_config_msg(
      src_bypass = CFG.SRC_NORTH,
      dst_bypass = CFG.DST_SOUTH,
      src_altbps = CFG.SRC_SOUTH,
      dst_altbps = CFG.DST_EAST | CFG.DST_NORTH,
    )
    src_msgs = [
     [ b32(5), b32(8) ] * 5, # North
     [ b32(4), b32(7) ] * 10, # South
     [], # West
     [], # East
    ]
    sink_msgs = [
     [ b32(4), b32(7) ] * 10, # North
     [ b32(5), b32(8) ] * 5, # South
     [], # West
     [ b32(4), b32(7) ] * 10, # East
    ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th )

  def test_multi_bypass( s ):
    cfg = mk_config_msg(
      src_bypass = CFG.SRC_NORTH,
      dst_bypass = CFG.DST_WEST | CFG.DST_SOUTH,
    )
    src_msgs = [
     [ b32(5), b32(8) ] * 5, # North
     [], # South
     [], # West
     [], # East
    ]
    sink_msgs = [
     [], # North
     [ b32(5), b32(8) ] * 5, # South
     [ b32(5), b32(8) ] * 5, # West
     [], # East
    ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, cfg )
    th.set_param( 'top.sink[1].construct', initial_delay=6 )
    s.run_sim( th )

  def test_opd_altbps( s ):
    cfg = mk_config_msg(
      func        = CFG.ADD,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      dst_compute = CFG.DST_SOUTH,
      src_altbps  = CFG.SRC_NORTH,
      dst_altbps  = CFG.DST_EAST,
    )
    src_msgs = [
      [ b32(10), b32(18) ], # North
      [], # South
      [ b32(22), b32(46) ], # West
      [], # East
    ]
    sink_msgs = [
      [], # North
      [ b32(32), b32(64) ], # South
      [], # West
      [ b32(10), b32(18) ], # East
    ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, cfg )
    th.set_param( f'top.sink[{TD.SOUTH}].construct', initial_delay=15 )
    s.run_sim( th )

  def test_both_opd_bypass( s ):
    cfg = mk_config_msg(
      func        = CFG.ADD,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      dst_compute = CFG.DST_SOUTH,
      src_bypass  = CFG.SRC_WEST,
      dst_bypass  = CFG.DST_NORTH,
      src_altbps  = CFG.SRC_NORTH,
      dst_altbps  = CFG.DST_EAST,
    )
    src_msgs = [
      [ b32(10), b32(18) ], # North
      [], # South
      [ b32(22), b32(46) ], # West
      [], # East
    ]
    sink_msgs = [
      [ b32(22), b32(46) ], # North
      [ b32(32), b32(64) ], # South
      [], # West
      [ b32(10), b32(18) ], # East
    ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, cfg )
    th.set_param( f'top.sink[{TD.EAST}].construct', initial_delay=10 )
    s.run_sim( th )

  #-----------------------------------------------------------------------
  # Streaming tests
  #-----------------------------------------------------------------------

  def test_stall( s ):
    cfg = ConfigMsg(
      func        = CFG.NOP,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_SELF,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_NONE,
      dst_bypass  = CFG.DST_NONE,
    )

    src_msgs = [ [], [], [], [] ]
    sink_msgs = [ [], [], [], [] ]

    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg, imm=0, done_cnt=500 )
    s.run_sim( th, max_cycles=600 )

  def test_stream_mul( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.MUL,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a = b32( randint(0, 2**32 -1) )
      b = b32( randint(0, 2**32 -1) )
      res = b32( a * b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # a
      test_msgs.append( None ) # a
      test_msgs.append( res  ) # a
      test_msgs.append( None ) # a

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_add( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.ADD,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a + b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_sub( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.SUB,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a - b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_sll( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.SLL,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 31)       )
      res = b32( a << b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_srl( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.SRL,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 31)       )
      res = b32( a >> b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_cp0( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.CP0,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_SELF,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      res = a
      test_msgs.append( a    ) # a
      test_msgs.append( None ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_and( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.AND,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a & b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_or( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.OR,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a | b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_xor( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.XOR,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a ^ b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_eq( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.EQ,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a == b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_ne( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.NE,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a != b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_gt( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.GT,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a > b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_geq( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.GEQ,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a >= b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_lt( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.LT,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a < b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_leq( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.LEQ,
      src_opd_a   = CFG.SRC_NORTH,
      src_opd_b   = CFG.SRC_WEST,
      src_bypass  = CFG.SRC_SELF,
      dst_compute = CFG.DST_EAST,
      dst_bypass  = CFG.DST_NONE,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      b   = b32( randint(0, 2**32 -1) )
      res = b32( a <= b )
      test_msgs.append( a    ) # a
      test_msgs.append( b    ) # b
      test_msgs.append( None ) # bps
      test_msgs.append( res  ) # res
      test_msgs.append( None ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

  def test_stream_bps( s ):
    nmsgs = 100
    cfg = mk_config_msg(
      func        = CFG.NOP,
      src_opd_a   = CFG.SRC_SELF,
      src_opd_b   = CFG.SRC_SELF,
      src_bypass  = CFG.SRC_NORTH,
      dst_compute = CFG.DST_NONE,
      dst_bypass  = CFG.DST_EAST,
    )

    test_msgs = []
    for _ in range(nmsgs):
      a   = b32( randint(0, 2**32 -1) )
      test_msgs.append( None ) # a
      test_msgs.append( None ) # b
      test_msgs.append( a    ) # bps
      test_msgs.append( None ) # res
      test_msgs.append( a    ) # bps_res

    src_msgs, sink_msgs = mk_test_msgs( cfg, test_msgs )
    th = s.th_cls( Bits32, src_msgs, sink_msgs, cfg )
    s.run_sim( th, max_cycles=500 )

#-------------------------------------------------------------------------
# Transaltion-import test
#-------------------------------------------------------------------------

class TileStaticV_Tests( TileStatic_Tests ):

  def run_sim( s, th, max_cycles=200 ):
    print()
    th.elaborate()
    th.dut.yosys_translate_import = True
    # Use 750MHz PyMTL clock (1.33 ns period)
    th.dut.yosys_import = ImportConfigs(
      vl_trace = True,
      vl_trace_timescale  = "1ps",
      vl_trace_cycle_time = 1332,
    )
    th = TranslationImportPass()( th )
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
