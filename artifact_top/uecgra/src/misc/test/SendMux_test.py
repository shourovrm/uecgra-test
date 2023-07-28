"""
==========================================================================
SendMux_test.py
==========================================================================
Test cases for SendBox.

Author : Yanghui Ou
  Date : August 2, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.test import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ..SendMux import SendMux

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, Type, src_msgs, sink_msgs, configs, ninputs=4 ):

    # Local parameters

    s.ninputs = ninputs
    sel_type = mk_bits( clog2( ninputs ) )

    # Components

    s.src     = [ TestSrcRTL( Type, src_msgs[i] ) for i in range(ninputs) ]
    s.cfg_src = TestSrcRTL( sel_type, configs )
    s.dut     = SendMux( Type, ninputs )
    s.sink    = TestSinkCL( Type, sink_msgs )

    for i in range( ninputs ):
      connect( s.src[i].send, s.dut.recv[i] )

    connect( s.cfg_src.send.msg, s.dut.sel   )
    connect( s.cfg_src.send.rdy, b1(1)       )
    connect( s.dut.send,         s.sink.recv )

  def done( s ):
    done_flag = s.sink.done()
    for i in range(s.ninputs):
      done_flag = done_flag and s.src[i].done()
    return done_flag

  def line_trace( s ):
    return s.dut.line_trace()

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

class SendMux_Tests:

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

  def test_sm_simple( s ):
    src_msgs = [
      [ b16(0xface) ],
      [ b16(0xb00c) ],
      [ ],
      [ ],
    ]

    configs   = [ b2(1), b2(0) ]
    sink_msgs = [ b16(0xb00c), b16(0xface) ]

    th = TestHarness( Bits16, src_msgs, sink_msgs, configs, 4 )
    s.run_sim( th )
