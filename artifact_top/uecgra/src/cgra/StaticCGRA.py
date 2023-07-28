"""
==========================================================================
StaticCGRA.py
==========================================================================
RTL implementation of elastic static CGRA implementation.

Author : Yanghui Ou
  Date : August 10, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

from .enums import TileDirection as TD
from .TileStatic import TileStatic

class StaticCGRA( Component ):

  def construct( s, Type, CfgMsgType, ncols=2, nrows=2, mul_ncycles=0, elasticity="elastic", fifo_depth=2 ):

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Local parameter

    ntiles = ncols * nrows
    s.ntiles = ntiles

    # Interface

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

    # Components

    s.tiles = [ TileStatic( Type, CfgMsgType, mul_ncycles, elasticity, fifo_depth=fifo_depth ) for _ in range( ntiles ) ]

    # Connections

    for i in range( ntiles ):
      s.clk //= s.tiles[i].clk
      s.reset //= s.tiles[i].reset
      connect( s.tiles[i].cfg,    s.cfg[i]    )
      connect( s.tiles[i].cfg_en, s.cfg_en[i] )
      connect( s.tiles[i].imm,    s.imm[i]    )

    for y in range( nrows ):
      for x in range( ncols ):

        tid = y * ncols + x

        # Connect north and south ports of each tile
        if y == nrows-1:
          connect( s.tiles[tid].recv[TD.NORTH], s.recv_n[x] )
          connect( s.tiles[tid].send[TD.NORTH], s.send_n[x] )
        else:
          connect( s.tiles[tid].recv[TD.NORTH], s.tiles[tid+ncols].send[TD.SOUTH] )
          connect( s.tiles[tid].send[TD.NORTH], s.tiles[tid+ncols].recv[TD.SOUTH] )

        # Connect first row to south ports
        if y == 0:
          connect( s.tiles[tid].recv[TD.SOUTH], s.recv_s[x] )
          connect( s.tiles[tid].send[TD.SOUTH], s.send_s[x] )

        # Connect west and east ports
        if x == ncols-1:
          connect( s.tiles[tid].recv[TD.EAST], s.recv_e[y] )
          connect( s.tiles[tid].send[TD.EAST], s.send_e[y] )
        else:
          connect( s.tiles[tid].recv[TD.EAST], s.tiles[tid+1].send[TD.WEST] )
          connect( s.tiles[tid].send[TD.EAST], s.tiles[tid+1].recv[TD.WEST] )

        # Connect first column to west ports
        if x==0:
          connect( s.tiles[tid].recv[TD.WEST], s.recv_w[y] )
          connect( s.tiles[tid].send[TD.WEST], s.send_w[y] )

  def line_trace( s ):
    trace_lst = [ f'  [{i:2}]:{s.tiles[i].line_trace()}' for i in range(s.ntiles) ]
    tile_str = '\n'.join( trace_lst )
    return f'\n{trace_lst[11]}'
    return f'\n{tile_str}'
