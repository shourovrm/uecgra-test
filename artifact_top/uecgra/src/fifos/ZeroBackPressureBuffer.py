#=========================================================================
# ZeroBackPressureBuffer.py
#=========================================================================
# Buffer that causes no back pressure on its input.
#
# Author : Peitian Pan
# Date   : Sep 8, 2019

from pymtl3 import *
from pymtl3.stdlib.ifcs import EnqIfcRTL, DeqIfcRTL
from pymtl3.stdlib.rtl import RegRst, RegEnRst

class ZeroBackPressureBuffer( Component ):
  # Only contains 1 register

  def construct( s, Type ):

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Interface

    s.enq = EnqIfcRTL( Type )
    s.deq = DeqIfcRTL( Type )

    # Components

    s.full = RegRst( Bits1 )(
      clk   = s.clk,
      reset = s.reset,
    )

    s.ele = RegEnRst( Type )(
      clk   = s.clk,
      reset = s.reset,
      en    = s.enq.en,
      in_   = s.enq.msg,
    )

    @s.update
    def upblk_full():
      # Pipeline behavior
      if s.enq.en == b1(1):
        s.full.in_ = b1(1)
      elif s.deq.en == b1(1):
        s.full.in_ = b1(0)
      else:
        s.full.in_ = s.full.out

    # Connections

    s.enq.rdy //= b1(1)
    s.deq.msg //= s.ele.out
    s.deq.rdy //= s.full.out
