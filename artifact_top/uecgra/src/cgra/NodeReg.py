"""
==========================================================================
NodeReg.py
==========================================================================
A register with recv interface for CGRA tile to hold temporary value.

Author : Yanghui Ou
  Date : August 6, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.rtl import RegEn
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

# TODO: add a load port
class NodeReg( Component ):

  def construct( s, Type ):

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    s.recv = RecvIfcRTL( Type )
    s.out  = OutPort( Type )

    s.data_reg = RegEn( Type )(
      clk   = s.clk,
      reset = s.reset,
      en    = s.recv.en,
      in_   = s.recv.msg,
      out   = s.out,
    )

    s.recv.rdy //= b1(1)
