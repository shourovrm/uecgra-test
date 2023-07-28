#=========================================================================
# suppressor.py
#=========================================================================
# PyMTL suppressor wrapper.
#
# Author : Peitian Pan
# Date   :  Aug 21, 2019

from pymtl3 import *
from pymtl3.stdlib.rtl import Mux, RegRst

from clock.enums import *
from crossing.enums import *

class Suppressor( Component ):
  def construct( s ):
    s.reset = InPort( Bits1 )

    # r_clk will clock the empty/empty_next registers
    s.r_clk = InPort( Bits1 )

    s.w_clk_rate = InPort( Bits2 )
    s.r_clk_rate = InPort( Bits2 )
    s.is_empty = InPort( Bits1 )
    s.is_empty_next = InPort( Bits1 )
    s.unsafe_bus = InPort( Bits9 )

    s.from_left = InPort( Bits1 )
    s.to_right = OutPort( Bits1 )
    s.from_right = InPort( Bits1 )
    s.to_left = OutPort( Bits1 )

    # Wires
    s.suppress = Wire( Bits1 )
    s.suppress_en = Wire( Bits1 )
    s.unsafe_sel = Wire( Bits4 )
    s.is_unsafe = Wire( Bits1 )

    # Regs
    s.empty_reg = RegRst( Bits1 )(
      clk = s.r_clk,
      in_ = s.is_empty,
      reset = s.reset,
    )
    s.empty_next_reg = RegRst( Bits1 )(
      clk = s.r_clk,
      in_ = s.is_empty_next,
      reset = s.reset,
    )

    @s.update
    def unsafe_sel_gen():
      if s.w_clk_rate == CLK_FAST:
        if s.r_clk_rate == CLK_FAST:
          s.unsafe_sel = SEL_FAST_FAST
        elif s.r_clk_rate == CLK_SLOW:
          s.unsafe_sel = SEL_FAST_SLOW
        else:
          # Treat the clock of current doamin as nominal
          s.unsafe_sel = SEL_FAST_NOMINAL
      elif s.w_clk_rate == CLK_SLOW:
        if s.r_clk_rate == CLK_FAST:
          s.unsafe_sel = SEL_SLOW_FAST
        elif s.r_clk_rate == CLK_SLOW:
          s.unsafe_sel = SEL_SLOW_SLOW
        else:
          # Treat the clock of current doamin as nominal
          s.unsafe_sel = SEL_SLOW_NOMINAL
      elif s.w_clk_rate == CLK_NOMINAL:
        if s.r_clk_rate == CLK_FAST:
          s.unsafe_sel = SEL_NOMINAL_FAST
        elif s.r_clk_rate == CLK_SLOW:
          s.unsafe_sel = SEL_NOMINAL_SLOW
        else:
          # Treat the clock of current doamin as nominal
          s.unsafe_sel = SEL_NOMINAL_NOMINAL
      else:
        # This is the outmost input buffer. We assume that the input
        # data appears in the buffer on the exact clock edge and therefore
        # no suppression is needed (this is achieved by selecting the 
        # nominal-nominal crossing suppression bit which is always 0).
        s.unsafe_sel = SEL_NOMINAL_NOMINAL

    @s.update
    def suppress_en_gen():
      # Enable suppression if the queue was or was expected to be empty on
      # last edge of r_clk and the queue is not empty right now.
      s.suppress_en = ((not s.is_empty) and s.empty_reg.out) or ((not s.is_empty) and s.empty_next_reg.out)

    @s.update
    def is_unsafe_gen():
      s.is_unsafe = s.unsafe_bus[ s.unsafe_sel ]

    @s.update
    def suppress_gen():
      s.suppress = s.is_unsafe and s.suppress_en

    # Suppress the transaction

    @s.update
    def do_suppress():
      if s.suppress:
        s.to_right = b1(0)
        s.to_left = b1(0)
      else:
        s.to_right = s.from_left
        s.to_left = s.from_right
