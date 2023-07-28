"""
==========================================================================
enums.py
==========================================================================
Enums for CGRA tile. We don't use python Enum here since it does not
support comparison.

DO NOT MODIFY THIS FILE!

Author : Yanghui Ou
  Date : Aug 2, 2019
"""
from pymtl3 import *

class AluOp:
  CP0 = b5(0)
  CP1 = b5(1)
  ADD = b5(2)
  SUB = b5(3)
  SLL = b5(4)
  SRL = b5(5)
  AND = b5(6)
  OR  = b5(7)
  XOR = b5(8)
  EQ  = b5(9)
  NE  = b5(10)
  GT  = b5(11)
  GEQ = b5(12)
  LT  = b5(13)
  LEQ = b5(14)
  NOP = b5(31)

# TODO: Switch box is already deprecated
class SwitchBoxDirection:
  NORTH = b5(0b00001)
  SOUTH = b5(0b00010)
  WEST  = b5(0b00100)
  EAST  = b5(0b01000)
  SELF  = b5(0b10000)
  NONE  = b5(0b00000)

class NodeConfig:
  ALU_CP0 = AluOp.CP0
  ALU_CP1 = AluOp.CP1
  ALU_ADD = AluOp.ADD
  ALU_SUB = AluOp.SUB
  ALU_SLL = AluOp.SLL
  ALU_SRL = AluOp.SRL
  ALU_AND = AluOp.AND
  ALU_OR  = AluOp.OR
  ALU_XOR = AluOp.XOR
  ALU_EQ  = AluOp.EQ
  ALU_NE  = AluOp.NE
  ALU_GT  = AluOp.GT
  ALU_GEQ = AluOp.GEQ
  ALU_LT  = AluOp.LT
  ALU_LEQ = AluOp.LEQ
  MUL     = b5(15)
  NOP     = AluOp.NOP

class TileDirection:
  NORTH = 0
  SOUTH = 1
  WEST  = 2
  EAST  = 3
  SELF  = 4

class InputMux:
  NORTH = 0
  SOUTH = 1
  WEST  = 2
  EAST  = 3
  SELF  = 4

class OutputMux:
  COMPUTE = 0
  BYPASS  = 1
  BPS_ALT = 2

class RegMux:
  COMPUTE = 0
  BYPASS  = 1
  BPS_ALT = 2
  CONST   = 3

class CfgMsg:

  # Opcode
  OP_Q_TYPE = b2(0)
  OP_B_TYPE = b2(1)
  OP_I_TYPE = b2(2)

  # Func

  # Arithmetic
  CP0 = NodeConfig.ALU_CP0
  CP1 = NodeConfig.ALU_CP1
  ADD = NodeConfig.ALU_ADD
  SUB = NodeConfig.ALU_SUB
  SLL = NodeConfig.ALU_SLL
  SRL = NodeConfig.ALU_SRL
  AND = NodeConfig.ALU_AND
  OR  = NodeConfig.ALU_OR
  XOR = NodeConfig.ALU_XOR
  EQ  = NodeConfig.ALU_EQ
  NE  = NodeConfig.ALU_NE
  GT  = NodeConfig.ALU_GT
  GEQ = NodeConfig.ALU_GEQ
  LT  = NodeConfig.ALU_LT
  LEQ = NodeConfig.ALU_LEQ
  MUL = NodeConfig.MUL

  # Control
  PHI = b5(30)
  NOP = NodeConfig.NOP

  # Source direction

  SRC_NORTH = b3(0)
  SRC_SOUTH = b3(1)
  SRC_WEST  = b3(2)
  SRC_EAST  = b3(3)
  SRC_SELF  = b3(4)

  # Destination direcrtion

  DST_NORTH = SwitchBoxDirection.NORTH
  DST_SOUTH = SwitchBoxDirection.SOUTH
  DST_WEST  = SwitchBoxDirection.WEST
  DST_EAST  = SwitchBoxDirection.EAST
  DST_SELF  = SwitchBoxDirection.SELF
  DST_NONE  = SwitchBoxDirection.NONE
