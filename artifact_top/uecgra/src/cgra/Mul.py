"""
==========================================================================
Mul.py
==========================================================================
Combinational multiplier with send/recv interfaces.

Author : Yanghui Ou
  Date : July 30, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL

from .AluMsg import mk_alu_msg

class Mul( Component ):

  def construct( s, OpdType, DataGating=True ):

    # Local parameter

    ReqType = mk_alu_msg( OpdType )

    # Clk and reset

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Interface

    s.recv = RecvIfcRTL( ReqType )
    s.send = SendIfcRTL( OpdType )

    # Components

    s.opd_a_wire = Wire( OpdType )
    s.opd_b_wire = Wire( OpdType )

    # Logic

    # if DataGating:
      # # Data gating the input to save power
      # @s.update
      # def up_opd_wires():
        # if s.send.en:
          # s.opd_a_wire = s.recv.msg.opd_a
          # s.opd_b_wire = s.recv.msg.opd_b
        # else:
          # s.opd_a_wire = OpdType(0)
          # s.opd_b_wire = OpdType(0)
    # else:
      # Non-gated version is needed because we need to suppress the current
      # transaction while the signal is propagating in UE-CGRA.
    s.opd_a_wire //= s.recv.msg.opd_a
    s.opd_b_wire //= s.recv.msg.opd_b

    @s.update
    def up_mul_send():
      s.send.msg = s.opd_a_wire * s.opd_b_wire
      s.recv.rdy = s.send.rdy
      s.send.en  = s.recv.en

  def line_trace( s ):
    return f'{s.recv}(){s.send}'
