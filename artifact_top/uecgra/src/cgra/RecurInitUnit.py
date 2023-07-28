"""
==========================================================================
RecurInitUnit.py
==========================================================================
Recurrence init unit which is used for kicking start the cycle in DFG.

Author : Yanghui Ou
  Date : August 24, 2019

"""
from pymtl3 import *

class RecurInitUnit( Component ):

  def construct( s ):

    # Clock and reset

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Interface

    s.deq_rdy = OutPort( Bits1 )
    s.deq_en  = InPort ( Bits1 )

    # Component

    s.state      = Wire( Bits1 )
    s.state_next = Wire( Bits1 )

    # Logic

    @s.update_on_edge
    def up_state():
      s.state = s.state_next

    @s.update
    def up_state_next():
      if s.reset:
        s.state_next = b1(1)
      elif s.state == b1(1):
        s.state_next = ~s.deq_en
      else:
        s.state_next = s.state

    @s.update
    def up_deq_rdy():
      s.deq_rdy = s.state

  def line_trace( s ):
    return f'{s.deq_en}({s.state}){s.deq_rdy}'
