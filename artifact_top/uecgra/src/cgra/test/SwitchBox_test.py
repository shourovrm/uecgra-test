"""
==========================================================================
SwitchBox_test.py
==========================================================================
Test cases for SwitchBox.

Author : Yanghui Ou
  Date : August 2, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.test import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ..SwitchBox import SwitchBox
from ..enums import SwitchBoxDirection as SB_Dir

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, Type, src_msgs, sink_msgs, configs ):
    s.src     = TestSrcRTL( Type, src_msgs )
    s.cfg_src = TestSrcRTL( Bits5, configs )
    s.dut     = SwitchBox( Type )
    s.sink    = [ TestSinkCL( Type, sink_msgs[i] ) for i in range(5) ]

    connect( s.src.send,         s.dut.recv )
    connect( s.cfg_src.send.msg, s.dut.cfg  )
    connect( s.cfg_src.send.rdy, b1(1)      )

    for i in range(5):
      connect( s.dut.send[i], s.sink[i].recv )

  def done( s ):
    done_flag = s.src.done()
    for i in range(5):
      done_flag = done_flag and s.sink[i].done()
    return done_flag

  def line_trace( s ):
    return s.dut.line_trace()

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

class SB_Tests:

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

  def test_sb_simple( s ):
    src_msgs  = [ b16(0xface), b16(0xface) ]
    configs   = [ SB_Dir.NONE, SB_Dir.NONE, SB_Dir.NORTH, SB_Dir.SOUTH ]
    sink_msgs = [
      [ b16(0xface) ],
      [ b16(0xface) ],
      [ ],
      [ ],
      [ ],
    ]
    th = TestHarness( Bits16, src_msgs, sink_msgs, configs )
    s.run_sim( th )
