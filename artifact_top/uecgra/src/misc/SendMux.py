"""
==========================================================================
SendMux.py
==========================================================================
Mux for send interface.

Author : Yanghui Ou
  Date : August 8, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL


class SendMux( Component ):

  def construct( s, Type, ninputs=4 ):

    # Local parameter

    s.ninputs = ninputs
    sel_type = mk_bits( clog2( ninputs ) )

    # Interface

    s.recv = [ RecvIfcRTL( Type ) for _ in range( ninputs ) ]
    s.send = SendIfcRTL( Type )
    s.sel  = InPort( sel_type )

    # Logic

    @s.update
    def up_en_msg():
      s.send.en  = b1(0)
      s.send.msg = Type()
      for i in range( ninputs ):
        if s.sel == sel_type(i):
          s.send.en  = s.recv[i].en
          s.send.msg = s.recv[i].msg

    @s.update
    def up_rdy():
      for i in range( ninputs ):
        s.recv[i].rdy = b1(0)
        if s.sel == sel_type(i):
          s.recv[i].rdy = s.send.rdy

  def line_trace( s ):
    recv_str = '|'.join([ str(s.recv[i]) for i in range( s.ninputs ) ])
    return f'{recv_str}(){s.send}'