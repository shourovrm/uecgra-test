#=========================================================================
# ProcDpathComponentsPRTL.py
#=========================================================================

from pymtl3            import *
from proc.TinyRV2InstPRTL  import *

#-------------------------------------------------------------------------
# Generate intermediate (imm) based on type
#-------------------------------------------------------------------------

class ImmGenPRTL( Component ):

  # Interface

  def construct( s ):
    dtype = mk_bits( 32 )

    s.imm_type = InPort( Bits3 )
    s.inst     = InPort( dtype )
    s.imm      = OutPort( dtype )

    @s.update
    def up_immgen():
      s.imm = dtype(0)

      # Always sext!

      if   s.imm_type == Bits3(0): # I-type

        s.imm = concat( sext( s.inst[ I_IMM ], 32 ) )

      elif s.imm_type == Bits3(2): # B-type

        s.imm = concat( sext( s.inst[ B_IMM3 ], 20 ),
                                    s.inst[ B_IMM2 ],
                                    s.inst[ B_IMM1 ],
                                    s.inst[ B_IMM0 ],
                                    Bits1( 0 ) )

      elif s.imm_type == Bits3(1): # S-type

        s.imm = concat( sext( s.inst[ S_IMM1 ], 27 ),
                                    s.inst[ S_IMM0 ] )

      elif s.imm_type == Bits3(3): # U-type

        s.imm = concat(       s.inst[ U_IMM ],
                                    Bits12( 0 ) )

      elif s.imm_type == Bits3(4): # J-type

        s.imm = concat( sext( s.inst[ J_IMM3 ], 12 ),
                                    s.inst[ J_IMM2 ],
                                    s.inst[ J_IMM1 ],
                                    s.inst[ J_IMM0 ],
                                    Bits1( 0 ) )

#-------------------------------------------------------------------------
# ALU
#-------------------------------------------------------------------------

class AluPRTL( Component ):

  # Interface

  def construct( s ):
    dtype = mk_bits( 32 )

    s.in0      = InPort ( dtype )
    s.in1      = InPort ( dtype )
    s.fn       = InPort ( Bits4 )

    s.out      = OutPort( dtype )
    s.ops_eq   = OutPort( Bits1 )
    s.ops_lt   = OutPort( Bits1 )
    s.ops_ltu  = OutPort( Bits1 )

  # Combinational Logic

    s.tmp_a = Wire( Bits33 )
    s.tmp_b = Wire( Bits64 )
    s.tmp_c = Wire( Bits32 )

    @s.update
    def comb_logic():

      s.tmp_a = Bits33( 0 )
      s.tmp_b = Bits64( 0 )

      if   s.fn == Bits4(0) : s.out = s.in0 + s.in1       # ADD
      elif s.fn == Bits4(11): s.out = s.in0               # CP OP0
      elif s.fn == Bits4(12): s.out = s.in1               # CP OP1

      elif s.fn == Bits4(1): s.out = s.in0 - s.in1       # SUB
      elif s.fn == Bits4(2): s.out = s.in0 << s.in1[0:5] # SLL
      elif s.fn == Bits4(3): s.out = s.in0 | s.in1       # OR

      elif s.fn == Bits4(4):                                   # SLT
        s.tmp_a = sext( s.in0, 33 ) - sext( s.in1, 33 )
        s.out   = zext( s.tmp_a[32], 32 )

      elif s.fn == Bits4(5): s.out = zext( s.in0 < s.in1, 32 )       # SLTU
      elif s.fn == Bits4(6): s.out = s.in0 & s.in1       # AND
      elif s.fn == Bits4(7): s.out = s.in0 ^ s.in1       # XOR
      elif s.fn == Bits4(8): s.out = ~( s.in0 | s.in1 )  # NOR
      elif s.fn == Bits4(9): s.out = s.in0 >> s.in1[0:5] # SRL

      elif s.fn == Bits4(10):                                   # SRA
        s.tmp_b = sext( s.in0, 64 ) >> s.in1[0:5]
        s.out   = s.tmp_b[0:32]

      elif s.fn == Bits4(13):                                   # ADDZ for clearing LSB
        s.tmp_c = s.in0 + s.in1
        s.out   = concat( s.tmp_c[1:32], Bits1(0) )
      else:
        s.out = dtype(0)                   # Unknown

      s.ops_eq  = ( s.in0 == s.in1 )
      s.ops_lt  = s.tmp_a[32]
      s.ops_ltu = ( s.in0 < s.in1 )
