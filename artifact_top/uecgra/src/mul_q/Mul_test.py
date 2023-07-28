"""
==========================================================================
Mul_test.py
==========================================================================
Multiplier test.

Author : Yanghui Ou
  Date : July 30, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.test import TestSrcCL, TestSinkCL
from .Mul import Mul

class TestHarness( Component ):

  def construct( s, OpdType, src_msgs, sink_msgs ):
    MsgType = mk_bits( OpdType.nbits * 2 )
    s.src  = TestSrcCL ( MsgType, src_msgs  )
    s.dut  = Mul( OpdType )
    s.sink = TestSinkCL( MsgType, sink_msgs )

    s.src.send //= s.dut.recv
    s.dut.send //= s.sink.recv

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return f'{s.src.send}  > {s.dut.line_trace()} > {s.sink.recv}'

class Mul_Tests:
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

  def test_simple( s ):
    src_msgs  = [ b32(0x00040005) ] * 1
    sink_msgs = [ b32(0x00000014) ] * 1
    th = TestHarness( Bits16, src_msgs, sink_msgs )
    th.set_param( 'top.dut.construct', ncycles=1 )
    s.run_sim( th )

  def test_backpressure( s ):
    src_msgs  = [ b32(0x00040005), b32(0x00050004), b32(0x00000000) ]
    sink_msgs = [ b32(0x00000014), b32(0x00000014), b32(0x00000000) ]
    th = TestHarness( Bits16, src_msgs, sink_msgs )
    th.set_param( 'top.dut.construct', ncycles=4 )
    th.set_param( 'top.sink.construct', initial_delay=10 )
    s.run_sim( th )