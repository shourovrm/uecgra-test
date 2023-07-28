#=========================================================================
# TileStatic_RGALS_test.py
#=========================================================================
# Test cases for RGALS static elastic CGRA tile.
#
# Author : Yanghui Ou, Peitian Pan
# Date   : Aug 27, 2019

from pymtl3 import *
from pymtl3.stdlib.rtl import And
from pymtl3.stdlib.test import TestSinkCL, TestSrcCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL
from pymtl3.passes.yosys import TranslationImportPass, ImportConfigs

from clock.clock_counter import ClockCounter
from clock.clock_divider import ClockDivider
from clock.enums import CLK_NOMINAL, CLK_FAST, CLK_SLOW
from cgra.TileStatic_RGALS import TileStatic_RGALS_wrapper
from cgra.ConfigMsg_RGALS import ConfigMsg_RGALS
from cgra.test.TileStatic_test import TileStatic_Tests

#-------------------------------------------------------------------------
# Test harness clock rate settings
#-------------------------------------------------------------------------

# We are using 750MHz nominal clock frequency

TH_CLK_RATE_IN  = CLK_NOMINAL
TH_CLK_RATE_OUT = CLK_NOMINAL

# TH_CLK_RATE_IN  = CLK_FAST
# TH_CLK_RATE_OUT = CLK_FAST

if TH_CLK_RATE_IN == CLK_FAST:
  CLK_RATIO_IN = 2
elif TH_CLK_RATE_IN == CLK_SLOW:
  CLK_RATIO_IN = 9
else:
  CLK_RATIO_IN = 3

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, Type, src_msgs, sink_msgs, cfg_msg, imm=0, done_cnt=0,
                    clk_rate_in=TH_CLK_RATE_IN, clk_rate_out=TH_CLK_RATE_OUT ):

    # Done counter

    s.done_cnt = 0
    s.done_limit = done_cnt

    # Create an RGALS config message from the given config

    s.cfg             = ConfigMsg_RGALS()
    s.cfg.opcode      = cfg_msg.opcode
    s.cfg.func        = cfg_msg.func
    s.cfg.src_opd_a   = cfg_msg.src_opd_a
    s.cfg.src_opd_b   = cfg_msg.src_opd_b
    s.cfg.dst_compute = cfg_msg.dst_compute
    s.cfg.src_bypass  = cfg_msg.src_bypass
    s.cfg.dst_bypass  = cfg_msg.dst_bypass
    s.cfg.src_altbps  = cfg_msg.src_altbps
    s.cfg.dst_altbps  = cfg_msg.dst_altbps
    s.cfg.clk_self    = clk_rate_out

    # clocks and reset

    s.clk = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    s.clk1 = Wire( Bits1 )
    s.clk2 = Wire( Bits1 )
    s.clk3 = Wire( Bits1 )

    s.cd1 = ClockDivider( 2 )(
      clk = s.clk,
      clk_reset = s.clk_reset,
      clk_divided = s.clk1,
    )
    s.cd2 = ClockDivider( 9 )(
      clk = s.clk,
      clk_reset = s.clk_reset,
      clk_divided = s.clk2,
    )
    s.cd3 = ClockDivider( 3 )(
      clk = s.clk,
      clk_reset = s.clk_reset,
      clk_divided = s.clk3,
    )
    s.cd1.yosys_translate_import = True
    s.cd2.yosys_translate_import = True
    s.cd3.yosys_translate_import = True

    s.clksel_en = InPort( Bits1 )
    s.clksel_msg = InPort( Bits2 )
    s.clksel_rdy = OutPort( Bits1 )

    # Components

    tile_clk_in = "nominal"
    if TH_CLK_RATE_IN == CLK_FAST:
      tile_clk_in = "fast"
    if TH_CLK_RATE_IN == CLK_SLOW:
      tile_clk_in = "slow"

    s.src  = [ TestSrcCL( Type, src_msgs[i] ) for i in range(4) ]
    s.dut  = TileStatic_RGALS_wrapper( Type, ConfigMsg_RGALS, mul_ncycles=0, clk_in=tile_clk_in )
    s.sink = [ TestSinkCL( Type, sink_msgs[i] ) for i in range(4) ]

    s.cfg_en = InPort( Bits1 )
    s.imm    = InPort( Type  )

    # Connections

    for i in range(4):
      s.src[i].reset //= s.reset
      s.sink[i].reset //= s.reset
      s.src[i].send //= s.dut.recv[i]
      s.dut.send[i] //= s.sink[i].recv

      if clk_rate_in == CLK_FAST:
        s.dut.clk_rate_in[i] //= CLK_FAST
      elif clk_rate_in == CLK_SLOW:
        s.dut.clk_rate_in[i] //= CLK_SLOW
      else:
        s.dut.clk_rate_in[i] //= CLK_NOMINAL

    s.cfg_en     //= s.dut.cfg_en
    s.clk        //= s.dut.clk
    s.clk1       //= s.dut.clk_rgals.clk1
    s.clk2       //= s.dut.clk_rgals.clk2
    s.clk3       //= s.dut.clk_rgals.clk3
    s.clk_reset  //= s.dut.clk_rgals.clk_reset
    s.reset      //= s.dut.reset
    s.clksel_en  //= s.dut.clk_rgals.clksel.en
    s.clksel_msg //= s.dut.clk_rgals.clksel.msg
    s.clksel_rdy //= s.dut.clk_rgals.clksel.rdy

    @s.update
    def up_configure():
      s.dut.cfg = s.cfg
      s.dut.imm = Type(imm)

  def rgals_reset( s ):
    """Reset the RGALS design and set up the correct clock for each tile"""
    reset_cycles = 2+3+9

    s.reset = b1(1)
    s.clk_reset = b1(1)
    s.tick()
    s.tick()

    # Set up clock switcher
    assert s.clksel_rdy
    s.clk_reset = b1(0)
    s.clksel_en = b1(1)
    s.clksel_msg = b2(s.cfg.clk_self)
    s.tick()
    s.tick()

    # Wait till the configuration finishes
    s.cfg_en = b1(1)
    for _ in range(reset_cycles-2):
      s.tick()

    # Reset finishes
    s.reset = b1(0)

    # De-assert clksel enable
    s.clksel_en = b1(0)
    s.tick()

    # Configure CGRA
    s.tick()
    s.cfg_en = b1(0)

    print("RGALS reset finished!")

  def done( s ):
    if s.done_limit:
      if s.done_cnt == s.done_limit:
        return True
      else:
        s.done_cnt += 1
        return False
    else:
      return all([c.done() for c in (s.src + s.sink)])

  def line_trace( s ):
    return s.dut.line_trace()

class TileStatic_RGALS_Tests( TileStatic_Tests ):

  # Inorder to make the nominal clock 750MHz (divided by 3),
  # PyMTL magic clock should be 2.25GHz (444ps clock period).
  vcd_timescale = "1ps"
  vcd_cycle_time = 444

  def th_cls( s, *args, **kwargs ):
    return TestHarness( *args, **kwargs )

  def run_sim( s, th, max_cycles=100 ):
    print()
    th.elaborate()
    th.dut.yosys_translate_import = True
    th.dut.yosys_import = ImportConfigs(
      vl_trace = True,
      vl_trace_timescale  = TileStatic_RGALS_Tests.vcd_timescale,
      vl_trace_cycle_time = TileStatic_RGALS_Tests.vcd_cycle_time,
    )
    th = TranslationImportPass()( th )
    th.elaborate()
    th.apply( SimulationPass )
    th.rgals_reset()
    ncycles = 0
    th.tick()
    ncycles += 1

    while not th.done() and ncycles < max_cycles:
      th.tick()
      ncycles += 1
      if ncycles % 5000 == 0:
        print(f"ncycles = {ncycles}")

    assert ncycles < max_cycles
