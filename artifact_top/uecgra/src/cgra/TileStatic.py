"""
==========================================================================
TileStatic.py
==========================================================================
Synchronous dynamic elastic or inelastic CGRA tile.

Note:
  1D convolution:

for ( int i = 0; i < N; i++ ){
  int sum = 0;
  for ( int j = 0; j < F_SIZE; j++ ){
    sum += seq[i+j] * fil[j];
  }
  result[i] = sum;
}

Author : Yanghui Ou
  Date : August 1, 2019

"""
from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

from fifos.NormalQueuePow2RTL import NormalQueuePow2RTL
from fifos.ZeroBackPressureBuffer import ZeroBackPressureBuffer
from .enums import CfgMsg as CFG, TileDirection as TD
from .TileStaticDpath import TileStaticDpath
from .TileStaticCtrl import TileStaticCtrl

class TileStatic( Component ):

  def construct( s, Type, CfgMsgType, mul_ncycles=0, elasticity="elastic", fifo_depth=2 ):

    # Check elasticity setting
    assert elasticity in ['elastic', 'inelastic']

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Interface

    s.recv = [ RecvIfcRTL( Type ) for _ in range(4) ]
    s.send = [ SendIfcRTL( Type ) for _ in range(4) ]

    s.cfg    = InPort( CfgMsgType )
    s.cfg_en = InPort( Bits1      )

    # Temporary port to configure the constant
    s.imm = InPort( Type )

    # Components

    s.ctrl  = TileStaticCtrl( Type, CfgMsgType, elasticity )
    s.dpath = TileStaticDpath( Type, mul_ncycles )

    if elasticity == "elastic":
      s.in_q_n = NormalQueuePow2RTL( Type, num_entries=fifo_depth )( enq = s.recv[ TD.NORTH ] )
      s.in_q_s = NormalQueuePow2RTL( Type, num_entries=fifo_depth )( enq = s.recv[ TD.SOUTH ] )
      s.in_q_w = NormalQueuePow2RTL( Type, num_entries=fifo_depth )( enq = s.recv[ TD.WEST  ] )
      s.in_q_e = NormalQueuePow2RTL( Type, num_entries=fifo_depth )( enq = s.recv[ TD.EAST  ] )

    elif elasticity == "inelastic":
      s.in_q_n = ZeroBackPressureBuffer( Type )( enq = s.recv[ TD.NORTH ] )
      s.in_q_s = ZeroBackPressureBuffer( Type )( enq = s.recv[ TD.SOUTH ] )
      s.in_q_w = ZeroBackPressureBuffer( Type )( enq = s.recv[ TD.WEST  ] )
      s.in_q_e = ZeroBackPressureBuffer( Type )( enq = s.recv[ TD.EAST  ] )

    # Connect ctrl and datapath

    connect_pairs(
      s.dpath.branch_cond,    s.ctrl.branch_cond,
      s.dpath.acc_reg_en,     s.ctrl.acc_reg_en,
      s.dpath.node_cfg,       s.ctrl.node_cfg,
      s.dpath.node_cfg_func,  s.ctrl.node_cfg_func,
      s.dpath.node_recv_en,   s.ctrl.node_recv_en,
      s.dpath.node_recv_rdy,  s.ctrl.node_recv_rdy,
      s.dpath.node_send_en,   s.ctrl.node_send_en,
      s.dpath.node_send_rdy,  s.ctrl.node_send_rdy,
      s.dpath.opd_a_mux_sel,  s.ctrl.opd_a_mux_sel,
      s.dpath.opd_b_mux_sel,  s.ctrl.opd_b_mux_sel,
      s.dpath.bypass_mux_sel, s.ctrl.bypass_mux_sel,
      s.dpath.altbps_mux_sel, s.ctrl.altbps_mux_sel,
      s.dpath.acc_mux_sel,    s.ctrl.acc_mux_sel,
      s.dpath.send_mux_n_sel, s.ctrl.send_mux_n_sel,
      s.dpath.send_mux_s_sel, s.ctrl.send_mux_s_sel,
      s.dpath.send_mux_w_sel, s.ctrl.send_mux_w_sel,
      s.dpath.send_mux_e_sel, s.ctrl.send_mux_e_sel,
    )

    # Connect input queues to control and datapath

    connect_pairs(
      s.in_q_n.deq.en,  s.ctrl.deq_en_n,
      s.in_q_n.deq.rdy, s.ctrl.deq_rdy_n,
      s.in_q_n.deq.msg, s.dpath.deq_msg_n,

      s.in_q_s.deq.en,  s.ctrl.deq_en_s,
      s.in_q_s.deq.rdy, s.ctrl.deq_rdy_s,
      s.in_q_s.deq.msg, s.dpath.deq_msg_s,

      s.in_q_w.deq.en,  s.ctrl.deq_en_w,
      s.in_q_w.deq.rdy, s.ctrl.deq_rdy_w,
      s.in_q_w.deq.msg, s.dpath.deq_msg_w,

      s.in_q_e.deq.en,  s.ctrl.deq_en_e,
      s.in_q_e.deq.rdy, s.ctrl.deq_rdy_e,
      s.in_q_e.deq.msg, s.dpath.deq_msg_e,
    )

    # Connect interface to control and datapath

    connect_pairs(
      s.cfg,            s.ctrl.cfg,
      s.cfg_en,         s.ctrl.cfg_en,

      s.imm,            s.dpath.imm,

      s.send[TD.NORTH].en, s.ctrl.send_en_n,
      s.send[TD.NORTH].rdy, s.ctrl.send_rdy_n,
      s.send[TD.NORTH].msg, s.dpath.send_msg_n,

      s.send[TD.SOUTH].en, s.ctrl.send_en_s,
      s.send[TD.SOUTH].rdy, s.ctrl.send_rdy_s,
      s.send[TD.SOUTH].msg, s.dpath.send_msg_s,

      s.send[TD.WEST ].en, s.ctrl.send_en_w,
      s.send[TD.WEST ].rdy, s.ctrl.send_rdy_w,
      s.send[TD.WEST ].msg, s.dpath.send_msg_w,

      s.send[TD.EAST ].en, s.ctrl.send_en_e,
      s.send[TD.EAST ].rdy, s.ctrl.send_rdy_e,
      s.send[TD.EAST ].msg, s.dpath.send_msg_e,
    )

  def line_trace( s ):
    recv_str = '|'.join([ str(s.recv[i]) for i in range(4) ])
    send_str = '|'.join([ str(s.send[i]) for i in range(4) ])
    op_str   = (
      'cp0' if s.cfg.func == CFG.CP0 else
      'cp1' if s.cfg.func == CFG.CP1 else
      'add' if s.cfg.func == CFG.ADD else
      'sll' if s.cfg.func == CFG.SLL else
      'srl' if s.cfg.func == CFG.SRL else
      'and' if s.cfg.func == CFG.AND else
      'mul' if s.cfg.func == CFG.MUL else
      'nop' if s.cfg.func == CFG.NOP else
      'phi' if s.cfg.func == CFG.PHI else
      '???'
    )
    src_a = (
      'n' if s.cfg.src_opd_a == CFG.SRC_NORTH else
      's' if s.cfg.src_opd_a == CFG.SRC_SOUTH else
      'w' if s.cfg.src_opd_a == CFG.SRC_WEST else
      'e' if s.cfg.src_opd_a == CFG.SRC_EAST else
      'S' if s.cfg.src_opd_a == CFG.SRC_SELF else
      '?'
    )
    src_b = (
      'n' if s.cfg.src_opd_b == CFG.SRC_NORTH else
      's' if s.cfg.src_opd_b == CFG.SRC_SOUTH else
      'w' if s.cfg.src_opd_b == CFG.SRC_WEST else
      'e' if s.cfg.src_opd_b == CFG.SRC_EAST else
      'S' if s.cfg.src_opd_b == CFG.SRC_SELF else
      '?'
    )
    src_bps = (
      'n' if s.cfg.src_bypass == CFG.SRC_NORTH else
      's' if s.cfg.src_bypass == CFG.SRC_SOUTH else
      'w' if s.cfg.src_bypass == CFG.SRC_WEST else
      'e' if s.cfg.src_bypass == CFG.SRC_EAST else
      'S' if s.cfg.src_bypass == CFG.SRC_SELF else
      '?'
    )
    dst_comp = (
      'n' if s.cfg.dst_compute == CFG.DST_NORTH else
      's' if s.cfg.dst_compute == CFG.DST_SOUTH else
      'w' if s.cfg.dst_compute == CFG.DST_WEST else
      'e' if s.cfg.dst_compute == CFG.DST_EAST else
      'S' if s.cfg.dst_compute == CFG.DST_SELF else
      '-' if s.cfg.dst_compute == CFG.DST_NONE else
      '?'
    )
    dst_bps = (
      'n' if s.cfg.dst_bypass == CFG.DST_NORTH else
      's' if s.cfg.dst_bypass == CFG.DST_SOUTH else
      'w' if s.cfg.dst_bypass == CFG.DST_WEST else
      'e' if s.cfg.dst_bypass == CFG.DST_EAST else
      'S' if s.cfg.dst_bypass == CFG.DST_SELF else
      '-' if s.cfg.dst_bypass == CFG.DST_NONE else
      '?'
    )

    q_str = f'{s.in_q_n.deq}|{s.in_q_s.deq}{s.in_q_w.deq}{s.in_q_e.deq}'
    op_and_node_deq_rdy = f'{s.ctrl.operands_deq_rdy}&{s.ctrl.node_recv_rdy}'
    deq_branch = f'{s.ctrl.bypass_opd}'
    other = f'{deq_branch}|{s.dpath.node.line_trace()}'
    alu = f'{s.dpath.node.alu.line_trace()}'
    node = f'{s.dpath.node.line_trace()}'
    reg  = f'{s.dpath.acc_reg.line_trace()}'

    cfg_str = f'{op_str}:{src_a}.{src_b}>{dst_comp}:{src_bps}>{dst_bps}'
    return f'{recv_str}({cfg_str}|{node}|{s.ctrl.bypass_send_rdy}){send_str}'
