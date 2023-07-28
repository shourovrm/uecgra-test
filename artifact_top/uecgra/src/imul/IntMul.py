from pymtl3 import *
from pymtl3.stdlib.rtl import RegEn, Reg, Mux, RightLogicalShifter, LeftLogicalShifter, Adder, ZeroComparator
from pymtl3.stdlib.ifcs   import InValRdyIfc, OutValRdyIfc

A_MUX_SEL_LSH        = 0
A_MUX_SEL_LD         = 1
A_MUX_SEL_X          = 0

B_MUX_SEL_RSH        = 0
B_MUX_SEL_LD         = 1
B_MUX_SEL_X          = 0

RESULT_MUX_SEL_ADD   = 0
RESULT_MUX_SEL_0     = 1
RESULT_MUX_SEL_X     = 0

ADD_MUX_SEL_ADD      = 0
ADD_MUX_SEL_RESULT   = 1
ADD_MUX_SEL_X        = 0

class CalcShamt( Component ):

  def construct( s ):
    s.in_ = InPort( Bits8 )
    s.out = OutPort( Bits4 )

    @s.update
    def up_calc_shamt():
      if   s.in_ == Bits8(0): s.out = Bits4( 8 )
      elif s.in_[0] : s.out = Bits4( 1 )
      elif s.in_[1] : s.out = Bits4( 1 )
      elif s.in_[2] : s.out = Bits4( 2 )
      elif s.in_[3] : s.out = Bits4( 3 )
      elif s.in_[4] : s.out = Bits4( 4 )
      elif s.in_[5] : s.out = Bits4( 5 )
      elif s.in_[6] : s.out = Bits4( 6 )
      elif s.in_[7] : s.out = Bits4( 7 )
      else:           s.out = Bits4( 8 )

class IntMulCS( Interface ):

  def construct( s ):
    s.a_mux_sel   = InPort( Bits1 )
    s.b_mux_sel   = InPort( Bits1 )
    s.res_mux_sel = InPort( Bits1 )
    s.res_reg_en  = InPort( Bits1 )
    s.add_mux_sel = InPort( Bits1 )
    s.b_lsb       = OutPort( Bits1 )
    s.is_b_zero   = OutPort( Bits1 )

class IntMulDpath( Component ):

  def construct( s, nbits, mode ):
    dtype = mk_bits( nbits )

    s.req_msg  = InPort( mk_bits(nbits*2) )
    s.resp_msg = OutPort( dtype )
    s.cs       = IntMulCS()

    # Variables and upblks associated with B

    s.b_mux = Mux( dtype, 2 )(
      in_ = { B_MUX_SEL_LD: s.req_msg[nbits:nbits*2] },
      sel = s.cs.b_mux_sel,
    )

    s.b_reg = Reg( dtype )( in_ = s.b_mux.out )
    connect( s.cs.b_lsb, s.b_reg.out[0] )

    if mode == 'varlat':
      s.calc_sh = CalcShamt()( in_ = s.b_reg.out[0:8] )
      shift_amount = s.calc_sh.out
    else:
      shift_amount = 1

    s.b_zcp = ZeroComparator( dtype )( in_ = s.b_reg.out, out = s.cs.is_b_zero )


    s.b_rsh = RightLogicalShifter( dtype, 4 )(
      in_   = s.b_reg.out,
      shamt = shift_amount,
      out   = s.b_mux.in_[ B_MUX_SEL_RSH ],
    )

    # Variables and upblks associated with A

    s.a_mux = Mux( dtype, 2 )(
      in_ = { A_MUX_SEL_LD: s.req_msg[0:nbits] },
      sel = s.cs.a_mux_sel,
    )

    s.a_reg = Reg( dtype )( in_ = s.a_mux.out )

    s.a_lsh = LeftLogicalShifter( dtype, 4 )(
      in_   = s.a_reg.out,
      shamt = shift_amount,
      out   = s.a_mux.in_[A_MUX_SEL_LSH],
    )

    # Variables and upblks associated with Result

    s.res_mux = Mux( dtype, 2 )(
      sel = s.cs.res_mux_sel,
      in_ = { RESULT_MUX_SEL_0: 0 },
    )

    s.res_reg = RegEn( dtype )(
      in_ = s.res_mux.out,
      out = s.resp_msg,
      en  = s.cs.res_reg_en,
    )

    s.res_add = Adder( dtype )( in0 = s.a_reg.out, in1 = s.res_reg.out )

    s.add_mux = Mux( dtype, 2 )(
      in_ = { ADD_MUX_SEL_ADD: s.res_add.out,
              ADD_MUX_SEL_RESULT: s.res_reg.out },
      sel = s.cs.add_mux_sel,
      out = s.res_mux.in_[RESULT_MUX_SEL_ADD],
    )

class IntMulCtrl( Component ):

  def construct( s ):
    # s.sb = bytearray(2**30)

    s.req_val  = InPort( Bits1 )
    s.req_rdy  = OutPort( Bits1 )
    s.resp_val = OutPort( Bits1 )
    s.resp_rdy = InPort( Bits1 )
    s.cs       = IntMulCS().inverse()

    s.state = Reg( Bits2 )

    s.STATE_IDLE = Bits2(0)
    s.STATE_CALC = Bits2(1)
    s.STATE_DONE = Bits2(2)

    @s.update
    def state_transitions():
      curr_state  = s.state.out

      s.state.in_ = curr_state

      if   curr_state == s.STATE_IDLE:
        if s.req_val and s.req_rdy:
          s.state.in_ = s.STATE_CALC

      elif curr_state == s.STATE_CALC:
        if s.cs.is_b_zero:
          s.state.in_ = s.STATE_DONE

      elif curr_state == s.STATE_DONE:
        if s.resp_val and s.resp_rdy:
          s.state.in_ = s.STATE_IDLE

    @s.update
    def state_outputs():

      curr_state = s.state.out

      s.req_rdy        = Bits1( 0 )
      s.resp_val       = Bits1( 0 )
      s.cs.a_mux_sel   = Bits1( 0 )
      s.cs.b_mux_sel   = Bits1( 0 )
      s.cs.add_mux_sel = Bits1( 0 )
      s.cs.res_mux_sel = Bits1( 0 )
      s.cs.res_reg_en  = Bits1( 0 )

      # In IDLE state we simply wait for inputs to arrive and latch them

      if curr_state == s.STATE_IDLE:
        s.req_rdy        = Bits1( 1 )
        s.resp_val       = Bits1( 0 )

        s.cs.a_mux_sel   = Bits1( A_MUX_SEL_LD )
        s.cs.b_mux_sel   = Bits1( B_MUX_SEL_LD )
        s.cs.res_mux_sel = Bits1( RESULT_MUX_SEL_0 )
        s.cs.res_reg_en  = Bits1( 1 )
        s.cs.add_mux_sel = Bits1( ADD_MUX_SEL_X )

      elif curr_state == s.STATE_CALC:
        s.req_rdy        = Bits1( 0 )
        s.resp_val       = Bits1( 0 )

        s.cs.a_mux_sel   = Bits1( A_MUX_SEL_LSH )
        s.cs.b_mux_sel   = Bits1( B_MUX_SEL_RSH )
        s.cs.res_mux_sel = Bits1( RESULT_MUX_SEL_ADD )
        s.cs.res_reg_en  = Bits1( 1 )
        s.cs.add_mux_sel = Bits1( ADD_MUX_SEL_ADD ) if s.cs.b_lsb else Bits1( ADD_MUX_SEL_RESULT )

      # In DONE state we simply wait for output transaction to occur

      elif curr_state == s.STATE_DONE:
        s.req_rdy        = Bits1( 0 )
        s.resp_val       = Bits1( 1 )

        s.cs.a_mux_sel   = Bits1( A_MUX_SEL_X )
        s.cs.b_mux_sel   = Bits1( A_MUX_SEL_X )
        s.cs.res_mux_sel = Bits1( A_MUX_SEL_X )
        s.cs.add_mux_sel = Bits1( A_MUX_SEL_X )
        s.cs.res_reg_en  = Bits1( 0 )

class IntMul( Component ):

  def construct( s, nbits=32, mode='varlat' ):
    assert nbits >= 8

    nbitsx2 = 2*nbits

    s.req  = InValRdyIfc( mk_bits(nbits*2) )
    s.resp = OutValRdyIfc( mk_bits(nbits) )

    if mode == 'single_cycle':
      s.state = Wire( Bits1 )

      # Register input because the processor expects the
      # path between resp.msg and req.msg to be cut.

      s.op_a = Wire( mk_bits(nbits) )
      s.op_b = Wire( mk_bits(nbits) )

      @s.update_ff
      def comb_imul_reg_input():
        s.op_a <<= s.req.msg[0:nbits]
        s.op_b <<= s.req.msg[nbits:nbitsx2]

      @s.update_ff
      def comb_imul_state():
        # 0: IDLE
        # 1: WORK
        if s.reset:
          s.state <<= b1(0)
        else:
          if   s.req.val  & s.req.rdy  & (s.state == b1(0)):
            s.state <<= b1(1)
          elif s.resp.val & s.resp.rdy & (s.state == b1(1)):
            s.state <<= b1(0)

      s.req.rdy  //= lambda: ~s.state
      s.resp.val //= lambda:  s.state
      s.resp.msg //= lambda:  s.op_a * s.op_b

    else:
      s.dpath = IntMulDpath( nbits, mode )(
        req_msg  = s.req.msg,
        resp_msg = s.resp.msg,
      )
      s.ctrl  = IntMulCtrl()(
        cs = s.dpath.cs,
        req_val  = s.req.val,
        req_rdy  = s.req.rdy,
        resp_val = s.resp.val,
        resp_rdy = s.resp.rdy,
      )

  def line_trace( s ):
    return "{} >>> {}{} >>> {}".format( s.req.line_trace(),
            s.dpath.a_reg.line_trace(), s.dpath.res_reg.line_trace(),
            s.resp.line_trace() )
