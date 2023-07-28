#=========================================================================
# StaticCGRA_RGALS.py
#=========================================================================
# Provides an RGALS top level component. Apart from the RGALS tiles, the
# top component also instantiates several clock dividers to generate clocks
# of different frequencies.
#
# Author : Peitian Pan
# Date   : Aug 12, 2019

from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

from clock.clock_divider import ClockDivider
from clock.clock_counter import ClockCounter
from clock.enums import CLK_NOMINAL, CLK_FAST, CLK_SLOW
from crossing.suppressor import Suppressor
from crossing.unsafe_gen import UnsafeCrossingGen
from misc.adapters import Enq2Send, Recv2Send
from fifos.BisyncQueue import BisyncQueue

from .enums import TileDirection as TD
from .TileStatic_RGALS import TileStatic_RGALS
from .RgalsClkIfc import RgalsClkIfc

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

class StaticCGRA_RGALS_wrapper( Component ):

  def construct( s, Type, CfgMsgType, ncols=2, nrows=2, mul_ncycles=0,
                 fifo_latency=0, freq_choice=2 ):

    ntiles = ncols * nrows

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )

    # Interfaces

    s.recv_n = [ RecvIfcRTL( Type ) for _ in range( ncols ) ]
    s.recv_s = [ RecvIfcRTL( Type ) for _ in range( ncols ) ]
    s.recv_w = [ RecvIfcRTL( Type ) for _ in range( nrows ) ]
    s.recv_e = [ RecvIfcRTL( Type ) for _ in range( nrows ) ]

    s.send_n = [ SendIfcRTL( Type ) for _ in range( ncols ) ]
    s.send_s = [ SendIfcRTL( Type ) for _ in range( ncols ) ]
    s.send_w = [ SendIfcRTL( Type ) for _ in range( nrows ) ]
    s.send_e = [ SendIfcRTL( Type ) for _ in range( nrows ) ]

    s.cfg    = [ InPort( CfgMsgType ) for _ in range( ntiles ) ]
    s.cfg_en = InPort( mk_bits(ntiles) )
    s.imm    = [ InPort( Type ) for _ in range( ntiles ) ]

    s.clksel = [ RecvIfcRTL( Bits2 ) for _ in range( ntiles ) ]

    s.cgra = StaticCGRA_RGALS(Type, CfgMsgType, ncols, nrows, mul_ncycles,
                              fifo_latency=fifo_latency,
                              freq_choice=freq_choice)(
      clk = s.clk,
      reset = s.reset,
      clk_reset = s.clk_reset,
      cfg_en = s.cfg_en,
    )
    for i in range(ntiles):
      s.cgra.cfg[i] //= s.cfg[i]
      s.cgra.imm[i] //= s.imm[i]
      s.cgra.clksel[i] //= s.clksel[i]

    # Input buffers to model SRAM write at the desired frequency

    s.inq_n = [ BisyncQueue( Type, num_entries = 2 )(
      w_clk = s.clk,
      r_clk = s.cgra.clk_out_n[i],
      reset = s.reset,
      enq   = s.recv_n[i],
      deq   = s.cgra.recv_n[i],
    ) for i in range( ncols ) ]
    s.inq_s = [ BisyncQueue( Type, num_entries = 2 )(
      w_clk = s.clk,
      r_clk = s.cgra.clk_out_s[i],
      reset = s.reset,
      enq   = s.recv_s[i],
      deq   = s.cgra.recv_s[i],
    ) for i in range( ncols ) ]
    s.inq_w = [ BisyncQueue( Type, num_entries = 2 )(
      w_clk = s.clk,
      r_clk = s.cgra.clk_out_w[i],
      reset = s.reset,
      enq   = s.recv_w[i],
      deq   = s.cgra.recv_w[i],
    ) for i in range( nrows ) ]
    s.inq_e = [ BisyncQueue( Type, num_entries = 2 )(
      w_clk = s.clk,
      r_clk = s.cgra.clk_out_e[i],
      reset = s.reset,
      enq   = s.recv_e[i],
      deq   = s.cgra.recv_e[i],
    ) for i in range( nrows ) ]

    # Output buffers to model SRAM read at the desired frequency

    # s.q_adapter_* converts DeqIfcRTL to SendIfcRTL

    # North 
    s.outq_adapter_n = [ Recv2Send( Type )(
      send = s.send_n[i],
    ) for i in range( ncols ) ]
    s.outq_n = [ BisyncQueue( Type, num_entries = 2 )(
      w_clk = s.cgra.clk_out_n[i],
      r_clk = s.clk,
      reset = s.reset,
      enq   = s.cgra.send_n[i],
      deq   = s.outq_adapter_n[i].recv,
    ) for i in range( ncols ) ]

    # South
    s.outq_adapter_s = [ Recv2Send( Type )(
      send = s.send_s[i],
    ) for i in range( ncols ) ]
    s.outq_s = [ BisyncQueue( Type, num_entries = 2 )(
      w_clk = s.cgra.clk_out_s[i],
      r_clk = s.clk,
      reset = s.reset,
      enq   = s.cgra.send_s[i],
      deq   = s.outq_adapter_s[i].recv,
    ) for i in range( ncols ) ]

    # West
    s.outq_adapter_w = [ Recv2Send( Type )(
      send = s.send_w[i],
    ) for i in range( nrows ) ]
    s.outq_w = [ BisyncQueue( Type, num_entries = 2 )(
      w_clk = s.cgra.clk_out_w[i],
      r_clk = s.clk,
      reset = s.reset,
      enq   = s.cgra.send_w[i],
      deq   = s.outq_adapter_w[i].recv,
    ) for i in range( nrows ) ]

    # East
    s.outq_adapter_e = [ Recv2Send( Type )(
      send = s.send_e[i],
    ) for i in range( nrows ) ]
    s.outq_e = [ BisyncQueue( Type, num_entries = 2 )(
      w_clk = s.cgra.clk_out_e[i],
      r_clk = s.clk,
      reset = s.reset,
      enq   = s.cgra.send_e[i],
      deq   = s.outq_adapter_e[i].recv,
    ) for i in range( nrows ) ]


class StaticCGRA_RGALS( Component ):

  def construct( s, Type, CfgMsgType, ncols=2, nrows=2, mul_ncycles=0,
                 fifo_latency=0, freq_choice=2 ):

    # Local parameter

    ntiles = ncols * nrows

    # Clock and resets

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )

    # Add clock dividers

    s.clk1 = Wire( Bits1 ) # fast
    s.clk2 = Wire( Bits1 ) # slow
    s.clk3 = Wire( Bits1 ) # nominal

    fast_ratio, nominal_ratio, slow_ratio = clk_choices[freq_choice]

    s.cd1 = ClockDivider( fast_ratio )(
      clk = s.clk,
      clk_reset = s.clk_reset,
      clk_divided = s.clk1,
    )
    s.cd2 = ClockDivider( slow_ratio )(
      clk = s.clk,
      clk_reset = s.clk_reset,
      clk_divided = s.clk2,
    )
    s.cd3 = ClockDivider( nominal_ratio )(
      clk = s.clk,
      clk_reset = s.clk_reset,
      clk_divided = s.clk3,
    )

    # Interface

    s.recv_n = [ RecvIfcRTL( Type ) for _ in range( ncols ) ]
    s.recv_s = [ RecvIfcRTL( Type ) for _ in range( ncols ) ]
    s.recv_w = [ RecvIfcRTL( Type ) for _ in range( nrows ) ]
    s.recv_e = [ RecvIfcRTL( Type ) for _ in range( nrows ) ]

    s.send_n = [ SendIfcRTL( Type ) for _ in range( ncols ) ]
    s.send_s = [ SendIfcRTL( Type ) for _ in range( ncols ) ]
    s.send_w = [ SendIfcRTL( Type ) for _ in range( nrows ) ]
    s.send_e = [ SendIfcRTL( Type ) for _ in range( nrows ) ]

    s.clk_out_n = [ OutPort( Bits1 ) for _ in range( ncols ) ]
    s.clk_out_s = [ OutPort( Bits1 ) for _ in range( ncols ) ]
    s.clk_out_w = [ OutPort( Bits1 ) for _ in range( nrows ) ]
    s.clk_out_e = [ OutPort( Bits1 ) for _ in range( nrows ) ]

    s.cfg    = [ InPort( CfgMsgType ) for _ in range( ntiles ) ]
    s.cfg_en = InPort( mk_bits(ntiles) )
    s.imm    = [ InPort( Type ) for _ in range( ntiles ) ]

    s.clksel = [ RecvIfcRTL( Bits2 ) for _ in range( ntiles ) ]

    # Components

    s.tiles = [
        TileStatic_RGALS( Type, CfgMsgType, mul_ncycles,  fifo_latency = fifo_latency ) for _ in range( ntiles ) ]

    s.clk_rate_out_n = [ Wire( Bits2 ) for _ in range(ncols) ]
    s.clk_rate_out_s = [ Wire( Bits2 ) for _ in range(ncols) ]
    s.clk_rate_out_w = [ Wire( Bits2 ) for _ in range(ncols) ]
    s.clk_rate_out_e = [ Wire( Bits2 ) for _ in range(ncols) ]

    # Connections

    for i in range( ntiles ):
      s.clk1 //= s.tiles[i].clk_rgals.clk1
      s.clk2 //= s.tiles[i].clk_rgals.clk2
      s.clk3 //= s.tiles[i].clk_rgals.clk3
      s.clk_reset //= s.tiles[i].clk_rgals.clk_reset
      s.reset //= s.tiles[i].reset
      connect( s.tiles[i].cfg, s.cfg[i] )
      connect( s.tiles[i].clk_rgals.clksel, s.clksel[i] )
      connect( s.tiles[i].cfg_en, s.cfg_en[i] )
      connect( s.tiles[i].imm, s.imm[i] )

    for y in range( nrows ):
      for x in range( ncols ):

        tid = y * ncols + x

        # Connect north and south ports of each tile
        if y == nrows-1:
          connect( s.tiles[tid].clk_in[TD.NORTH], s.clk_out_n[x] )
          connect( s.tiles[tid].clk_rate_in[TD.NORTH], s.clk_rate_out_n[x] )
          connect( s.clk_rate_out_n[x], s.tiles[tid].clk_rate_out[TD.NORTH] )
          connect( s.tiles[tid].recv[TD.NORTH], s.recv_n[x] )
          connect( s.tiles[tid].send[TD.NORTH], s.send_n[x] )
          connect( s.tiles[tid].clk_out[TD.NORTH], s.clk_out_n[x] )
        else:
          connect( s.tiles[tid].clk_in[TD.NORTH], s.tiles[tid+ncols].clk_out[TD.SOUTH] )
          connect( s.tiles[tid].clk_rate_in[TD.NORTH], s.tiles[tid+ncols].clk_rate_out[TD.SOUTH] )
          connect( s.tiles[tid].clk_out[TD.NORTH], s.tiles[tid+ncols].clk_in[TD.SOUTH] )
          connect( s.tiles[tid].clk_rate_out[TD.NORTH], s.tiles[tid+ncols].clk_rate_in[TD.SOUTH] )
          connect( s.tiles[tid].recv[TD.NORTH], s.tiles[tid+ncols].send[TD.SOUTH] )
          connect( s.tiles[tid].send[TD.NORTH], s.tiles[tid+ncols].recv[TD.SOUTH] )

        # Connect first row to south ports
        if y == 0:
          connect( s.tiles[tid].clk_in[TD.SOUTH], s.clk_out_s[x] )
          connect( s.tiles[tid].clk_rate_in[TD.SOUTH], s.clk_rate_out_s[x] )
          connect( s.clk_rate_out_s[x], s.tiles[tid].clk_rate_out[TD.SOUTH] )
          connect( s.tiles[tid].recv[TD.SOUTH], s.recv_s[x] )
          connect( s.tiles[tid].send[TD.SOUTH], s.send_s[x] )
          connect( s.tiles[tid].clk_out[TD.SOUTH], s.clk_out_s[x] )

        # Connect west and east ports
        if x == ncols-1:
          connect( s.tiles[tid].clk_in[TD.EAST], s.clk_out_e[y] )
          connect( s.tiles[tid].clk_rate_in[TD.EAST], s.clk_rate_out_e[y] )
          connect( s.clk_rate_out_e[y], s.tiles[tid].clk_rate_out[TD.EAST] )
          connect( s.tiles[tid].recv[TD.EAST], s.recv_e[y] )
          connect( s.tiles[tid].send[TD.EAST], s.send_e[y] )
          connect( s.tiles[tid].clk_out[TD.EAST], s.clk_out_e[y] )
        else:
          connect( s.tiles[tid].clk_in[TD.EAST], s.tiles[tid+1].clk_out[TD.WEST] )
          connect( s.tiles[tid].clk_rate_in[TD.EAST], s.tiles[tid+1].clk_rate_out[TD.WEST] )
          connect( s.tiles[tid].clk_out[TD.EAST], s.tiles[tid+1].clk_in[TD.WEST] )
          connect( s.tiles[tid].clk_rate_out[TD.EAST], s.tiles[tid+1].clk_rate_in[TD.WEST] )
          connect( s.tiles[tid].recv[TD.EAST], s.tiles[tid+1].send[TD.WEST] )
          connect( s.tiles[tid].send[TD.EAST], s.tiles[tid+1].recv[TD.WEST] )

        # Connect first column to west ports
        if x==0:
          connect( s.tiles[tid].clk_in[TD.WEST], s.clk_out_w[y] )
          connect( s.tiles[tid].clk_rate_in[TD.WEST], s.clk_rate_out_w[y] )
          connect( s.clk_rate_out_w[y], s.tiles[tid].clk_rate_out[TD.WEST] )
          connect( s.tiles[tid].recv[TD.WEST], s.recv_w[y] )
          connect( s.tiles[tid].send[TD.WEST], s.send_w[y] )
          connect( s.tiles[tid].clk_out[TD.WEST], s.clk_out_w[y] )

  def line_trace( s ):
    tile_str = ' <> '.join([ t.line_trace() for t in s.tiles ])
    return f'{tile_str}'
