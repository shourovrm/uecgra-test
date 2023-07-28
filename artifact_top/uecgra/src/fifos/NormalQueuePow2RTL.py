"""
-------------------------------------------------------------------------
NormalQueuePow2RTL.py
-------------------------------------------------------------------------
Normal queue optimized for power-of-2 number of entries.

Author : Yanghui Ou, Peitian Pan
  Date : Mar 23, 2019
"""

from pymtl3 import *
from pymtl3.stdlib.ifcs import DeqIfcRTL, EnqIfcRTL
from pymtl3.stdlib.rtl import RegisterFile
from pymtl3.stdlib.rtl.queues import NormalQueue1EntryRTL

#-------------------------------------------------------------------------
# Dpath and Ctrl
#-------------------------------------------------------------------------

class NormalQueuePow2DpathRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq_msg =  InPort( EntryType )
    s.deq_msg = OutPort( EntryType )

    s.wen   = InPort( Bits1 )
    s.waddr = InPort( mk_bits( clog2( num_entries ) ) )
    s.raddr = InPort( mk_bits( clog2( num_entries ) ) )

    # Component

    s.queue = RegisterFile( EntryType, num_entries )(
      raddr = { 0: s.raddr   },
      rdata = { 0: s.deq_msg },
      wen   = { 0: s.wen     },
      waddr = { 0: s.waddr   },
      wdata = { 0: s.enq_msg },
    )

class NormalQueuePow2CtrlRTL( Component ):

  def construct( s, num_entries=2 ):

    # Constants

    addr_nbits     = clog2    ( num_entries   )

    PtrType        = mk_bits  ( addr_nbits    )
    PtrWrapBitType = mk_bits  ( addr_nbits+1  )

    # Interface

    s.enq_en  = InPort ( Bits1   )
    s.enq_rdy = OutPort( Bits1   )
    s.deq_en  = InPort ( Bits1   )
    s.deq_rdy = OutPort( Bits1   )

    s.wen     = OutPort( Bits1   )
    s.waddr   = OutPort( PtrType )
    s.raddr   = OutPort( PtrType )

    # Registers

    s.w_ptr_with_wrapbit = Wire( PtrWrapBitType )
    s.r_ptr_with_wrapbit = Wire( PtrWrapBitType )

    s.w_ptr = Wire( PtrType )
    s.r_ptr = Wire( PtrType )

    s.full = Wire( Bits1 )
    s.empty = Wire( Bits1 )

    # Connections

    s.w_ptr //= s.w_ptr_with_wrapbit[0:addr_nbits]
    s.r_ptr //= s.r_ptr_with_wrapbit[0:addr_nbits]
    s.waddr //= s.w_ptr
    s.raddr //= s.r_ptr

    @s.update_on_edge
    def upblk_w_ptr():
      if s.reset:
        s.w_ptr_with_wrapbit = PtrWrapBitType(0)
      elif s.enq_en and s.enq_rdy:
        s.w_ptr_with_wrapbit = s.w_ptr_with_wrapbit + PtrWrapBitType(1)

    @s.update_on_edge
    def upblk_r_ptr():
      if s.reset:
        s.r_ptr_with_wrapbit = PtrWrapBitType(0)
      elif s.deq_en and s.deq_rdy:
        s.r_ptr_with_wrapbit = s.r_ptr_with_wrapbit + PtrWrapBitType(1)

    @s.update
    def upblk_full():
      s.full = (s.w_ptr == s.r_ptr) and (s.w_ptr_with_wrapbit != s.r_ptr_with_wrapbit)

    @s.update
    def upblk_empty():
      s.empty = (s.w_ptr_with_wrapbit == s.r_ptr_with_wrapbit)

    @s.update
    def upblk_output():
      s.enq_rdy = not s.full
      s.deq_rdy = not s.empty
      s.wen     = (s.enq_en and s.enq_rdy)

#-------------------------------------------------------------------------
# NormalQueuePow2RTL
#-------------------------------------------------------------------------

class NormalQueuePow2RTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    assert (num_entries == 1) or ( (num_entries >= 2) and (num_entries % 2 == 0) )

    # Interface

    s.enq   = EnqIfcRTL( EntryType )
    s.deq   = DeqIfcRTL( EntryType )

    # Components

    if num_entries == 1:
      s.q = NormalQueue1EntryRTL( EntryType )
      connect( s.enq, s.q.enq )
      connect( s.deq, s.q.deq )

    else:
      s.ctrl  = NormalQueuePow2CtrlRTL ( num_entries )
      s.dpath = NormalQueuePow2DpathRTL( EntryType, num_entries )

      # Connect ctrl to data path

      connect( s.ctrl.wen,     s.dpath.wen     )
      connect( s.ctrl.waddr,   s.dpath.waddr   )
      connect( s.ctrl.raddr,   s.dpath.raddr   )

      # Connect to interface

      connect( s.enq.en,  s.ctrl.enq_en   )
      connect( s.enq.rdy, s.ctrl.enq_rdy  )
      connect( s.deq.en,  s.ctrl.deq_en   )
      connect( s.deq.rdy, s.ctrl.deq_rdy  )
      connect( s.enq.msg, s.dpath.enq_msg )
      connect( s.deq.msg, s.dpath.deq_msg )

  # Line trace

  def line_trace( s ):
    return "{}(){}".format( s.enq, s.deq )
