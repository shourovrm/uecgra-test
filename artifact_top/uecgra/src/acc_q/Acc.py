"""
==========================================================================
Acc.py
==========================================================================
Accumulator with send/recv interfaces and a normal queue as input buffer.

Author : Yanghui Ou
  Date : July 30, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL
from pymtl3.stdlib.rtl.queues import NormalQueueRTL

class Acc( Component ):

  def construct( s, Type, nmsgs=4 ):

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Local parameters

    CountType   = mk_bits( clog2( nmsgs + 1 ) )
    INIT        = CountType(0)
    START       = CountType(1)
    DONE        = CountType(nmsgs)

    # Interface

    s.recv = RecvIfcRTL( Type )
    s.send = SendIfcRTL( Type )

    # Components

    s.count      = Wire( CountType )
    s.count_next = Wire( CountType )
    s.cur_sum    = Wire( Type )

    s.in_q = NormalQueueRTL( Type, num_entries=2 )

    s.in_q.clk //= s.clk
    s.in_q.reset //= s.reset

    # Connections

    s.recv.msg //= s.in_q.enq.msg
    s.recv.rdy //= s.in_q.enq.rdy

    @s.update
    def norm_q_en():
      s.in_q.enq.en = s.recv.en & s.in_q.enq.rdy

    s.send.msg //= s.cur_sum

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
          START if s.in_q.deq.en else
          INIT
        )

      elif s.count != DONE:
        if s.in_q.deq.en:
          s.count_next = s.count + CountType(1)
        else:
          s.count_next = s.count

      else: # s.count == DONE
        # Here wo don't use s.in_q.count as we don't have that for async
        # FIFOs.
        s.count_next = (
          START if s.send.en & s.in_q.deq.en else
          INIT  if s.send.en else
          DONE
        )

    @s.update
    def deq_send_en():
      s.send.en = ( s.count == DONE ) & s.send.rdy
      s.in_q.deq.en = (
        s.in_q.deq.rdy & s.send.rdy if s.count == DONE else
        s.in_q.deq.rdy
      )

    @s.update_on_edge
    def accum_logic():
      if s.reset:
        s.cur_sum = Type(0)
      elif s.send.en & s.in_q.deq.en:
        s.cur_sum = s.in_q.deq.msg
      elif s.send.en:
        s.cur_sum = Type(0)
      elif s.in_q.deq.en:
        s.cur_sum = s.cur_sum + s.in_q.deq.msg

  def line_trace( s ):
    return f'{s.recv}({s.count}){s.send}'
