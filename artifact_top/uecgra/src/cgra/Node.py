"""
==========================================================================
Node.py
==========================================================================
Compute node for CGRA tile.

Author : Yanghui Ou
  Date : August 2, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.rtl import RegisterFile
from .enums import NodeConfig
from .Alu import Alu
from .Mul import Mul
from .AluMsg import mk_alu_msg

class Node( Component ):

  def construct( s, Type, mul_ncycles=3, DataGating=True ):

    # Local parameters

    ReqType = mk_alu_msg( Type )

    # NOTE: rename enums to workaround translation
    NodeConfig_MUL = NodeConfig.MUL
    NodeConfig_NOP = NodeConfig.NOP

    IDLE = b1(0)
    MUL  = b1(1) # Occupied by the multiplier

    # Clk and reset

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Interface

    s.recv = RecvIfcRTL( ReqType )
    s.send = SendIfcRTL( Type    )
    s.cfg  = InPort    ( Bits5   )

    # A field from cfg signal used to perform data gating
    # of ALU and MUL

    s.cfg_func = InPort( Bits5   )

    # Component

    s.alu        = Alu ( Type )
    s.mul        = Mul ( Type, DataGating )
    s.state      = Wire( Bits1 )
    s.state_next = Wire( Bits1 )

    # Wires for data gating
    s.mul_opd_a = Wire( Type )
    s.mul_opd_b = Wire( Type )
    s.alu_opd_a = Wire( Type )
    s.alu_opd_b = Wire( Type )

    s.clk //= s.mul.clk
    s.reset //= s.mul.reset

    connect( s.alu.fn,                s.cfg       )
    connect( s.alu.in0,               s.alu_opd_a )
    connect( s.alu.in1,               s.alu_opd_b )
    connect( s.mul.recv.msg.opd_a,    s.mul_opd_a )
    connect( s.mul.recv.msg.opd_b,    s.mul_opd_b )

    @s.update
    def up_data_gating():
      if s.cfg_func == NodeConfig_NOP:
        s.mul_opd_a = Type(0)
        s.mul_opd_b = Type(0)
        s.alu_opd_a = Type(0)
        s.alu_opd_b = Type(0)
      elif s.cfg_func == NodeConfig_MUL:
        s.mul_opd_a = s.recv.msg.opd_a
        s.mul_opd_b = s.recv.msg.opd_b
        s.alu_opd_a = Type(0)
        s.alu_opd_b = Type(0)
      else:
        s.mul_opd_a = Type(0)
        s.mul_opd_b = Type(0)
        s.alu_opd_a = s.recv.msg.opd_a
        s.alu_opd_b = s.recv.msg.opd_b

    # en/rdy logic
    @s.update
    def up_en_msg():
      if s.state == IDLE:
        # If configured to use multiplier
        if s.cfg == NodeConfig_MUL:
          s.mul.recv.en = s.recv.en
          s.send.en     = s.mul.send.en
          s.send.msg    = s.mul.send.msg

        # If configured to do nothing
        elif s.cfg == NodeConfig_NOP:
          s.mul.recv.en = b1(0)
          s.send.en     = b1(0)
          s.send.msg    = Type(0)

        # If configured to use ALU
        else:
          s.mul.recv.en = b1(0)
          s.send.en     = s.recv.en
          s.send.msg    = s.alu.out

      else: # MUL
        s.mul.recv.en = s.recv.en
        s.send.en     = s.mul.send.en
        s.send.msg    = s.mul.send.msg

    @s.update
    def up_rdy():
      if s.state == IDLE:
        # If configured to use multiplier
        if s.cfg == NodeConfig_MUL:
          s.mul.send.rdy = s.send.rdy
          s.recv.rdy     = s.mul.recv.rdy

        elif s.cfg == NodeConfig_NOP:
          s.mul.send.rdy = b1(0)
          s.recv.rdy     = b1(0)

        # If configured to use ALU
        else:
          s.mul.send.rdy = b1(0)
          s.recv.rdy     = s.send.rdy

      else: # MUL
        s.mul.send.rdy = s.send.rdy
        s.recv.rdy     = s.mul.recv.rdy & ( s.cfg == NodeConfig_MUL )

    # FSM logic

    @s.update_on_edge
    def up_state():
      if s.reset:
        s.state = IDLE
      else:
        s.state = s.state_next

    # If a message is received and but not send immediately, then it means
    # that the node is occupied by the multiplier and should not accept
    # messages for the ALU.
    # NOTE: We assume the multiplier has a single-entry queue here.
    @s.update
    def up_state_next():
      if s.state == IDLE:
        s.state_next = IDLE
        if s.recv.en & ~s.send.en:
          s.state_next = MUL
      else: # MUL
        s.state_next = MUL
        if ~s.recv.en & s.send.en:
          s.state_next = IDLE

  def line_trace( s ):
    return f'{s.recv}({s.cfg}|{s.state}|{s.alu.line_trace()}){s.send}'
