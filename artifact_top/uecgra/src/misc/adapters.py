"""
==========================================================================
adapters.py
==========================================================================
Adapters for UE-CGRA project.

Author : Yanghui Ou
  Date : August 12, 2019

"""

from pymtl3 import *
from pymtl3.stdlib.ifcs import InValRdyIfc, OutValRdyIfc, RecvIfcRTL, SendIfcRTL, \
                               DeqIfcRTL, EnqIfcRTL

#-------------------------------------------------------------------------
# ValRdy2EnRdy
#-------------------------------------------------------------------------

class ValRdy2EnRdy( Component ):

  def construct( s, MsgType ):

    s.in_ = InValRdyIfc( MsgType )
    s.out = SendIfcRTL( MsgType )

    @s.update
    def comb_logic0():
      s.in_.rdy = s.out.rdy

    @s.update
    def comb_logic1():
      s.out.en  = s.out.rdy and s.in_.val

    @s.update
    def comb_logic2():
      s.out.msg = s.in_.msg

  def line_trace( s ):

    return "{} | {}".format( s.in_, s.out )

#-------------------------------------------------------------------------
# EnRdy2ValRdy
#-------------------------------------------------------------------------

class EnRdy2ValRdy( Component ):

  def construct( s, MsgType ):

    s.in_ = RecvIfcRTL( MsgType )
    s.out = OutValRdyIfc( MsgType )

    @s.update
    def comb_logic0():
      s.in_.rdy = s.out.rdy

    @s.update
    def comb_logic1():
      s.out.val = s.in_.en

    @s.update
    def comb_logic2():
      s.out.msg = s.in_.msg

  def line_trace( s ):

    return "{} | {}".format( s.in_, s.out )

#-------------------------------------------------------------------------
# Recv2Send
#-------------------------------------------------------------------------

class Recv2Send( Component ):

  def construct( s, MsgType ):

    s.recv = RecvIfcRTL( MsgType )
    s.send = SendIfcRTL( MsgType )

    s.recv //= s.send

  def line_trace( s ):

    return "{} | {}".format( s.recv, s.send )

#-------------------------------------------------------------------------
# Deq2Send
#-------------------------------------------------------------------------

class Enq2Send( Component ):

  def construct( s, MsgType ):

    s.enq = EnqIfcRTL( MsgType )
    s.send = SendIfcRTL( MsgType )
    s.adapter = Recv2Send( MsgType )(
      recv = s.enq,
      send = s.send,
    )

  def line_trace( s ):

    return "{} | {}".format( s.deq, s.send )
