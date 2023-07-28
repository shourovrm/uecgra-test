#=========================================================================
# tile_suppress.py
#=========================================================================
# All suppression and related logic needed for a single tile.
#
# Author : Peitian Pan
# Date   : Aug 30, 2019

from pymtl3 import *

from crossing.suppressor import Suppressor
from crossing.unsafe_gen import UnsafeCrossingGen
from crossing.tile_ifcs import TileSuppressClkIfc, TileSuppressQueueIfc

class TileSuppress( Component ):
  def construct( s ):

    # Interfaces

    s.reset = InPort( Bits1 )
    s.clk_ifc = TileSuppressClkIfc()
    s.q_ifcs = [ TileSuppressQueueIfc() for _ in range(4) ]

    # Wires

    s.unsafe_bus = Wire( Bits9 )

    # Components

    s.unsafe_gen = UnsafeCrossingGen()(
      clk1 = s.clk_ifc.clk1,
      clk2 = s.clk_ifc.clk2,
      clk3 = s.clk_ifc.clk3,
      clk_reset = s.clk_ifc.clk_reset,
      unsafe_bus = s.unsafe_bus,
    )

    s.suppressors = [ Suppressor()(
      reset = s.reset,
      r_clk = s.clk_ifc.domain_clk,
      r_clk_rate = s.clk_ifc.domain_clk_rate,
      w_clk_rate = s.q_ifcs[i].clk_rate,
      is_empty = s.q_ifcs[i].is_empty,
      is_empty_next = s.q_ifcs[i].is_empty_next,
      unsafe_bus = s.unsafe_bus,
      from_left = s.q_ifcs[i].from_q_deq_rdy,
      to_right = s.q_ifcs[i].to_ctrl_deq_rdy,
      from_right = s.q_ifcs[i].from_ctrl_deq_en,
      to_left = s.q_ifcs[i].to_q_deq_en,
    ) for i in range(4) ]
