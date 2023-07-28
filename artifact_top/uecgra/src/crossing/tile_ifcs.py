#=========================================================================
# tile_ifcs.py
#=========================================================================
# Interfaces used by RGALS tiles.
#
# Author : Peitian Pan
# Date   : Aug 30, 2019

from pymtl3 import *

class TileSuppressClkIfc( Interface ):
  def construct( s ):
    s.clk1 = InPort( Bits1 )
    s.clk2 = InPort( Bits1 )
    s.clk3 = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.domain_clk = InPort( Bits1 )
    s.domain_clk_rate = InPort( Bits2 )

class TileSuppressQueueIfc( Interface ):
  def construct( s ):
    s.clk_rate = InPort( Bits2 )
    s.is_empty = InPort( Bits1 )
    s.is_empty_next = InPort( Bits1 )
    s.from_q_deq_rdy = InPort( Bits1 )
    s.to_ctrl_deq_rdy = OutPort( Bits1 )
    s.from_ctrl_deq_en = InPort( Bits1 )
    s.to_q_deq_en = OutPort( Bits1 )
