"""
==========================================================================
Mul.py
==========================================================================
Multiplier with send/recv interfaces and a normal queue as input buffer.

Author : Yanghui Ou
  Date : July 30, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL
from pymtl3.stdlib.rtl.queues import PipeQueueRTL

#-------------------------------------------------------------------------
# Multi-cycle multiplier
#-------------------------------------------------------------------------

class MulMcycle( Component ):

  def construct( s, OpdType, ncycles=3 ):

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Local parameter

    ReqType   = mk_bits( OpdType.nbits * 2 )
    CountType = mk_bits( clog2( ncycles + 1 ) )
    INIT      = CountType(0)
    START     = CountType(1)
    DONE      = CountType(ncycles)
    opd_a     = slice(0,             OpdType.nbits  )
    opd_b     = slice(OpdType.nbits, OpdType.nbits*2)

    # Interface

    s.recv = RecvIfcRTL( ReqType )
    s.send = SendIfcRTL( OpdType )

    # Component

    s.count      = Wire( CountType )
    s.count_next = Wire( CountType )

    # We use single entry queue to simplify control logic for CGRA.ls

    s.in_q = PipeQueueRTL( ReqType, num_entries=1 )

    s.in_q.clk //= s.clk
    s.in_q.reset //= s.reset

    # Connectionns

    s.recv.msg //= s.in_q.enq.msg
    s.recv.rdy //= s.in_q.enq.rdy

    @s.update
    def pipe_q_en():
      s.in_q.enq.en = s.recv.en & s.in_q.enq.rdy

    # Logic

    @s.update_on_edge
    def state_trans():
      if s.reset:
        s.count = INIT
      else:
        s.count = s.count_next

    @s.update
    def next_state_logic():
      if s.count == INIT:
        s.count_next = (
          START if s.in_q.deq.rdy | s.in_q.enq.en else
          INIT
        )

      elif s.count != DONE:
        s.count_next = s.count + CountType(1)

      else: # s.count == DONE
        # Here wo don't use s.in_q.count as we don't have that for async
        # FIFOs.
        s.count_next = (
          START if s.send.en & ( ~s.in_q.enq.rdy | s.in_q.enq.en ) else
          INIT  if s.send.en else
          DONE
        )

    @s.update
    def deq_send_en():
      s.in_q.deq.en = ( s.count == DONE ) & s.in_q.deq.rdy & s.send.rdy
      s.send.en     = ( s.count == DONE ) & s.in_q.deq.rdy & s.send.rdy
      s.send.msg    = s.in_q.deq.msg[opd_a] * s.in_q.deq.msg[opd_b]

  def line_trace( s ):
    return f'{s.recv}({s.count}){s.send}'

#-------------------------------------------------------------------------
# Combinational multiplier
#-------------------------------------------------------------------------

class MulComb( Component ):

  def construct( s, OpdType, DataGating = True ):

    # Local parameter

    ReqType = mk_bits( OpdType.nbits * 2 )
    opd_a   = slice(0,             OpdType.nbits  )
    opd_b   = slice(OpdType.nbits, OpdType.nbits*2)

    # Interface

    s.recv = RecvIfcRTL( ReqType )
    s.send = SendIfcRTL( OpdType )

    # Components

    s.opd_a_wire = Wire( OpdType )
    s.opd_b_wire = Wire( OpdType )

    # Logic

    if DataGating:
      # Data gating the input to save power
      @s.update
      def up_opd_wires():
        if s.send.en:
          s.opd_a_wire = s.recv.msg[opd_a]
          s.opd_b_wire = s.recv.msg[opd_b]
        else:
          s.opd_a_wire = OpdType(0)
          s.opd_b_wire = OpdType(0)
    else:
      s.opd_a_wire //= s.recv.msg[opd_a]
      s.opd_b_wire //= s.recv.msg[opd_b]

    @s.update
    def up_mul_send():
      s.send.msg = s.opd_a_wire * s.opd_b_wire
      s.recv.rdy = s.send.rdy
      s.send.en  = s.recv.en

  def line_trace( s ):
    return f'{s.recv}(){s.send}'

class Mul( Component ):

  def construct( s, OpdType, ncycles = 3, DataGating = True ):

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Local parameter

    ReqType = mk_bits( OpdType.nbits * 2 )

    # Interface

    s.recv = RecvIfcRTL( ReqType )
    s.send = SendIfcRTL( OpdType )

    if ncycles == 0:
      s.mul = MulComb( OpdType, DataGating )
      connect( s.recv,     s.mul.recv  )
      connect( s.mul.send, s.send      )
    else:
      s.mul = MulMcycle( OpdType, ncycles )
      connect( s.recv,     s.mul.recv  )
      connect( s.mul.send, s.send      )
      connect( s.clk,      s.mul.clk   )
      connect( s.reset,    s.mul.reset )

  def line_trace( s ):
    return f'{s.recv}(){s.send}'

