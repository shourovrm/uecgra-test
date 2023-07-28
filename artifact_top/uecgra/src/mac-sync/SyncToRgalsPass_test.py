# Synchronous MAC unit tests
# Test harness and test structure from Yanghui

from pymtl3 import *
from pymtl3.stdlib.test import TestSrcCL, TestSinkCL
from pymtl3.stdlib.ifcs import RecvIfcRTL
from pymtl3.passes.sverilog import TranslationImportPass, ImportConfigs

from SyncToRgalsPass import Top, SyncToRgalsPass

class TestHarness( Component ):
  def construct( s, Type, src, sink ):

    # Interfaces
    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.clksel1 = RecvIfcRTL( Bits1 )
    s.clksel2 = RecvIfcRTL( Bits1 )

    # Types
    InType = mk_bits( Type.nbits*2 )
    OutType = Type

    # Components
    s.src = TestSrcCL( InType, src )
    s.dut = Top( InType, OutType )
    s.sink = TestSinkCL( OutType, sink )

    # Connections
    s.clk //= s.src.clk
    s.reset //= s.src.reset
    s.clk //= s.dut.clk
    s.reset //= s.dut.reset
    s.clk //= s.sink.clk
    s.reset //= s.sink.reset

    s.clk_reset //= s.dut.clk_reset
    s.clksel1 //= s.dut.pe1_clksel_recv
    s.clksel2 //= s.dut.pe2_clksel_recv

    s.src.send //= s.dut.recv
    s.dut.send //= s.sink.recv

    # Flags and misc attributes
    s.dump_vcd = True
    s.vcd_file_name = "mac_sync_top"
    s.p1, s.p2 = s.dut.cd1.clk_div[0], s.dut.cd2.clk_div[0]

  def rgals_sim_reset( s ):
    # Reset the RGALS design and set up the correct clock for each PE

    def gcd( x, y ):
      if x < y:
        x, y = y, x
      while(y):
        x, y = y, x % y
      return x

    # Least common multiplier of the clock dividers
    lcm = (s.p1 * s.p2) // gcd(s.p1, s.p2)

    s.reset = b1(1)
    s.clk_reset = b1(1)
    print(s.dut.internal_line_trace()); print("-----")
    s.tick()
    print(s.dut.internal_line_trace()); print("-----")
    s.tick()

    # Set up clock switcher
    assert s.clksel1.rdy == b1(1)
    assert s.clksel2.rdy == b1(1)
    s.clk_reset = b1(0)
    s.clksel1.en = b1(1)
    s.clksel1.msg = b1(0)
    s.clksel2.en = b1(1)
    s.clksel2.msg = b1(1)
    s.tick()

    # Wait till the configuration finishes
    for _ in range(lcm-1):
      print(s.dut.internal_line_trace()); print("-----")
      s.tick()

    # Reset finishes
    s.reset = b1(0)
    s.clksel1.en = b1(0)
    s.clksel2.en = b1(0)
    print(s.dut.internal_line_trace()); print("-----")
    s.tick()
    print("RGALS reset finished!")

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return f'{s.src.send} > {s.dut.line_trace()} > {s.sink.recv}'

class MACSyncTop_Tests:
  # Pure-python simulation of the synchronous design
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
    # Test sink is always ready
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
    # Test sink is not ready until 20 cycles later
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

class MACRgalsTop_Tests( MACSyncTop_Tests ):
  # Transform-translate-import simulation of the RGALS design
  def run_sim( s, th, max_cycles=200 ):
    print()
    th.elaborate()
    th.apply( SyncToRgalsPass() )
    th.dut.sverilog_translate_import = True
    th.dut.sverilog_import = ImportConfigs(vl_trace = True)
    th = TranslationImportPass()( th )
    th.apply( SimulationPass )
    # Special RGALS reset
    th.rgals_sim_reset()
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
