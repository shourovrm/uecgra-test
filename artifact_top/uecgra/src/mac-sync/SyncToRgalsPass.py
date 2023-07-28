#=========================================================================
# SyncToRgalsPass.py
#=========================================================================
# Transform an elaborated synchronous design into an RGALS design.
#
# Author : Peitian Pan
# Date   : Aug 4, 2019

from pymtl3 import *
from pymtl3.dsl import Placeholder
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.sverilog import TranslationPass, TranslationConfigs
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL, DeqIfcRTL
from pymtl3.stdlib.rtl.queues import NormalQueueRTL

# Hack to insert the top of RGALS directory to PYTHONPATH
try:
  import mul_q
except:
  import os, sys
  cur_dir = os.path.dirname(os.path.abspath(__file__))
  while cur_dir and not os.path.isfile(f"{cur_dir}/conftest.py"):
    cur_dir = os.path.dirname(cur_dir)
    sys.path.insert(0, cur_dir)

from mul_q.Mul import Mul
from acc_q.Acc import Acc
from clock.clk_divider import ClockDivider, SyncClockDivider
from clock.clk_switcher import ClockSwitcher
from misc.normal_queue import BisynchronousNormalQueue, SyncNormalQueue

class PE( Component ):
  # PE module which does not include the input buffer. the
  # ratio-chronous wrapper will wrap this component together
  # with input buffer and clock switcher to form a stand-alone
  # PE unit.
  def construct( s, DataType ):
    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.recv = RecvIfcRTL( DataType )
    s.send = SendIfcRTL( DataType )
    s.recv //= s.send

class PESync( Component ):
  # This synchronous PE wrapper includes the PE module and
  # has the same interface as the ratio-chronous wrapper.
  def construct( s, InType, OutType, PEType ):
    s.clk1 = InPort( Bits1 )
    s.clk2 = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.clksel = RecvIfcRTL( Bits1 )

    s.clk_m = InPort( Bits1 )
    s.clk_out = OutPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.recv = RecvIfcRTL( InType )
    s.send = SendIfcRTL( OutType )
    s.pe = PEType( OutType )(
      clk = s.clk_m,
      reset = s.reset,
      recv = s.recv,
      send = s.send,
    )
    s.clksel.rdy //= b1(1)
    s.clk_out //= s.clk_m

  def line_trace( s ):
    return s.pe.line_trace()

class PERgals( Component ):
  # A ratio-chronous wrapper that contains a PE module
  # instance that is of class `PEType`. This wrapper also includes
  # an input buffer (bisynchronous queue) and a clock switcher
  def construct( s, InType, OutType, PEType ):
    s.clk1 = InPort( Bits1 )
    s.clk2 = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.clksel = RecvIfcRTL( Bits1 )

    s.clk_m = InPort( Bits1 )
    s.clk_out = OutPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.recv = RecvIfcRTL( InType )
    s.send = SendIfcRTL( OutType )

    s.domain_clk = Wire( Bits1 )

    s.switcher = ClockSwitcher()(
      clk1 = s.clk1,
      clk2 = s.clk2,
      clk_reset = s.clk_reset,
      switch_val = s.clksel.en,
      switch_rdy = s.clksel.rdy,
      switch_msg = s.clksel.msg,
      clk_out = s.domain_clk,
    )
    s.pe = PEType( OutType )(
      clk = s.domain_clk,
      reset = s.reset
    )
    s.q = BisynchronousNormalQueue(InType.nbits)(
      w_clk = s.clk_m,
      r_clk = s.domain_clk,
      reset = s.reset,
      w_val = s.recv.en,
      w_rdy = s.recv.rdy,
      w_msg = s.recv.msg,
      r_val = s.pe.recv.en,
      r_rdy = s.pe.recv.rdy,
      r_msg = s.pe.recv.msg,
    )
    s.pe.send.en  //= s.send.en
    s.pe.send.rdy //= s.send.rdy
    s.pe.send.msg //= s.send.msg
    s.clk_out //= s.domain_clk

class Top( Component ):
  # Top of sync/rgals design. Note that currently we have to
  # include clock dividers at top level even for synchronous
  # designs.
  def construct( s, InType, OutType ):
    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.pe1_clksel_recv = RecvIfcRTL( Bits1 )
    s.pe2_clksel_recv = RecvIfcRTL( Bits1 )
    s.recv = RecvIfcRTL( InType )
    s.send = SendIfcRTL( OutType )

    # Clock dividers
    s.cd1 = SyncClockDivider()(
      clk = s.clk,
      clk_reset = s.clk_reset,
    )
    s.cd1.clk_div = (3,)
    s.cd2 = SyncClockDivider()(
      clk = s.clk,
      clk_reset = s.clk_reset,
    )
    s.cd2.clk_div = (5,)

    # PE's, Mul -> Acc
    s.pe1 = PESync( InType, OutType, Mul )(
      clk_m = s.clk,
      clk1 = s.cd1.clk_divided,
      clk2 = s.cd2.clk_divided,
      clk_reset = s.clk_reset,
      clksel = s.pe1_clksel_recv,
      reset = s.reset,
      recv = s.recv,
    )
    s.pe1.pe_sync = (InType, OutType, Mul)
    s.pe2 = PESync( OutType, OutType, Acc )(
      clk_m = s.pe1.clk_out,
      clk1 = s.cd1.clk_divided,
      clk2 = s.cd2.clk_divided,
      clk_reset = s.clk_reset,
      clksel = s.pe2_clksel_recv,
      reset = s.reset,
      recv = s.pe1.send,
    )
    s.pe2.pe_sync = (OutType, OutType, Acc)

    # Clock domain crossing queue at output side
    s.biq_out = SyncNormalQueue(OutType.nbits)(
      w_clk = s.pe2.clk_out,
      r_clk = s.clk,
      reset = s.reset,
      w_val = s.pe2.send.en,
      w_rdy = s.pe2.send.rdy,
      w_msg = s.pe2.send.msg,
      r_val = s.send.en,
      r_rdy = s.send.rdy,
      r_msg = s.send.msg,
    )
    s.biq_out.cdc_out_q = True

    s.sverilog_translate = TranslationConfigs()

  def line_trace( s ):
    return f"{s.recv}(M:{s.pe1.line_trace()})>(A:{s.pe2.line_trace()}){s.send}"

class SyncToRgalsPass( BasePass ):
  """Transform a synchronous PyMTL design into a ratio-chronous design."""

  def __call__( s, top ):
    # Swap in Verilog clock dividers
    s.swap_clk_dividers( top )
    # Swap in rgals PE wrappers
    s.swap_pes( top )
    # Swap in Verilog output clock domain crossing queue
    s.swap_output_crossing_queues( top )

  def swap_clk_dividers( s, top ):
    def do_swap_clk_divider( orig, tag ):
      top.replace_component_with_obj(orig, ClockDivider(tag[0]))
    s.traverse( top, "clk_div", do_swap_clk_divider )

  def swap_pes( s, top ):
    def do_swap_pe( orig, tag ):
      new_pe = PERgals( *tag )
      top.replace_component_with_obj(orig, new_pe)
    s.traverse( top, "pe_sync", do_swap_pe )

  def swap_output_crossing_queues( s, top ):
    def do_swap_output_crossing_queue( orig, tag ):
      new_q = BisynchronousNormalQueue(orig._dsl.args[0])
      top.replace_component_with_obj(orig, new_q)
    s.traverse( top, "cdc_out_q", do_swap_output_crossing_queue )

  def traverse( s, m, tag, action ):
    if hasattr( m, tag ):
      action( m, getattr(m, tag) )
    else:
      for child in m.get_child_components():
        s.traverse( child, tag, action )

if __name__ == "__main__":
  dut = Top( Bits16, Bits8 )
  dut.elaborate()
  dut.apply( SyncToRgalsPass() )
  dut.apply( TranslationPass() )
