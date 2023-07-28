#=========================================================================
# clock_counter.py
#=========================================================================

from pymtl3 import *
from pymtl3.dsl import Placeholder
from pymtl3.passes.sverilog import TranslationConfigs

class ClockCounter( Placeholder, Component ):
  # taken as a blackbox during translation
  def construct( s, count_to, nbits ):
    s.clk = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.clk_cnt = OutPort( mk_bits( nbits ) )

    s.sverilog_translate = TranslationConfigs(
      v_src = "$RGALS_TOP/src/clock/ClockCounter.v",
    )
    s.yosys_translate = TranslationConfigs(
      v_src = "$RGALS_TOP/src/clock/ClockCounter.v",
    )
