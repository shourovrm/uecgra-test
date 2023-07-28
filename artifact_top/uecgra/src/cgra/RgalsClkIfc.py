#=========================================================================
# RgalsClkIfc.py
#=========================================================================
# An interface that includes divided clock signals, clock reset, and
# clock selection signals. These signals will be used in an RGALS design
# to distribute the desired clock to different PE's.
#
# Author: Peitian Pan
# Date  : Aug 12, 2019

from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL

class RgalsClkIfc( Interface ):

  def construct( s ):
    # TODO: Currently only supports two divided clocks because the Verilog
    # clock switcher is not parameterized.
    s.clk1 = InPort( Bits1 )
    s.clk2 = InPort( Bits1 )
    s.clk3 = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.clksel = RecvIfcRTL( Bits2 )
