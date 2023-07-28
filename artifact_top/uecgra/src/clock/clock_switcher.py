#=========================================================================
# clock_switcher.py
#=========================================================================
# Provides a Placeholder for the Verilog clock switcher.
#
# Author : Peitian Pan
# Date   : Aug 12, 2019

from pymtl3 import *
from pymtl3.dsl import Placeholder
from pymtl3.passes.sverilog import TranslationConfigs

class ClockSwitcher_3( Placeholder, Component ):
  # taken as a blackbox during translation
  def construct( s ):
    s.clk1 = InPort( Bits1 )
    s.clk2 = InPort( Bits1 )
    s.clk3 = InPort( Bits1 )

    s.clk_reset = InPort( Bits1 )
    s.switch_val = InPort( Bits1 )
    s.switch_rdy = OutPort( Bits1 )
    s.switch_msg = InPort( Bits2 )
    s.clk_out = OutPort( Bits1 )
    s.sverilog_translate = TranslationConfigs(
      v_src = "$RGALS_TOP/src/clock/ClockSwitcher.v",
    )
    s.yosys_translate = TranslationConfigs(
      v_src = "$RGALS_TOP/src/clock/ClockSwitcher.v",
    )
