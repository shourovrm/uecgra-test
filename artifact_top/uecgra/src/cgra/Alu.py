"""
==========================================================================
Alu.py
==========================================================================
Simple ALU for CGRA tile.

Author : Yanghui Ou
  Date : Aug 2, 2019
"""
from pymtl3 import *
from .enums import AluOp

class Alu( Component ):

  def construct( s, Type ):

    # Local parameters

    shamt = clog2( Type.nbits )

    # NOTE:Rename enums to workaround verilog transaltion
    AluOp_CP0 = AluOp.CP0
    AluOp_CP1 = AluOp.CP1
    AluOp_ADD = AluOp.ADD
    AluOp_SUB = AluOp.SUB
    AluOp_SLL = AluOp.SLL
    AluOp_SRL = AluOp.SRL
    AluOp_AND = AluOp.AND
    AluOp_OR  = AluOp.OR
    AluOp_XOR = AluOp.XOR
    AluOp_EQ  = AluOp.EQ
    AluOp_NE  = AluOp.NE
    AluOp_GT  = AluOp.GT
    AluOp_GEQ = AluOp.GEQ
    AluOp_LT  = AluOp.LT
    AluOp_LEQ = AluOp.LEQ

    # Interface

    s.in0 = InPort ( Type  )
    s.in1 = InPort ( Type  )
    s.fn  = InPort ( Bits5 )

    s.out = OutPort( Type  )

    # Data gating wires

    s.cp0_wire = Wire( Type )
    s.cp1_wire = Wire( Type )

    s.add_a_wire = Wire( Type )
    s.add_b_wire = Wire( Type )

    s.sub_a_wire = Wire( Type )
    s.sub_b_wire = Wire( Type )

    s.sll_a_wire = Wire( Type )
    s.sll_b_wire = Wire( Type )

    s.srl_a_wire = Wire( Type )
    s.srl_b_wire = Wire( Type )

    s.and_a_wire = Wire( Type )
    s.and_b_wire = Wire( Type )

    s.or_a_wire  = Wire( Type )
    s.or_b_wire  = Wire( Type )

    s.xor_a_wire = Wire( Type )
    s.xor_b_wire = Wire( Type )

    s.eq_a_wire  = Wire( Type )
    s.eq_b_wire  = Wire( Type )

    s.gt_a_wire  = Wire( Type )
    s.gt_b_wire  = Wire( Type )

    s.a_eq_b     = Wire( Bits1 )
    s.a_gt_b     = Wire( Bits1 )

    @s.update
    def up_data_gating():
      s.cp0_wire   = s.in0 if s.fn == AluOp_CP0 else Type(0)
      s.cp1_wire   = s.in1 if s.fn == AluOp_CP1 else Type(0)

      s.add_a_wire = s.in0 if s.fn == AluOp_ADD else Type(0)
      s.add_b_wire = s.in1 if s.fn == AluOp_ADD else Type(0)

      s.sub_a_wire = s.in0 if s.fn == AluOp_SUB else Type(0)
      s.sub_b_wire = s.in1 if s.fn == AluOp_SUB else Type(0)

      s.sll_a_wire = s.in0 if s.fn == AluOp_SLL else Type(0)
      s.sll_b_wire = s.in1 if s.fn == AluOp_SLL else Type(0)

      s.srl_a_wire = s.in0 if s.fn == AluOp_SRL else Type(0)
      s.srl_b_wire = s.in1 if s.fn == AluOp_SRL else Type(0)

      s.and_a_wire = s.in0 if s.fn == AluOp_AND else Type(0)
      s.and_b_wire = s.in1 if s.fn == AluOp_AND else Type(0)

      s.or_a_wire  = s.in0 if s.fn == AluOp_OR  else Type(0)
      s.or_b_wire  = s.in1 if s.fn == AluOp_OR  else Type(0)

      s.xor_a_wire = s.in0 if s.fn == AluOp_XOR else Type(0)
      s.xor_b_wire = s.in1 if s.fn == AluOp_XOR else Type(0)

      if ( s.fn == AluOp_EQ  ) | ( s.fn == AluOp_NE ) | \
         ( s.fn == AluOp_GEQ ) | ( s.fn == AluOp_LT ):
        s.eq_a_wire = s.in0
        s.eq_b_wire = s.in1
      else:
        s.eq_a_wire = Type(0)
        s.eq_b_wire = Type(0)

      if ( s.fn == AluOp_GT ) | ( s.fn == AluOp_GEQ ) | \
         ( s.fn == AluOp_LT ) | ( s.fn == AluOp_LEQ ):
        s.gt_a_wire = s.in0
        s.gt_b_wire = s.in1
      else:
        s.gt_a_wire = Type(0)
        s.gt_b_wire = Type(0)

    @s.update
    def up_eq_gt_wire():
      s.a_eq_b = s.eq_a_wire == s.eq_b_wire
      s.a_gt_b = s.gt_a_wire > s.gt_b_wire

    @s.update
    def comb_logic():
      if   s.fn == AluOp_CP0: s.out = s.cp0_wire                                    # COPY OP0
      elif s.fn == AluOp_CP1: s.out = s.cp1_wire                                    # COPY OP1
      elif s.fn == AluOp_ADD: s.out = s.add_a_wire + s.add_b_wire                   # ADD
      elif s.fn == AluOp_SUB: s.out = s.sub_a_wire - s.sub_b_wire                   # SUB
      elif s.fn == AluOp_SLL: s.out = s.sll_a_wire << s.sll_b_wire[0:shamt]         # SLL
      elif s.fn == AluOp_SRL: s.out = s.srl_a_wire >> s.srl_b_wire[0:shamt]         # SRL
      elif s.fn == AluOp_AND: s.out = s.and_a_wire & s.and_b_wire                   # AND
      elif s.fn == AluOp_OR : s.out = s.or_a_wire  | s.or_b_wire                    # OR
      elif s.fn == AluOp_XOR: s.out = s.xor_a_wire ^ s.xor_b_wire                   # XOR
      elif s.fn == AluOp_EQ : s.out = Type(1) if  s.a_eq_b else Type(0)             # EQ
      elif s.fn == AluOp_NE : s.out = Type(1) if ~s.a_eq_b else Type(0)             # NE
      elif s.fn == AluOp_GT : s.out = Type(1) if  s.a_gt_b else Type(0)             # GT
      elif s.fn == AluOp_GEQ: s.out = Type(1) if  s.a_gt_b |  s.a_eq_b else Type(0) # GEQ
      elif s.fn == AluOp_LT : s.out = Type(1) if ~s.a_gt_b & ~s.a_eq_b else Type(0) # GEQ
      elif s.fn == AluOp_LEQ: s.out = Type(1) if ~s.a_gt_b             else Type(0) # GEQ

      else:                   s.out = Type(0)                                      # NOP

  def line_trace( s ):
    fn_str = (
      'cp0' if s.fn == AluOp.CP0 else
      'cp1' if s.fn == AluOp.CP1 else
      'add' if s.fn == AluOp.ADD else
      'sub' if s.fn == AluOp.SUB else
      'sll' if s.fn == AluOp.SLL else
      'srl' if s.fn == AluOp.SRL else
      'and' if s.fn == AluOp.AND else
      'or ' if s.fn == AluOp.OR  else
      'xor' if s.fn == AluOp.XOR else
      'eq ' if s.fn == AluOp.EQ  else
      'ne ' if s.fn == AluOp.NE  else
      'gt ' if s.fn == AluOp.GT  else
      'geq' if s.fn == AluOp.GEQ else
      'lt ' if s.fn == AluOp.LT  else
      'leq' if s.fn == AluOp.LEQ else
      'nop'
    )
    return f'{s.in0}<{fn_str}>{s.in1}(){s.out}'
