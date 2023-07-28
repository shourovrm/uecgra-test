#=========================================================================
# clock_divider.py
#=========================================================================
# Provides a Verilog clock divider Placeholder and a PyMTL synchronous
# dummy clock divider.
# Author : Peitian Pan
# Date   : Aug 12, 2019

from pymtl3 import *
from pymtl3.dsl import Placeholder
from pymtl3.passes.sverilog import TranslationConfigs

class ClockDivider( Placeholder, Component ):
  # taken as a blackbox during translation
  def construct( s, p_divideby ):
    s.clk  = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.clk_divided = OutPort( Bits1 )
    s.sverilog_translate = TranslationConfigs(
      v_src = "$RGALS_TOP/src/clock/ClockDivider.v",
    )
    s.yosys_translate = TranslationConfigs(
      v_src = "$RGALS_TOP/src/clock/ClockDivider.v",
    )

class SyncClockDivider( Component ):
  # TODO: right now the only mutation API available is `replace_component`
  # which means every component that appears after the mutation has to
  # have a dummy place holder in the original hierarchy.
  def construct( s ):
    s.clk  = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.clk_divided = OutPort( Bits1 )
    # In the synchronous design no clock division happens
    s.clk_divided //= s.clk
