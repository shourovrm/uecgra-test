"""
==========================================================================
StaticCGRA_RGALS_test.py
==========================================================================
Test cases for the ratio-chronous elastic static CGRA.

Author : Yanghui Ou, Peitian Pan
  Date : August 14, 2019

"""

import pytest
from itertools import product
from random import randint

from pymtl3 import *
from pymtl3.stdlib.test import TestSrcCL, TestSinkCL
from pymtl3.stdlib.ifcs import SendIfcRTL
from pymtl3.passes.yosys import TranslationImportPass, ImportConfigs

from fifos.BisyncQueue import BisyncQueue
from clock.clock_divider import ClockDivider
from clock.enums import CLK_NOMINAL, CLK_FAST, CLK_SLOW
from cgra.StaticCGRA_RGALS import StaticCGRA_RGALS_wrapper
from cgra.ConfigMsg_RGALS import ConfigMsg_RGALS
from cgra.test.test_utils import json_to_cfgs
from misc.adapters import Enq2Send

from .test_utils import to_vcd_cycle_time

clk_choices = {
    0 : (   1,  1,  3 ),
    1 : (   5,  6, 18 ),
    2 : (   2,  3,  9 ),
    3 : (   1,  2,  6 ),
    4 : (   2,  5, 15 ),
    5 : (   1,  3,  9 ),
    6 : (   2,  7, 21 ),
    7 : (   1,  4, 12 ),
    8 : (   2,  9, 27 ),
    9 : (   1,  5, 15 ),
   10 : (   2, 11, 33 ),
   11 : (   1,  6, 18 ),
}

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, Type, CfgMsgType, ncols=2, nrows=2, cfg_msgs=[],
                 src_n_msgs=[], src_s_msgs=[], src_w_msgs=[], src_e_msgs=[],
                 sink_n_msgs=[], sink_s_msgs=[], sink_w_msgs=[], sink_e_msgs=[],
                 imms=None, skip_check=False, fifo_latency=0,
                 freq_choice=2 ):

    print(f"Current fifo latency = {fifo_latency}")
    print(f"Frequency choice: {freq_choice}")

    s.freq_choice = freq_choice

    s.cfgs = cfg_msgs

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )

    # Local parameter

    ntiles = nrows * ncols
    s.ntiles = ntiles

    # Components

    # s.clksel = [ SendIfcRTL( Bits1 ) for _ in range( ntiles ) ]
    s.clksel_en = [ InPort( Bits1 ) for _ in range( ntiles ) ]
    s.clksel_msg = [ InPort( Bits2 ) for _ in range( ntiles ) ]
    s.clksel_rdy = [ OutPort( Bits1 ) for _ in range( ntiles ) ]

    s.src_n = [ TestSrcCL( Type, src_n_msgs[i] ) for i in range( ncols ) ]
    s.src_s = [ TestSrcCL( Type, src_s_msgs[i] ) for i in range( ncols ) ]
    s.src_w = [ TestSrcCL( Type, src_w_msgs[i] ) for i in range( nrows ) ]
    s.src_e = [ TestSrcCL( Type, src_e_msgs[i] ) for i in range( nrows ) ]

    s.dut = StaticCGRA_RGALS_wrapper( Type, CfgMsgType, ncols, nrows, 0,
                                      fifo_latency=fifo_latency,
                                      freq_choice=freq_choice )(
      clk = s.clk,
      reset = s.reset,
      clk_reset = s.clk_reset,
    )

    if not skip_check:
      s.sink_n = [ TestSinkCL( Type, sink_n_msgs[i] ) for i in range( ncols ) ]
      s.sink_s = [ TestSinkCL( Type, sink_s_msgs[i] ) for i in range( ncols ) ]
      s.sink_w = [ TestSinkCL( Type, sink_w_msgs[i] ) for i in range( nrows ) ]
      s.sink_e = [ TestSinkCL( Type, sink_e_msgs[i] ) for i in range( nrows ) ]
    else:
      s.sink_n = [ TestSinkCL( Type, sink_n_msgs[i], cmp_fn=lambda a, b: True) for i in range( ncols ) ]
      s.sink_s = [ TestSinkCL( Type, sink_s_msgs[i], cmp_fn=lambda a, b: True) for i in range( ncols ) ]
      s.sink_w = [ TestSinkCL( Type, sink_w_msgs[i], cmp_fn=lambda a, b: True) for i in range( nrows ) ]
      s.sink_e = [ TestSinkCL( Type, sink_e_msgs[i], cmp_fn=lambda a, b: True) for i in range( nrows ) ]

    s.cfg_en = InPort( Bits1 )

    if not imms:
      imms = [ Type(0) for _ in range( ntiles ) ]

    # Connect to DUT

    s.dut.clk //= s.clk
    s.dut.reset //= s.reset
    s.dut.clk_reset //= s.clk_reset

    for i in range(ntiles):
      # s.dut.clksel[i] //= s.clksel[i]
      s.dut.clksel[i].en //= s.clksel_en[i]
      s.dut.clksel[i].msg //= s.clksel_msg[i]
      s.dut.clksel[i].rdy //= s.clksel_rdy[i]
      s.dut.cfg_en[i] //= s.cfg_en

    # Connect reset to srcs/sinks

    for i in range(ncols):
      s.src_n[i].reset //= s.reset
      s.src_s[i].reset //= s.reset

      s.sink_n[i].reset //= s.reset
      s.sink_s[i].reset //= s.reset

    for i in range(nrows):
      s.src_w[i].reset //= s.reset
      s.src_e[i].reset //= s.reset

      s.sink_w[i].reset //= s.reset
      s.sink_e[i].reset //= s.reset

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

    @s.update
    def up_configs():
      for i in range( ntiles ):
        s.dut.cfg[i] = cfg_msgs[i]
        s.dut.imm[i] = imms[i]


  def rgals_reset( s ):
    """Reset the RGALS design and set up the correct clock for each tile"""
    fast, nominal, slow = clk_choices[s.freq_choice]
    reset_cycles = fast + nominal + slow

    s.reset = b1(1)
    s.clk_reset = b1(1)
    s.tick()
    s.tick()

    # Set up clock switcher
    # TODO: currently assume there are only two clocks
    assert all(s.clksel_rdy[i] for i in range(s.ntiles))
    s.clk_reset = b1(0)
    for i in range(s.ntiles):
      s.clksel_en[i] = b1(1)
      s.clksel_msg[i] = b2(s.cfgs[i].clk_self)
    s.tick()
    s.tick()

    # Wait till the configuration finishes
    s.cfg_en = b1(1)
    for _ in range(reset_cycles):
      s.tick()

    # Reset finishes
    s.reset = b1(0)

    # De-assert clksel enable
    for i in range(s.ntiles):
      s.clksel_en[i] = b1(0)
    s.tick()

    # Configure CGRA
    s.tick()
    s.cfg_en = b1(0)

    print("RGALS reset finished!")


  def done( s ):
    return all([c.done() for c in \
        sum([s.src_n, s.src_s, s.src_w, s.src_e,
             s.sink_n, s.sink_s, s.sink_w, s.sink_e], [])])


  def line_trace( s ):
    return s.dut.line_trace()

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

class StaticCGRA_RGALS_Tests:

  freq_choice = 0
  # PyMTL magic clock is 1GHz
  vcd_timescale = "1ps"
  # vcd_cycle_time = 444
  nominal_clk_ratio = 3.0

  def run_sim( s, n_iter, th, max_cycles=100, clock_time="1.33", vl_trace=True ):
    print()
    th.elaborate()
    th.dut.yosys_translate_import = True
    th.dut.yosys_import = ImportConfigs(
      vl_trace = vl_trace,
      vl_trace_timescale  = StaticCGRA_RGALS_Tests.vcd_timescale,
      vl_trace_cycle_time = to_vcd_cycle_time(clock_time),
    )
    print(f"Vcd cycle time = {to_vcd_cycle_time(clock_time)}")
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

    _, nominal, _ = clk_choices[s.freq_choice]
    nominal_factor = float(nominal)/3

    # n_iter iterations
    print("num_cycles = {}, num_nominal_cycles = {}, iterations/nominal cycle = {} iters/cycle".format(
      ncycles,
      float(ncycles) / nominal_factor,
      StaticCGRA_RGALS_Tests.nominal_clk_ratio*n_iter/ncycles,
    ))

  def test_elaborate( s ):
    dut = StaticCGRA_RGALS_wrapper( Bits32, ConfigMsg_RGALS )
    dut.elaborate()

  @pytest.mark.parametrize(
    "n_iter, json_file",
    list(product(
      # Number of iterations
      # [ 1000, ],
      [ 20, ],

      # config JSONs
      [
        "cfg_vvadd_2x2.json",
        # "cfg_vvadd_2x2_mix.json",
      ],
    )),
  )
  def test_vvadd( s, n_iter, json_file ):
    ncols = 2; nrows = 2

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )

    src_n_msgs = [ [] for _ in range(2) ]
    src_s_msgs = [ [] for _ in range(2) ]
    src_w_msgs = [
      [b32(randint(0, 255)) for _ in range(n_iter)],
      [b32(randint(0, 255)) for _ in range(n_iter)],
    ]
    src_e_msgs = [ [] for _ in range(2) ]

    sink_n_msgs = [ [] for _ in range(2) ]
    sink_s_msgs = [ [] for _ in range(2) ]
    sink_w_msgs = [ [] for _ in range(2) ]
    sink_e_msgs = [ [], [b32(x+y) for x, y in zip(src_w_msgs[0], src_w_msgs[1])], ]

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs )
    s.run_sim( n_iter, th, 2000 * n_iter )

  @pytest.mark.parametrize(
    "n_iter, json_file",
    list(product(
      # Number of iterations
      # [ 1000, ],
      [ 20, ],

      # clksel for each tile
      [
        "cfg_1d_conv_2x6.json",
        "cfg_1d_conv_2x6_mix.json",
      ],
    )),
  )
  def test_1d_conv_2x6( s, n_iter, json_file ):
    ncols = 6; nrows = 2

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )

    src_n_msgs = [
      [b32(randint(0, 255)) for _ in range(n_iter)], # a0
      [b32(randint(0, 255)) for _ in range(n_iter)], # b0
      [b32(randint(0, 255)) for _ in range(n_iter)], # a1
      [b32(randint(0, 255)) for _ in range(n_iter)], # b1
      [b32(randint(0, 255)) for _ in range(n_iter)], # a2
      [b32(randint(0, 255)) for _ in range(n_iter)], # b2
    ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [
      [b32(a0 * b0 + a1 * b1 + a2 * b2) for a0, b0, a1, b1, a2, b2 in zip(*src_n_msgs[:-2])],
      []
    ]

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs )
    s.run_sim( n_iter, th, 100 * n_iter )

  @pytest.mark.parametrize(
    "n_iter, json_file",
    list(product(
      # Number of iterations
      [ 10, ],
      # [ 2, ],

      # clksel for each tile
      [
        "cfg_1d_conv_8x8.json",
        # "cfg_1d_conv_8x8_mix.json",
      ],
    )),
  )
  def test_1d_conv_8x8( s, n_iter, json_file ):
    ncols = 8; nrows = 8
    ntiles = ncols * nrows

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )

    src_n_msgs = [
      [b32(randint(0, 255)) for _ in range(n_iter)], # a0
      [b32(randint(0, 255)) for _ in range(n_iter)], # b0
      [b32(randint(0, 255)) for _ in range(n_iter)], # a1
      [b32(randint(0, 255)) for _ in range(n_iter)], # b1
      [b32(randint(0, 255)) for _ in range(n_iter)], # a2
      [b32(randint(0, 255)) for _ in range(n_iter)], # b2
      [], [],
    ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [], [], [], [], [], [],
      [b32(a0 * b0 + a1 * b1 + a2 * b2) for a0, b0, a1, b1, a2, b2 in zip(*src_n_msgs[:-2])],
      [],
    ]

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs )
    s.run_sim( n_iter, th, 100 * n_iter )

  @pytest.mark.parametrize(
    "n_iter, json_file",
    list(product(
      # Number of iterations
      [ 1000, ],
      # [ 2, ],
      # [ 20, ],

      # clksel for each tile
      [
        "cfg_series_parallel_8x8_add_1_nominal_1_nominal_1_nominal.json",
        # "cfg_1d_conv_8x8_mix.json",
      ],
    )),
  )
  def test_series_parallel_8x8_1_1_1( s, n_iter, json_file ):
    ncols = 8; nrows = 8
    ntiles = ncols * nrows

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )

    src_n_msgs = [
      [b32(randint(0, 255)) for _ in range(n_iter)], [], [], [], [], [], [], [],
    ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [], [], [], [], [], [],
      [b32(8*n) for n in src_n_msgs[0]], [],
    ]

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs )
    s.run_sim( n_iter, th, 200 * n_iter )

  @pytest.mark.parametrize(
    "n_iter, p_clk, b_clk, e_clk",
    list(product(
      # Number of iterations
      [ 200, ],
      # [ 2, ],

      # Prologue clock domain
      # [ "nominal", "fast", "slow" ],
      [ "nominal" ],

      # Body clock domain
      # [ "nominal", "fast", "slow" ],
      [ "fast" ],
      # [ "nominal" ],

      # Epilogue clock domain
      # [ "nominal", "fast", "slow" ],
      [ "nominal" ],
    )),
  )
  def test_series_parallel_8x8_3_5_3( s, n_iter, p_clk, b_clk, e_clk ):
    ncols = 8; nrows = 8
    ntiles = ncols * nrows

    # json_file = f"cfg_series_parallel_{nrows}x{ncols}_add_3_{p_clk}_5_{b_clk}_3_{e_clk}_r.json"
    json_file = "cfg_series_parallel_8x8_add_chapter.json"
    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )

    src_n_msgs = [ [b32(randint(0, 255)) for _ in range(n_iter)],
        [], [], [], [], [], [], [], ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [],
      [b32(1088*n) for n in src_n_msgs[0]], [], [], [], [], [], [], ]

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs )
    s.run_sim( n_iter, th, 200 * n_iter )

  @pytest.mark.parametrize(
    "n_iter, json_file",
    list(product(
      # Number of iterations
      [ 1000, ],
      # [ 2, ],
      # [ 20, ],

      # clksel for each tile
      [
        "cfg_series_cyclic_8x8_add_1_nominal_1_nominal_1_nominal.json",
      ],
    )),
  )
  def test_series_cyclic_8x8_1_1_1( s, n_iter, json_file ):
    ncols = 8; nrows = 8
    ntiles = ncols * nrows

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )

    src_n_msgs = [ [b32(randint(0, 255)) for _ in range(n_iter)],
        [], [], [], [], [], [], [], ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [], [], [], [], [], [],
      [b32(8*n) for n in src_n_msgs[0]], [], ]

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs )
    s.run_sim( n_iter, th, 200 * n_iter )

  @pytest.mark.parametrize(
    "n_iter, json_file",
    list(product(
      # Number of iterations
      [ 200, ],
      # [ 10, ],

      # clksel for each tile
      [
        # "cfg_series_cyclic_8x8_add_3_nominal_4_nominal_3_nominal_r.json",
        # "cfg_series_cyclic_8x8_add_3_nominal_4_fast_3_nominal_r.json",
        "cfg_series_cyclic_8x8_add_chapter.json",
      ],
    )),
  )
  def test_series_cyclic_8x8_3_4_3( s, n_iter, json_file ):
    ncols = 8; nrows = 8
    ntiles = ncols * nrows
    imm = [ b32(42) for _ in range(ntiles) ]

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )

    src_n_msgs = [ [], [b32(randint(0, 255)) for _ in range(n_iter)],
        [], [], [], [], [], [], ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    W = [b32(0) for _ in range(n_iter)]
    for i in range(n_iter):
      if i == 0:
        W[i] = b32(8*src_n_msgs[1][i] + int(imm[0]))
      else:
        W[i] = b32(8*src_n_msgs[1][i] + 4*W[i-1])

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [], [], [], [b32(8*n) for n in W], [], [], [], [], ]

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imm )
    s.run_sim( n_iter, th, 200 * n_iter )

  @pytest.mark.parametrize(
    "n_iter, json_file",
    list(product(
      # Number of iterations
      [ 100, ],

      # clksel for each tile
      [
        "fir.json",
        "fir_dvfs.json",
        "fir_dvfs_eeff.json",
      ],
    )),
  )
  def test_fir( s, n_iter, json_file, request ):
    ncols = 8; nrows = 8
    ntiles = ncols * nrows
    imms = [ b32(0) for _ in range( ntiles ) ]
    imms[35] = b32(1)
    imms[27] = b32(n_iter)
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( n_iter ):
      src_s_msgs[1].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[2].append( b32(randint(0, 2**32-1)) )

    sink_n_msgs[5].append( b32(sum(map(lambda x: x[0]*x[1], zip(src_s_msgs[1], src_s_msgs[2])))) )

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms )
    s.run_sim( n_iter, th, 60 * n_iter, clock_time=clock_time )

  @pytest.mark.parametrize(
    "n_iter, json_file",
    list(product(
      # Number of iterations
      [ 100, ],

      # clksel for each tile
      [
        "fir_alt.json",
        "fir_alt_dvfs.json",
      ],
    )),
  )
  def test_alt_fir( s, n_iter, json_file ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )
    imms = [ b32(0) for _ in range( ntiles ) ]
    imms[13] = b32(1)
    imms[20] = b32(1)
    imms[28] = b32(1)
    imms[36] = b32(n_iter)

    src_n_msgs = [ [] for _ in range( ncols ) ]
    src_s_msgs = [ [] for _ in range( ncols ) ]
    src_w_msgs = [ [] for _ in range( nrows ) ]
    src_e_msgs = [ [] for _ in range( nrows ) ]

    sink_n_msgs = [ [] for _ in range( ncols ) ]
    sink_s_msgs = [ [] for _ in range( ncols ) ]
    sink_w_msgs = [ [] for _ in range( nrows ) ]
    sink_e_msgs = [ [] for _ in range( nrows ) ]

    for i in range( n_iter ):
      src_s_msgs[4].append( b32(randint(0, 2**32-1)) )
      src_s_msgs[5].append( b32(randint(0, 2**32-1)) )

    sink_n_msgs[2].append( b32(sum(map(lambda x: x[0]*x[1], zip(src_s_msgs[4], src_s_msgs[5])))) )

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms )
    s.run_sim( n_iter, th, max_cycles=100*n_iter )

  @pytest.mark.parametrize(
    "json_file",
    [
      "latnrm.json",
      "latnrm_dvfs.json",
      "latnrm_dvfs_eeff.json",
    ],
  )
  def test_latnrm( s, json_file, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 100
    clock_time = request.config.option.clock_time

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )
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

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, skip_check=True )
    s.run_sim( niter, th, max_cycles=140*niter, clock_time=clock_time )

  @pytest.mark.parametrize(
    "json_file",
    [
      "bf.json",
      "bf_dvfs.json",
      "bf_dvfs_eeff.json",
    ],
  )
  def test_bf( s, json_file, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 32
    clock_time = request.config.option.clock_time
    fifo_lat = int(request.config.option.fifo_latency)

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )
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

    sink_n_msgs[6].append( b32(0) )

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, fifo_latency = fifo_lat,
                      skip_check=True )
    s.run_sim( niter, th, max_cycles=250*niter, clock_time=clock_time )

  @pytest.mark.parametrize(
    "json_file",
    [
      "fft.json",
      "fft_dvfs.json",
      "fft_dvfs_eeff.json",
    ],
  )
  def test_fft( s, json_file, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 1000
    clock_time = request.config.option.clock_time
    fifo_lat = int(request.config.option.fifo_latency)

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )
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

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, fifo_latency=fifo_lat,
                      skip_check=True )
    s.run_sim( niter, th, max_cycles=200*niter, clock_time=clock_time )

  @pytest.mark.parametrize(
    "json_file",
    [
      "susan.json",
      "susan_dvfs.json",
      "susan_dvfs_eeff.json",
    ],
  )
  def test_susan( s, json_file, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 1000
    clock_time = request.config.option.clock_time
    fifo_lat = int(request.config.option.fifo_latency)

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )
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
      src_s_msgs[3].append( b32(randint(0, 2*32-1)) )
      src_s_msgs[5].append( b32(randint(0, 2*32-1)) )
      src_s_msgs[6].append( b32(randint(0, 2*32-1)) )

    sink_n_msgs[1].append( b32(0) )

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, fifo_latency = fifo_lat,
                      skip_check=True )
    s.run_sim( niter, th, max_cycles=350*niter, clock_time=clock_time )

  @pytest.mark.parametrize(
    "json_file",
    [
      "llist.json",
      "llist_dvfs.json",
      "llist_dvfs_eeff.json",
    ],
  )
  def test_llist( s, json_file, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 1000
    clock_time = request.config.option.clock_time
    fifo_lat = int(request.config.option.fifo_latency)

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )
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

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, fifo_latency=fifo_lat,
                    )
                      # imms, skip_check=True )
    s.run_sim( niter, th, max_cycles=350*niter, clock_time=clock_time )

  @pytest.mark.parametrize(
    "json_file",
    [
      "dither.json",
      "dither_dvfs.json",
      "dither_dvfs_eeff.json",
    ],
  )
  def test_dither( s, json_file, request ):
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 1000
    clock_time = request.config.option.clock_time
    fifo_lat = int(request.config.option.fifo_latency)

    cfg_msgs = json_to_cfgs( json_file, ncols, nrows, False )
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

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, fifo_latency=fifo_lat,
                    )
                      # imms, skip_check=True )
    s.run_sim( niter, th, max_cycles=350*niter, clock_time=clock_time )

  @pytest.mark.parametrize(
    ("nbody, freq_choice"), list(product(
      # [
      #   2, 4, 6, 8
      # ],
      [
        4
      ],
      # list(range(12)),
      list(range(8)),
    ))
  )
  def test_freq_sweep( s, nbody, freq_choice, request ):
    json_file = f"cfg_series_cyclic_8x8_add_1_nominal_{nbody}_fast_1_nominal.json"
    print(f"Config file used: {json_file}")
    print(f"Freq choice: {freq_choice}")
    ncols  = 8; nrows = 8
    ntiles = ncols * nrows
    niter  = 2000
    clock_time = request.config.option.clock_time
    fifo_lat = int(request.config.option.fifo_latency)

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

    th = TestHarness( Bits32, ConfigMsg_RGALS, ncols, nrows, cfg_msgs,
                      src_n_msgs, src_s_msgs, src_w_msgs, src_e_msgs,
                      sink_n_msgs, sink_s_msgs, sink_w_msgs, sink_e_msgs,
                      imms, fifo_latency=fifo_lat,
                      freq_choice=freq_choice,
                      skip_check=True )
    s.freq_choice = freq_choice
    # s.run_sim( niter, th, max_cycles=350*niter, clock_time=clock_time, vl_trace=False )
    s.run_sim( niter, th, max_cycles=350*niter, clock_time=clock_time )
