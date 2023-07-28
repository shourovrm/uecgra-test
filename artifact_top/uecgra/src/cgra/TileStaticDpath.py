"""
==========================================================================
TileStaticDpath.py
==========================================================================
Datapath for dynamic elastic CGRA tile.

Author : Yanghui Ou
  Date : August 1, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.rtl import Mux
from pymtl3.stdlib.rtl.queues import NormalQueueRTL
from pymtl3.stdlib.rtl.registers import RegEn

from .enums import InputMux, OutputMux, RegMux, TileDirection as TD
from .AluMsg import mk_alu_msg
from .Node import Node
from .SwitchBox import SwitchBox
from .NodeReg import NodeReg

class TileStaticDpath( Component ):

  def construct( s, Type, mul_ncycles=3, DataGating = True ):

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Interface

    s.deq_msg_n = InPort ( Type )
    s.deq_msg_s = InPort ( Type )
    s.deq_msg_w = InPort ( Type )
    s.deq_msg_e = InPort ( Type )

    s.send_msg_n = OutPort( Type )
    s.send_msg_s = OutPort( Type )
    s.send_msg_w = OutPort( Type )
    s.send_msg_e = OutPort( Type )

    # Temporary imm port to configure constant
    s.imm = InPort( Type )

    s.acc_reg_en = InPort( Bits1 )

    s.node_cfg = InPort( Bits5 )
    s.node_cfg_func = InPort( Bits5 )

    s.branch_cond = OutPort( Type )

    s.node_recv_en  = InPort ( Bits1 )
    s.node_recv_rdy = OutPort( Bits1 )
    s.node_send_en  = OutPort( Bits1 )
    s.node_send_rdy = InPort ( Bits1 )

    s.opd_a_mux_sel  = InPort( Bits3 )
    s.opd_b_mux_sel  = InPort( Bits3 )
    s.bypass_mux_sel = InPort( Bits3 )
    s.altbps_mux_sel = InPort( Bits3 ) # Alternative bypass

    s.acc_mux_sel    = InPort( Bits2 )
    s.send_mux_n_sel = InPort( Bits2 )
    s.send_mux_s_sel = InPort( Bits2 )
    s.send_mux_w_sel = InPort( Bits2 )
    s.send_mux_e_sel = InPort( Bits2 )

    # Componnet

    s.opd_a_wire  = Wire( Type )
    s.opd_b_wire  = Wire( Type )
    s.bypass_wire = Wire( Type )
    s.altbps_wire = Wire( Type )
    s.acc_reg     = RegEn( Type )(
      clk = s.clk,
      en = s.acc_reg_en,
    )

    s.opd_a_mux = Mux( Type, ninputs=5 )(
      sel = s.opd_a_mux_sel,
      in_ = {
        InputMux.NORTH : s.deq_msg_n,
        InputMux.SOUTH : s.deq_msg_s,
        InputMux.WEST  : s.deq_msg_w,
        InputMux.EAST  : s.deq_msg_e,
        InputMux.SELF  : s.acc_reg.out,
      },
      out = s.opd_a_wire,
    )

    s.opd_b_mux = Mux( Type, ninputs=5 )(
      sel = s.opd_b_mux_sel,
      in_ = {
        InputMux.NORTH : s.deq_msg_n,
        InputMux.SOUTH : s.deq_msg_s,
        InputMux.WEST  : s.deq_msg_w,
        InputMux.EAST  : s.deq_msg_e,
        InputMux.SELF  : s.acc_reg.out,
      },
      out = [ s.opd_b_wire, s.branch_cond ],
    )

    s.bypass_mux = Mux( Type, ninputs=5 )(
      sel = s.bypass_mux_sel,
      in_ = {
        InputMux.NORTH : s.deq_msg_n,
        InputMux.SOUTH : s.deq_msg_s,
        InputMux.WEST  : s.deq_msg_w,
        InputMux.EAST  : s.deq_msg_e,
        InputMux.SELF  : s.acc_reg.out,
      },
      out = s.bypass_wire,
    )

    s.altbps_mux = Mux( Type, ninputs=5 )(
      sel = s.altbps_mux_sel,
      in_ = {
        InputMux.NORTH : s.deq_msg_n,
        InputMux.SOUTH : s.deq_msg_s,
        InputMux.WEST  : s.deq_msg_w,
        InputMux.EAST  : s.deq_msg_e,
        InputMux.SELF  : s.acc_reg.out,
      },
      out = s.altbps_wire,
    )

    s.node = Node( Type, mul_ncycles, DataGating )

    s.node.clk //= s.clk
    s.node.reset //= s.reset

    connect( s.node.cfg,             s.node_cfg      )
    connect( s.node.cfg_func,        s.node_cfg_func )
    connect( s.node.recv.msg.opd_a, s.opd_a_wire    )
    connect( s.node.recv.msg.opd_b, s.opd_b_wire    )
    connect( s.node.recv.en,         s.node_recv_en  )
    connect( s.node.recv.rdy,        s.node_recv_rdy )
    connect( s.node.send.en,         s.node_send_en  )
    connect( s.node.send.rdy,        s.node_send_rdy )

    # s.acc_mux selects inputs to the accumulate register
    s.acc_mux = Mux( Type, ninputs=4 )(
      sel = s.acc_mux_sel,
      in_ = {
        RegMux.COMPUTE : s.node.send.msg,
        RegMux.BYPASS  : s.bypass_wire,
        RegMux.BPS_ALT : s.altbps_wire,
        RegMux.CONST   : s.imm,
      },
      out = s.acc_reg.in_,
    )

    s.send_mux_n = Mux( Type, ninputs=3 )(
      sel = s.send_mux_n_sel,
      in_ = {
        OutputMux.COMPUTE : s.node.send.msg,
        OutputMux.BYPASS  : s.bypass_wire,
        OutputMux.BPS_ALT : s.altbps_wire,
      },
      out = s.send_msg_n,
    )

    s.send_mux_s = Mux( Type, ninputs=3 )(
      sel = s.send_mux_s_sel,
      in_ = {
        OutputMux.COMPUTE : s.node.send.msg,
        OutputMux.BYPASS  : s.bypass_wire,
        OutputMux.BPS_ALT : s.altbps_wire,
      },
      out = s.send_msg_s,
    )

    s.send_mux_w = Mux( Type, ninputs=3 )(
      sel = s.send_mux_w_sel,
      in_ = {
        OutputMux.COMPUTE : s.node.send.msg,
        OutputMux.BYPASS  : s.bypass_wire,
        OutputMux.BPS_ALT : s.altbps_wire,
      },
      out = s.send_msg_w,
    )

    s.send_mux_e = Mux( Type, ninputs=3 )(
      sel = s.send_mux_e_sel,
      in_ = {
        OutputMux.COMPUTE : s.node.send.msg,
        OutputMux.BYPASS  : s.bypass_wire,
        OutputMux.BPS_ALT : s.altbps_wire,
      },
      out = s.send_msg_e,
    )
