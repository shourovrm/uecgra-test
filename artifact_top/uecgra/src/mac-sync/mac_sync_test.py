# Synchronous MAC unit tests
# Test harness and test structure from Yanghui

from pymtl3 import *
from pymtl3.stdlib.test import TestSrcCL, TestSinkCL

from mac_sync import MACSync

class TestHarness( Component ):
  def construct( s, Type, src, sink ):
    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.src = TestSrcCL( mk_bits(Type.nbits*2), src )
    s.dut = MACSync()
    s.sink = TestSinkCL( Type, sink )

    s.src.send //= s.dut.recv
    s.dut.send //= s.sink.recv

    s.clk //= s.src.clk
    s.reset //= s.src.reset
    s.clk //= s.dut.clk
    s.reset //= s.dut.reset
    s.clk //= s.sink.clk
    s.reset //= s.sink.reset

    s.dump_vcd = True
    s.vcd_file_name = "mac_sync_th"

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return f'{s.src.send}  > {s.dut.line_trace()} > {s.sink.recv}'

class MACSync_Tests:
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
    src_msgs  = [
        b16(0x0102), b16(0x0304), b16(0x0506), b16(0x0708),
        b16(0x090a), b16(0x0b0c), b16(0x0d0e), b16(0x0f10),
        b16(0x1112), b16(0x1314), b16(0x1516), b16(0x1718),
        b16(0x191a), b16(0x1b1c), b16(0x1d1e), b16(0x1f20),
    ]
    sink_msgs = [
        # 0x64    0x284     0x6a4     0xcc4
        b8(0x64), b8(0x84), b8(0xa4), b8(0xc4) ]
    th = TestHarness( Bits8, src_msgs, sink_msgs )
    s.run_sim( th )

  def test_backpressure( s ):
    src_msgs  = [
        b16(0x0102), b16(0x0304), b16(0x0506), b16(0x0708),
        b16(0x090a), b16(0x0b0c), b16(0x0d0e), b16(0x0f10),
        b16(0x1112), b16(0x1314), b16(0x1516), b16(0x1718),
        b16(0x191a), b16(0x1b1c), b16(0x1d1e), b16(0x1f20),
    ]
    sink_msgs = [
        # 0x64    0x284     0x6a4     0xcc4
        b8(0x64), b8(0x84), b8(0xa4), b8(0xc4) ]
    th = TestHarness( Bits8, src_msgs, sink_msgs )
    th.set_param( 'top.sink.construct', initial_delay=20 )
    s.run_sim( th )
