#========================================================================
# TinyRV2 Instruction Type
#========================================================================
# Instruction types are similar to message types but are strictly used
# for communication within a TinyRV2-based processor. Instruction
# "messages" can be unpacked into the various fields as defined by the
# TinyRV2 ISA, as well as be constructed from specifying each field
# explicitly. The 32-bit instruction has different fields depending on
# the format of the instruction used. The following are the various
# instruction encoding formats used in the TinyRV2 ISA.
#
#  31          25 24   20 19   15 14    12 11          7 6      0
# | funct7       | rs2   | rs1   | funct3 | rd          | opcode |  R-type
# | imm[11:0]            | rs1   | funct3 | rd          | opcode |  I-type, I-imm
# | imm[11:5]    | rs2   | rs1   | funct3 | imm[4:0]    | opcode |  S-type, S-imm
# | imm[12|10:5] | rs2   | rs1   | funct3 | imm[4:1|11] | opcode |  SB-type,B-imm
# | imm[31:12]                            | rd          | opcode |  U-type, U-imm
# | imm[20|10:1|11|19:12]                 | rd          | opcode |  UJ-type,J-imm

from pymtl3 import *

#-------------------------------------------------------------------------
# TinyRV2 Instruction Fields
#-------------------------------------------------------------------------

OPCODE = slice(  0,  7 )
FUNCT3 = slice( 12, 15 )
FUNCT7 = slice( 25 ,32 )

RD     = slice(  7, 12 )
RS1    = slice( 15, 20 )
RS2    = slice( 20, 25 )
SHAMT  = slice( 20, 25 )

I_IMM  = slice( 20, 32 )
CSRNUM = slice( 20, 32 )

S_IMM0 = slice(  7, 12 )
S_IMM1 = slice( 25, 32 )

B_IMM0 = slice(  8, 12 )
B_IMM1 = slice( 25, 31 )
B_IMM2 = slice(  7,  8 )
B_IMM3 = slice( 31, 32 )

U_IMM  = slice( 12, 32 )

J_IMM0 = slice( 21, 31 )
J_IMM1 = slice( 20, 21 )
J_IMM2 = slice( 12, 20 )
J_IMM3 = slice( 31, 32 )

#-------------------------------------------------------------------------
# TinyRV2 Instruction Definitions
#-------------------------------------------------------------------------
NOP   = b8(0)  # 00000000000000000000000000000000

# Load
LB    = b8(1)  # ?????????????????000?????0000011
LH    = b8(2)  # ?????????????????001?????0000011
LW    = b8(3)  # ?????????????????010?????0000011
LBU   = b8(4)  # ?????????????????100?????0000011
LHU   = b8(5)  # ?????????????????101?????0000011

# Store
SB    = b8(6)  # ?????????????????000?????0100011
SH    = b8(7)  # ?????????????????001?????0100011
SW    = b8(8)  # ?????????????????010?????0100011

# Shifts
SLL   = b8(9)  # 0000000??????????001?????0110011
SLLI  = b8(10) # 0000000??????????001?????0010011
SRL   = b8(11) # 0000000??????????101?????0110011
SRLI  = b8(12) # 0000000??????????101?????0010011
SRA   = b8(13) # 0100000??????????101?????0110011
SRAI  = b8(14) # 0100000??????????101?????0010011

# Arithmetic
ADD   = b8(15) # 0000000??????????000?????0110011
ADDI  = b8(16) # ?????????????????000?????0010011
SUB   = b8(17) # 0100000??????????000?????0110011
LUI   = b8(18) # ?????????????????????????0110111
AUIPC = b8(19) # ?????????????????????????0010111

# Logical
XOR   = b8(20) # 0000000??????????100?????0110011
XORI  = b8(21) # ?????????????????100?????0010011
OR    = b8(22) # 0000000??????????110?????0110011
ORI   = b8(23) # ?????????????????110?????0010011
AND   = b8(24) # 0000000??????????111?????0110011
ANDI  = b8(25) # ?????????????????111?????0010011

# Compare
SLT   = b8(26) # 0000000??????????010?????0110011
SLTI  = b8(27) # ?????????????????010?????0010011
SLTU  = b8(28) # 0000000??????????011?????0110011
SLTIU = b8(29) # ?????????????????011?????0010011

# Branches
BEQ   = b8(30) # ?????????????????000?????1100011
BNE   = b8(31) # ?????????????????001?????1100011
BLT   = b8(32) # ?????????????????100?????1100011
BGE   = b8(33) # ?????????????????101?????1100011
BLTU  = b8(34) # ?????????????????110?????1100011
BGEU  = b8(35) # ?????????????????111?????1100011

# Jump & Link
JAL   = b8(36) # ?????????????????????????1101111
JALR  = b8(37) # ?????????????????000?????1100111

# Multiply
MUL   = b8(38) # 0000001??????????000?????0110011
MULH  = b8(39) # 0000001??????????001?????0110011
MULHSU= b8(40) # 0000001??????????010?????0110011
MULHU = b8(41) # 0000001??????????011?????0110011
DIV   = b8(42) # 0000001??????????100?????0110011
DIVU  = b8(43) # 0000001??????????101?????0110011
REM   = b8(44) # 0000001??????????110?????0110011
REMU  = b8(45) # 0000001??????????111?????0110011

# Misc
CSRR  = b8(46) # ????????????00000010?????1110011
CSRW  = b8(47) # ?????????????????001000001110011
FENCE = b8(48)
ECALL = b8(49) # 00000000000000000000000001110011
EBREAK= b8(50) # 00000000000100000000000001110011

# ZERO inst
ZERO  = b8(51)

#-------------------------------------------------------------------------
# TinyRV2 Instruction Disassembler
#-------------------------------------------------------------------------

inst_dict = {
  NOP   : "nop",
  LB    : "lb",
  LH    : "lh",
  LW    : "lw",
  LBU   : "lbu",
  LHU   : "lhu",
  SB    : "sb",
  SH    : "sh",
  SW    : "sw",
  SLL   : "sll",
  SLLI  : "slli",
  SRL   : "srl",
  SRLI  : "srli",
  SRA   : "sra",
  SRAI  : "srai",
  ADD   : "add",
  ADDI  : "addi",
  SUB   : "sub",
  LUI   : "lui",
  AUIPC : "auipc",
  XOR   : "xor",
  XORI  : "xori",
  OR    : "or",
  ORI   : "ori",
  AND   : "and",
  ANDI  : "andi",
  SLT   : "slt",
  SLTI  : "slti",
  SLTU  : "sltu",
  SLTIU : "sltiu",
  BEQ   : "beq",
  BNE   : "bne",
  BLT   : "blt",
  BGE   : "bge",
  BLTU  : "bltu",
  BGEU  : "bgeu",
  JAL   : "jal",
  JALR  : "jalr",
  MUL   : "mul",
  MULH  : "mulh",
  MULHSU: "mulhsu",
  MULHU : "mulhu",
  DIV   : "div",
  DIVU  : "divu",
  REM   : "rem",
  REMU  : "remu",
  CSRR  : "csrr",
  CSRW  : "csrw",
  FENCE : "fence",
  ECALL : "ecall",
  EBREAK: "ebreak",
  ZERO  : "????"
}

#-------------------------------------------------------------------------
# CSR registers
#-------------------------------------------------------------------------

# R/W
CSR_PROC2MNGR = b12(0x7C0)
CSR_STATS_EN  = b12(0x7C1)

# R/O)
CSR_MNGR2PROC = b12(0xFC0)
CSR_NUMCORES  = b12(0xFC1)
CSR_COREID    = b12(0xF14)

#-----------------------------------------------------------------------
# DecodeInstType
#-----------------------------------------------------------------------
# TinyRV2 Instruction Type Decoder

class DecodeInstType( Component ):

  # Interface

  def construct( s ):

    s.in_ = InPort ( Bits32 )
    s.out = OutPort( Bits8 )

    @s.update
    def comb_logic():

      s.out = Bits8( ZERO )

      if   s.in_ == b32(0b10011):               s.out = Bits8( NOP )
      elif s.in_[OPCODE] == b7(0b0110011):
        if   s.in_[FUNCT7] == b7(0b0000000):
          if   s.in_[FUNCT3] == b3(0b000):     s.out = Bits8( ADD )
          elif s.in_[FUNCT3] == b3(0b001):     s.out = Bits8( SLL )
          elif s.in_[FUNCT3] == b3(0b010):     s.out = Bits8( SLT )
          elif s.in_[FUNCT3] == b3(0b011):     s.out = Bits8( SLTU )
          elif s.in_[FUNCT3] == b3(0b100):     s.out = Bits8( XOR )
          elif s.in_[FUNCT3] == b3(0b101):     s.out = Bits8( SRL )
          elif s.in_[FUNCT3] == b3(0b110):     s.out = Bits8( OR )
          elif s.in_[FUNCT3] == b3(0b111):     s.out = Bits8( AND )
        elif s.in_[FUNCT7] == b7(0b0100000):
          if   s.in_[FUNCT3] == b3(0b000):     s.out = Bits8( SUB )
          elif s.in_[FUNCT3] == b3(0b101):     s.out = Bits8( SRA )
        elif s.in_[FUNCT7] == b7(0b0000001):
          if   s.in_[FUNCT3] == b3(0b000):     s.out = Bits8( MUL )
          elif s.in_[FUNCT3] == b3(0b001):     s.out = Bits8( MULH )
          elif s.in_[FUNCT3] == b3(0b010):     s.out = Bits8( MULHSU )
          elif s.in_[FUNCT3] == b3(0b011):     s.out = Bits8( MULHU )
          elif s.in_[FUNCT3] == b3(0b100):     s.out = Bits8( DIV )
          elif s.in_[FUNCT3] == b3(0b101):     s.out = Bits8( DIVU )
          elif s.in_[FUNCT3] == b3(0b110):     s.out = Bits8( REM )
          elif s.in_[FUNCT3] == b3(0b111):     s.out = Bits8( REMU )

      elif s.in_[OPCODE] == b7(0b0010011):
        if   s.in_[FUNCT3] == b3(0b000):       s.out = Bits8( ADDI )
        elif s.in_[FUNCT3] == b3(0b010):       s.out = Bits8( SLTI )
        elif s.in_[FUNCT3] == b3(0b011):       s.out = Bits8( SLTIU)
        elif s.in_[FUNCT3] == b3(0b100):       s.out = Bits8( XORI )
        elif s.in_[FUNCT3] == b3(0b110):       s.out = Bits8( ORI  )
        elif s.in_[FUNCT3] == b3(0b111):       s.out = Bits8( ANDI )
        elif s.in_[FUNCT3] == b3(0b001):       s.out = Bits8( SLLI )
        elif s.in_[FUNCT3] == b3(0b101):
          if   s.in_[FUNCT7] == b7(0b0000000): s.out = Bits8( SRLI )
          elif s.in_[FUNCT7] == b7(0b0100000): s.out = Bits8( SRAI )

      elif s.in_[OPCODE] == b7(0b0100011):
        if   s.in_[FUNCT3] == b3(0b000):       s.out = Bits8( SB )
        elif s.in_[FUNCT3] == b3(0b001):       s.out = Bits8( SH )
        elif s.in_[FUNCT3] == b3(0b010):       s.out = Bits8( SW )

      elif s.in_[OPCODE] == b7(0b0000011):
        if   s.in_[FUNCT3] == b3(0b000):       s.out = Bits8( LB )
        elif s.in_[FUNCT3] == b3(0b001):       s.out = Bits8( LH )
        elif s.in_[FUNCT3] == b3(0b010):       s.out = Bits8( LW )
        elif s.in_[FUNCT3] == b3(0b100):       s.out = Bits8( LBU )
        elif s.in_[FUNCT3] == b3(0b101):       s.out = Bits8( LHU )

      elif s.in_[OPCODE] == b7(0b1100011):
        if   s.in_[FUNCT3] == b3(0b000):       s.out = Bits8( BEQ )
        elif s.in_[FUNCT3] == b3(0b001):       s.out = Bits8( BNE )
        elif s.in_[FUNCT3] == b3(0b100):       s.out = Bits8( BLT )
        elif s.in_[FUNCT3] == b3(0b101):       s.out = Bits8( BGE )
        elif s.in_[FUNCT3] == b3(0b110):       s.out = Bits8( BLTU)
        elif s.in_[FUNCT3] == b3(0b111):       s.out = Bits8( BGEU)

      elif s.in_[OPCODE] == b7(0b0110111):     s.out = Bits8( LUI )

      elif s.in_[OPCODE] == b7(0b0010111):     s.out = Bits8( AUIPC )

      elif s.in_[OPCODE] == b7(0b1101111):     s.out = Bits8( JAL )

      elif s.in_[OPCODE] == b7(0b1100111):     s.out = Bits8( JALR )

      elif s.in_[OPCODE] == b7(0b1110011):
        if   s.in_[FUNCT3] == b3(0b001):       s.out = Bits8( CSRW )
        elif s.in_[FUNCT3] == b3(0b010):       s.out = Bits8( CSRR )
        elif (s.in_[FUNCT3] == b3(0)) & (s.in_[RS1] == b5(0)) & (s.in_[RD] == b5(0)):
          if   s.in_[I_IMM] == b12(0):          s.out = Bits8( ECALL )
          elif s.in_[I_IMM] == b12(1):          s.out = Bits8( EBREAK )
