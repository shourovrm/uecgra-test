"""
==========================================================================
Node_test.py
==========================================================================
Test cases for Node.

Author : Yanghui Ou
  Date : August 3, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.test import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ..enums import NodeConfig as NC
from ..Node import Node
from ..AluMsg import mk_alu_msg

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, Type, src_msgs, sink_msgs, configs ):
    ReqType = mk_alu_msg( Type )

    s.src     = TestSrcRTL( ReqType, src_msgs )
    s.cfg_src = TestSrcRTL( Bits5, configs )
    s.dut     = Node( Type )
    s.sink    = TestSinkCL( Type, sink_msgs )

    connect( s.src.send,         s.dut.recv  )
    connect( s.cfg_src.send.msg, s.dut.cfg   )
    connect( s.cfg_src.send.rdy, b1(1)       )
    connect( s.dut.send,         s.sink.recv )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.dut.line_trace()

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

alu32 = mk_alu_msg( Bits16 )
alu64 = mk_alu_msg( Bits32 )

class Node_Tests:

  def run_sim( s, th, max_cycles=200 ):
    print()
    th.elaborate()
    th.apply( SimulationPass )
    th.sim_reset()
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

  def test_node_mul( s ):
    src_msgs  = [ alu32( b16(0x0004), b16(0x0005) ), alu32( b16(0x0005), b16(0x0006) ) ]
    configs   = [ NC.MUL, NC.MUL, NC.MUL, NC.MUL ] * 5
    sink_msgs = [ b16(20), b16(30) ]
    th = TestHarness( Bits16, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=4 )
    s.run_sim( th )

  def test_node_mul_comb( s ):
    alu32 = mk_alu_msg( Bits16 )
    src_msgs  = [ alu32( b16(0x0004), b16(0x0005) ), alu32( b16(0x0005), b16(0x0006) ) ]
    configs   = [ NC.MUL, NC.MUL, NC.MUL, NC.MUL ] * 5
    sink_msgs = [ b16(20), b16(30) ]
    th = TestHarness( Bits16, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=0 )
    s.run_sim( th )

  def test_alu_add( s ):
    src_msgs  = [ alu32( b16(0x0004), b16(0x0005) ), alu32( b16(0x0005), b16(0x0006) ) ]
    configs   = [ NC.ALU_ADD, NC.ALU_ADD, NC.ALU_ADD, NC.ALU_ADD ] * 5
    sink_msgs = [ b16(9), b16(11) ]
    th = TestHarness( Bits16, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=0 )
    s.run_sim( th )

  def test_alu_sll( s ):
    src_msgs  = [ alu32( b16(0x0004), b16(0x0002) ), alu32( b16(0x0008), b16(0x0001) ) ]
    configs   = [ NC.ALU_SLL, NC.ALU_SLL, NC.ALU_SLL, NC.ALU_SLL ] * 5
    sink_msgs = [ b16(16), b16(16) ]
    th = TestHarness( Bits16, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=0 )
    s.run_sim( th )

  def test_mix_comb( s ):
    src_msgs  = [ alu32( b16(0x0004), b16(0x0005) ), alu32( b16(0x0005), b16(0x0006) ) ]
    configs   = [ NC.MUL, NC.ALU_ADD ]
    sink_msgs = [ b16(20), b16(11) ]
    th = TestHarness( Bits16, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=0 )
    s.run_sim( th )

  def test_mix_delay( s ):
    src_msgs  = [ alu32( b16(0x0004), b16(0x0005) ), alu32( b16(0x0005), b16(0x0006) ) ]
    configs   = [ NC.MUL, NC.ALU_ADD, NC.ALU_ADD ]
    sink_msgs = [ b16(20), b16(11) ]
    th = TestHarness( Bits16, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=1 )
    s.run_sim( th )

  def test_node_mul_32( s ):
    src_msgs  = [ alu64( b32(0x00000004), b32(0x00000005) ), alu64( b32(0x00000005), b32(0x00000006) ) ]
    configs   = [ NC.MUL, NC.MUL, NC.MUL, NC.MUL ] * 5
    sink_msgs = [ b32(20), b32(30) ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=4 )
    s.run_sim( th )

  def test_node_mul_comb_32( s ):
    src_msgs  = [ alu64( b32(0x00000004), b32(0x00000005) ), alu64( b32(0x00000005), b32(0x00000006) ) ]
    configs   = [ NC.MUL, NC.MUL, NC.MUL, NC.MUL ] * 5
    sink_msgs = [ b32(20), b32(30) ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=0 )
    s.run_sim( th )

  def test_alu_add_32( s ):
    src_msgs  = [ alu64( b32(0x00000004), b32(0x00000005) ), alu64( b32(0x00000005), b32(0x00000006) ) ]
    configs   = [ NC.ALU_ADD, NC.ALU_ADD, NC.ALU_ADD, NC.ALU_ADD ] * 5
    sink_msgs = [ b32(9), b32(11) ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=0 )
    s.run_sim( th )

  def test_alu_sll_32( s ):
    src_msgs  = [ alu64( b32(0x00000004), b32(0x00000002) ), alu64( b32(0x00000008), b32(0x00000001) ) ]
    configs   = [ NC.ALU_SLL, NC.ALU_SLL, NC.ALU_SLL, NC.ALU_SLL ] * 5
    sink_msgs = [ b32(16), b32(16) ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=0 )
    s.run_sim( th )

  def test_mix_comb_32( s ):
    src_msgs  = [ alu64( b32(0x00000004), b32(0x00000005) ), alu64( b32(0x00000008), b32(0x00000001) ) ]
    configs   = [ NC.MUL, NC.ALU_ADD ]
    sink_msgs = [ b32(20), b32(9) ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=0 )
    s.run_sim( th )

  def test_mix_delay_32( s ):
    src_msgs  = [ alu64( b32(0x00000004), b32(0x00000005) ), alu64( b32(0x00000005), b32(0x00000006) ) ]
    configs   = [ NC.MUL, NC.ALU_ADD, NC.ALU_ADD ]
    sink_msgs = [ b32(20), b32(11) ]
    th = TestHarness( Bits32, src_msgs, sink_msgs, configs )
    th.set_param( 'top.dut.construct', mul_ncycles=1 )
    s.run_sim( th )
