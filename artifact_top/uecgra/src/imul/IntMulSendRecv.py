from pymtl3 import *
from pymtl3.stdlib.rtl import RegEn, Reg, Mux, RShifter, LShifter, Adder, ZeroComp
from pymtl3.stdlib.ifcs   import SendIfcRTL, RecvIfcRTL

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
      if   s.in_ == b8(0): s.out = b4( 8 )
      elif s.in_[0] : s.out = b4( 1 )
      elif s.in_[1] : s.out = b4( 1 )
      elif s.in_[2] : s.out = b4( 2 )
      elif s.in_[3] : s.out = b4( 3 )
      elif s.in_[4] : s.out = b4( 4 )
      elif s.in_[5] : s.out = b4( 5 )
      elif s.in_[6] : s.out = b4( 6 )
      elif s.in_[7] : s.out = b4( 7 )

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
    s.connect( s.cs.b_lsb, s.b_reg.out[0] )

    if mode == 'varlat':
      s.calc_sh = CalcShamt()( in_ = s.b_reg.out[0:8] )
      shift_amount = s.calc_sh.out
    else:
      shift_amount = 1

    s.b_zcp = ZeroComp( dtype )( in_ = s.b_reg.out, out = s.cs.is_b_zero )


    s.b_rsh = RShifter( dtype, 4 )(
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

    s.a_lsh = LShifter( dtype, 4 )(
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

    s.req_en   = InPort( Bits1 )
    s.req_rdy  = OutPort( Bits1 )
    s.resp_en  = OutPort( Bits1 )
    s.resp_rdy = InPort( Bits1 )
    s.cs       = IntMulCS().inverse()

    s.state = Reg( Bits2 )

    s.STATE_IDLE = b2(0)
    s.STATE_CALC = b2(1)
    s.STATE_DONE = b2(2)

    @s.update
    def state_transitions():
      curr_state  = s.state.out

      s.state.in_ = curr_state

      if   curr_state == s.STATE_IDLE:
        if s.req_en:
          s.state.in_ = s.STATE_CALC

      elif curr_state == s.STATE_CALC:
        if s.cs.is_b_zero:
          s.state.in_ = s.STATE_DONE

      elif curr_state == s.STATE_DONE:
        if s.resp_en:
          s.state.in_ = s.STATE_IDLE

    @s.update
    def state_outputs():

      curr_state = s.state.out

      s.req_rdy        = b1( 0 )
      s.resp_en        = b1( 0 )
      s.cs.a_mux_sel   = b1( 0 )
      s.cs.b_mux_sel   = b1( 0 )
      s.cs.add_mux_sel = b1( 0 )
      s.cs.res_mux_sel = b1( 0 )
      s.cs.res_reg_en  = b1( 0 )

      # In IDLE state we simply wait for inputs to arrive and latch them

      if curr_state == s.STATE_IDLE:
        s.req_rdy        = b1( 1 )

        s.cs.a_mux_sel   = b1( A_MUX_SEL_LD )
        s.cs.b_mux_sel   = b1( B_MUX_SEL_LD )
        s.cs.res_mux_sel = b1( RESULT_MUX_SEL_0 )
        s.cs.add_mux_sel = b1( ADD_MUX_SEL_X )
        s.cs.res_reg_en  = b1( 1 )

      elif curr_state == s.STATE_CALC:

        s.cs.a_mux_sel   = b1( A_MUX_SEL_LSH )
        s.cs.b_mux_sel   = b1( B_MUX_SEL_RSH )
        s.cs.res_mux_sel = b1( RESULT_MUX_SEL_ADD )
        s.cs.res_reg_en  = b1( 1 )
        s.cs.add_mux_sel = b1( ADD_MUX_SEL_ADD ) if s.cs.b_lsb else b1( ADD_MUX_SEL_RESULT )

      # In DONE state we simply wait for output transaction to occur

      elif curr_state == s.STATE_DONE:
        s.resp_en        = s.resp_rdy

        s.cs.a_mux_sel   = b1( A_MUX_SEL_X )
        s.cs.b_mux_sel   = b1( B_MUX_SEL_X )
        s.cs.res_mux_sel = b1( RESULT_MUX_SEL_X )
        s.cs.add_mux_sel = b1( ADD_MUX_SEL_X )
        s.cs.res_reg_en  = b1( 0 )

class IntMul( Component ):

  def construct( s, nbits=32, mode='varlat' ):
    assert nbits >= 8

    s.req  = RecvIfcRTL( mk_bits(nbits*2) )
    s.resp = SendIfcRTL( mk_bits(nbits) )

    s.dpath = IntMulDpath( nbits, mode )(
      req_msg  = s.req.msg,
      resp_msg = s.resp.msg,
    )
    s.ctrl  = IntMulCtrl()(
      cs = s.dpath.cs,
      req_en   = s.req.en,
      req_rdy  = s.req.rdy,
      resp_en  = s.resp.en,
      resp_rdy = s.resp.rdy,
    )

  def line_trace( s ):
    return "{} >>> {}{} >>> {}".format( s.req.line_trace(),
            s.dpath.a_reg.line_trace(), s.dpath.res_reg.line_trace(),
            s.resp.line_trace() )
