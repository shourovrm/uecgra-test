from pymtl import *

from pclib.rtl import RegEn, Reg, Mux, RShifter, LShifter, Adder, ZeroComp
from pclib.valrdy import valrdy_to_str
from pclib.rtl import TestSourceValRdy, TestSinkValRdy
from pclib.ifcs   import InValRdyIfc, OutValRdyIfc

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

class CalcShamt( RTLComponent ):

  def construct( s ):
    s.in_ = InVPort( Bits8 )
    s.out = OutVPort( Bits4 )

    @s.update
    def up_calc_shamt():
      if   not s.in_: s.out = Bits4( 8 )
      elif s.in_[0] : s.out = Bits4( 1 )
      elif s.in_[1] : s.out = Bits4( 1 )
      elif s.in_[2] : s.out = Bits4( 2 )
      elif s.in_[3] : s.out = Bits4( 3 )
      elif s.in_[4] : s.out = Bits4( 4 )
      elif s.in_[5] : s.out = Bits4( 5 )
      elif s.in_[6] : s.out = Bits4( 6 )
      elif s.in_[7] : s.out = Bits4( 7 )

class IntMulCS( Interface ):

  def construct( s ):
    s.a_mux_sel   = InVPort( Bits1 )
    s.b_mux_sel   = InVPort( Bits1 )
    s.res_mux_sel = InVPort( Bits1 )
    s.res_reg_en  = InVPort( Bits1 )
    s.add_mux_sel = InVPort( Bits1 )
    s.b_lsb       = OutVPort( Bits1 )
    s.is_b_zero   = OutVPort( Bits1 )

class IntMulVarLatDpath( RTLComponent ):

  def construct( s, nbits ):
    dtype = mk_bits( nbits )

    s.req_msg  = InVPort( mk_bits(nbits*2) )
    s.resp_msg = OutVPort( dtype )
    s.cs       = IntMulCS()

    # Variables and upblks associated with B

    s.b_mux = Mux( dtype, 2 )(
      in_ = { B_MUX_SEL_LD: s.req_msg[nbits:nbits*2] },
      sel = s.cs.b_mux_sel,
    )

    s.b_reg = Reg( dtype )( in_ = s.b_mux.out )
    s.connect( s.cs.b_lsb, s.b_reg.out[0] )

    s.calc_sh = CalcShamt()( in_ = s.b_reg.out[0:8] )

    s.b_zcp = ZeroComp( dtype )( in_ = s.b_reg.out, out = s.cs.is_b_zero )

    s.b_rsh = RShifter( dtype, 4 )(
      in_   = s.b_reg.out,
      shamt = s.calc_sh.out,
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
      shamt = s.calc_sh.out,
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

class IntMulVarLatCtrl( RTLComponent ):

  def construct( s ):
    # s.sb = bytearray(2**30)

    s.req_val  = InVPort( Bits1 )
    s.req_rdy  = OutVPort( Bits1 )
    s.resp_val = OutVPort( Bits1 )
    s.resp_rdy = InVPort( Bits1 )
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

class IntMulVarLat( RTLComponent ):

  def construct( s, nbits=32 ):
    assert nbits >= 8

    s.req  = InValRdyIfc( mk_bits(nbits*2) )
    s.resp = OutValRdyIfc( mk_bits(nbits) )

    s.dpath = IntMulVarLatDpath( nbits )(
      req_msg  = s.req.msg,
      resp_msg = s.resp.msg,
    )
    s.ctrl  = IntMulVarLatCtrl()(
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

import random

class TestHarness( RTLComponent ):

  def construct( s, model, src_msgs, sink_msgs ):

    s.src  = TestSourceValRdy( Bits128, src_msgs )
    s.sink = TestSinkValRdy( Bits64, sink_msgs )

    s.imul = model( req = s.src.out, resp = s.sink.in_ )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.imul.line_trace()+" >>> "+s.sink.line_trace()

random.seed(0xdeadbeef)
src_msgs  = []
sink_msgs = []

for i in xrange(20):
  x = random.randint(0, 2**62)
  y = random.randint(0, 2**62)
  z = Bits128(0)
  z[0:64]  = x
  z[64:128] = y
  src_msgs.append( z )
  sink_msgs.append( Bits64( x * y ) )

def run_test( model ):
  th = TestHarness( model, src_msgs, sink_msgs )
  th.elaborate()

  import time
  t0 = time.clock()
  th.imul.delete_component_by_name( "dpath" )
  t1 = time.clock()
  print "delete_component: {:.03f}".format(t1-t0)
      
  th.imul.add_component_by_name( "dpath", IntMulVarLatDpath(64) ) # pass in a class?
  t2 = time.clock()
  print "add_component: {:.03f}".format(t2-t1)

  th.add_connection( th.imul.dpath.cs, th.imul.ctrl.cs )
  t3 = time.clock()
  print "add_connection: {:.03f}".format(t3-t2)
  th.add_connection( th.imul.dpath.resp_msg, th.imul.resp.msg )
  t4 = time.clock()
  print "add_connection: {:.03f}".format(t4-t3)

  # assert False
  
  # for net in th._all_nets:
    # print net[0], net[1:]
    # print 

  th.add_connection( th.imul.dpath.req_msg, th.imul.req.msg )

  # th.add_connection( "top.imul.dpath.cs", "top.imul.ctrl.cs" )

  th.check()

  SimRTLPass()( th )
  T, maxT = 0, 5000

  print
  while not th.done():
    th.tick()
    # print th.line_trace()
    T += 1
    assert T < maxT

def test_varlat():
  a = IntMulVarLat(64)
  th = run_test( a )
  # print th

  # for i in xrange(1000000000):
    # i=i

# def test_varlat2():
  # a = IntMulVarLat(64)
  # th = run_test( a )
  # print th

  # for i in xrange(1000000000):
    # i=i

# def test_varlat3():
  # a = IntMulVarLat(64)
  # th = run_test( a )
  # print th

  # for i in xrange(1000000000):
    # i=i
