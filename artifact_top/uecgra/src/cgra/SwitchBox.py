"""
==========================================================================
SwitchBox.py
==========================================================================
Switch box for routing CGRA data.

Author : Yanghui Ou
  Date : August 1, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL
from .enums import SwitchBoxDirection as SB_Dir

class SwitchBox( Component ):

  def construct( s, Type ):

    # Localparameter

    SB_Dir_NONE = SB_Dir.NONE

    # Interface

    s.recv  = RecvIfcRTL( Type )
    s.send  = [ SendIfcRTL( Type ) for _ in range(5) ]
    s.cfg   = InPort( Bits5 )

    # Compontnent

    s.rdy_cfg = Wire( Bits5 )

    # Logic

    # Route en and msg
    @s.update
    def up_en_msg():
      for i in range(5):
        if s.cfg[i]:
          s.send[i].en  = s.recv.en
          s.send[i].msg = s.recv.msg
        else:
          s.send[i].en  = b1(0)
          s.send[i].msg = Type(0)

    # Route rdy - note that now we only assert rdy when all receivers are
    # ready.
    @s.update
    def up_rdy():
      if s.cfg == SB_Dir_NONE:
        s.recv.rdy = b1(0)
      else:
        for i in range(5):
          if s.cfg[i]:
            s.rdy_cfg[i] = s.send[i].rdy
          else:
            s.rdy_cfg[i] = b1(1)
        s.recv.rdy = reduce_and( s.rdy_cfg )

  def line_trace( s ):
    send_str = '|'.join([ str(s.send[i]) for i in range(5) ])
    return f'{s.recv}({s.cfg}){send_str}'
