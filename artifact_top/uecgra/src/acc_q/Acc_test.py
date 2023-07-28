"""
==========================================================================
Acc_test.py
==========================================================================
Accumulator test.

Author : Yanghui Ou
  Date : July 30, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.test import TestSrcCL, TestSinkCL
from .Acc import Acc

class TestHarness( Component ):

  def construct( s, Type, src_msgs, sink_msgs ):
    s.src  = TestSrcCL ( Type, src_msgs  )
    s.dut  = Acc( Type )
    s.sink = TestSinkCL( Type, sink_msgs )

    s.src.send //= s.dut.recv
    s.dut.send //= s.sink.recv

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return f'{s.src.send}  > {s.dut.line_trace()} > {s.sink.recv}'

class Acc_Tests:
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
    src_msgs  = [ b16(0), b16(1), b16(2), b16(3) ]
    sink_msgs = [ b16(1), b16(5) ]
    th = TestHarness( Bits16, src_msgs, sink_msgs )
    th.set_param( 'top.dut.construct', nmsgs=2 )
    s.run_sim( th )

  def test_backpressure( s ):
    src_msgs  = [
      b16(4), b16(1), b16(2), b16(3),
      b16(1), b16(2), b16(3), b16(4),
    ]
    sink_msgs = [ b16(10), b16(10) ]
    th = TestHarness( Bits16, src_msgs, sink_msgs )
    th.set_param( 'top.dut.construct', nmsgs=4 )
    th.set_param( 'top.sink.construct', initial_delay=20 )
    s.run_sim( th )

  def test_delay( s ):
    src_msgs  = [
      b16(4), b16(1), b16(2), b16(3),
      b16(1), b16(2), b16(3), b16(4),
    ]
    sink_msgs = [ b16(10), b16(10) ]
    th = TestHarness( Bits16, src_msgs, sink_msgs )
    th.set_param( 'top.dut.construct', nmsgs=4 )
    th.set_param( 'top.sink.construct', initial_delay=3 )
    th.set_param( 'top.src.construct', interval_delay=5 )
    s.run_sim( th )