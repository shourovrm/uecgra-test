#=========================================================================
# TileStatic_RGALS.py
#=========================================================================
# Provides an RGALS wrapper and a dummy synchronous wrapper. Both components
# have the same interface.
#
# Author: Peitian Pan
# Date  : Aug 12, 2019

from pymtl3 import *
from pymtl3.stdlib.rtl import RegEnRst
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.connects import connect_pairs

from fifos.BisyncQueue import BisyncQueue
from clock.enums import CLK_FAST, CLK_SLOW, CLK_NOMINAL
from clock.clock_switcher import ClockSwitcher_3 as ClockSwitcher
from clock.clock_counter import ClockCounter
from crossing.tile_suppress import TileSuppress
from misc.adapters import Recv2Send

from .enums import CfgMsg as CFG, TileDirection as TD
from .TileStaticDpath import TileStaticDpath
from .TileStaticCtrl import TileStaticCtrl
from .RgalsClkIfc import RgalsClkIfc

class TileStatic_RGALS_wrapper( Component ):

  def construct( s, Type, CfgMsgType, mul_ncycles=0, clk_in='nominal' ):

    # In order to correctly generate clock trees for the bisync queues,
    # the wrapper does not connect the input clocks to the 4 bisync queues
    # at the input side. Instead, the wrapped tile will connect clk_out
    # of the clock switcher to the input clocks (we are using the nominal
    # frequency anayways).

    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Add RGALS clock signals

    s.clk_rgals = RgalsClkIfc()

    s.clk_rate_in = [ InPort( Bits2 ) for _ in range(4) ]

    s.clk_out = [ OutPort( Bits1 ) for _ in range(4) ]
    s.clk_rate_out = [ OutPort( Bits2 ) for _ in range(4) ]

    s.recv = [ RecvIfcRTL( Type ) for _ in range(4) ]
    s.send = [ SendIfcRTL( Type ) for _ in range(4) ]

    s.cfg    = InPort( CfgMsgType )
    s.cfg_en = InPort( Bits1 )
    s.imm    = InPort( Type )

    s.tile = TileStatic_RGALS( Type, CfgMsgType, mul_ncycles, clk_network=True )
    s.in_q = [ BisyncQueue( Type, num_entries=2 ) for _ in range(4) ]
    s.out_q = [ BisyncQueue( Type, num_entries=2 ) for _ in range(4) ]
    s.adapter = [ Recv2Send( Type ) for _ in range(4) ]

    s.reset //= s.tile.reset
    s.clk_rgals //= s.tile.clk_rgals

    for i in range(4):
      s.clk_rate_in[i] //= s.tile.clk_rate_in[i]
      s.clk_rate_out[i] //= s.tile.clk_rate_out[i]
      s.clk_out[i] //= s.tile.clk_out[i]
      s.cfg //= s.tile.cfg
      s.cfg_en //= s.tile.cfg_en
      s.imm //= s.tile.imm

      s.in_q[i].w_clk //= s.clk
      if clk_in == 'fast':
        s.in_q[i].r_clk //= s.clk_rgals.clk1
        # s.tile.clk_in[i] //= s.clk_rgals.clk1
      elif clk_in == 'slow':
        s.in_q[i].r_clk //= s.clk_rgals.clk2
        # s.tile.clk_in[i] //= s.clk_rgals.clk2
      else:
        s.in_q[i].r_clk //= s.clk_rgals.clk3
        # s.tile.clk_in[i] //= s.clk_rgals.clk3
      s.in_q[i].reset //= s.reset
      s.in_q[i].enq //= s.recv[i]
      s.in_q[i].deq //= s.tile.recv[i]

      s.out_q[i].w_clk //= s.clk_out[i]
      s.out_q[i].r_clk //= s.clk
      s.out_q[i].reset //= s.reset
      s.out_q[i].enq //= s.tile.send[i]
      s.out_q[i].deq //= s.adapter[i].recv
      s.send[i] //= s.adapter[i].send

class TileStatic_RGALS( Component ):

  def construct( s, Type, CfgMsgType, mul_ncycles=0, clk_network=False, fifo_latency=0 ):

    s.reset = InPort( Bits1 )

    # Add RGALS clock signals

    s.clk_rgals = RgalsClkIfc()

    # Add clock switcher

    s.domain_clk = Wire( Bits1 )
    s.domain_clk_rate = Wire( Bits2 )

    s.clk_switcher = ClockSwitcher()(
      clk1 = s.clk_rgals.clk1,
      clk2 = s.clk_rgals.clk2,
      clk3 = s.clk_rgals.clk3,

      clk_reset = s.clk_rgals.clk_reset,
      switch_val = s.clk_rgals.clksel.en,
      switch_msg = s.clk_rgals.clksel.msg,
      switch_rdy = s.clk_rgals.clksel.rdy,
      clk_out = s.domain_clk,
    )

    # Interface

    if not clk_network:
      s.clk_in = [ InPort( Bits1 ) for _ in range(4) ]
    else:
      # If the tile is required to generate the clock network,
      # we need to connect the output clock from the clock switcher
      # to the input clocks of bisync queues.
      s.clk_in = [ Wire( Bits1 ) for _ in range(4) ]
      for i in range(4):
        s.clk_in[i] //= s.domain_clk
    s.clk_rate_in = [ InPort( Bits2 ) for _ in range(4) ]

    s.clk_out = [ OutPort( Bits1 ) for _ in range(4) ]
    s.clk_rate_out = [ OutPort( Bits2 ) for _ in range(4) ]

    s.recv = [ RecvIfcRTL( Type ) for _ in range(4) ]
    s.send = [ SendIfcRTL( Type ) for _ in range(4) ]

    s.cfg    = InPort( CfgMsgType )
    s.cfg_en = InPort( Bits1 )
    s.imm    = InPort( Type )

    # Component

    s.ctrl  = TileStaticCtrl( Type, CfgMsgType )
    s.dpath = TileStaticDpath( Type, mul_ncycles, DataGating = False )

    # Bisynchronous input buffers

    s.in_qs = [ BisyncQueue( Type, num_entries=2, fifo_latency=fifo_latency )(
      w_clk = s.clk_in[i],
      r_clk = s.domain_clk,
      reset = s.reset,
    ) for i in range(4) ]

    # Suppress logic

    s.suppress = TileSuppress()

    # Connect clock interface of the suppress module

    s.suppress.reset //= s.reset
    s.suppress.clk_ifc.clk1 //= s.clk_rgals.clk1
    s.suppress.clk_ifc.clk2 //= s.clk_rgals.clk2
    s.suppress.clk_ifc.clk3 //= s.clk_rgals.clk3
    s.suppress.clk_ifc.clk_reset //= s.clk_rgals.clk_reset
    s.suppress.clk_ifc.domain_clk //= s.domain_clk
    s.suppress.clk_ifc.domain_clk_rate //= s.domain_clk_rate

    # Connect all four input queues to the suppress module

    for i in range(4):
      s.suppress.q_ifcs[i].clk_rate //= s.clk_rate_in[i]
      s.suppress.q_ifcs[i].is_empty //= s.in_qs[i].is_empty
      s.suppress.q_ifcs[i].is_empty_next //= s.in_qs[i].is_empty_next
      s.suppress.q_ifcs[i].from_q_deq_rdy //= s.in_qs[i].deq.rdy
      s.suppress.q_ifcs[i].to_q_deq_en //= s.in_qs[i].deq.en

    # Connect suppress module to tile control unit

    s.suppress.q_ifcs[TD.NORTH].from_ctrl_deq_en //= s.ctrl.deq_en_n
    s.suppress.q_ifcs[TD.NORTH].to_ctrl_deq_rdy //= s.ctrl.deq_rdy_n
    s.suppress.q_ifcs[TD.SOUTH].from_ctrl_deq_en //= s.ctrl.deq_en_s
    s.suppress.q_ifcs[TD.SOUTH].to_ctrl_deq_rdy //= s.ctrl.deq_rdy_s
    s.suppress.q_ifcs[TD.WEST ].from_ctrl_deq_en //= s.ctrl.deq_en_w
    s.suppress.q_ifcs[TD.WEST ].to_ctrl_deq_rdy //= s.ctrl.deq_rdy_w
    s.suppress.q_ifcs[TD.EAST ].from_ctrl_deq_en //= s.ctrl.deq_en_e
    s.suppress.q_ifcs[TD.EAST ].to_ctrl_deq_rdy //= s.ctrl.deq_rdy_e

    # Hook up the enq side of queues

    for i in range(4):
      s.in_qs[i].enq //= s.recv[i]

    # Connect clk and reset

    s.ctrl.clk //= s.domain_clk
    s.ctrl.reset //= s.reset
    s.dpath.clk //= s.domain_clk
    s.dpath.reset //= s.reset
    s.cfg.clk_self //= s.domain_clk_rate

    # Connect all clk_out

    for i in range(4):
      s.clk_out[i] //= s.domain_clk
      s.clk_rate_out[i] //= s.domain_clk_rate

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
    # NOTE: the val/rdy signals of the dequeue side will be suppressed
    # if the rising edge of the current clock domain is too close
    # to the edge when input data was registered to the input bisynchronous queue.

    connect_pairs(
      s.in_qs[TD.NORTH].deq.msg, s.dpath.deq_msg_n,

      s.in_qs[TD.SOUTH].deq.msg, s.dpath.deq_msg_s,

      s.in_qs[TD.WEST ].deq.msg, s.dpath.deq_msg_w,

      s.in_qs[TD.EAST ].deq.msg, s.dpath.deq_msg_e,
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
      'cp0' if s.cfg.opcode == CFG.CP0 else
      'cp1' if s.cfg.opcode == CFG.CP1 else
      'add' if s.cfg.opcode == CFG.ADD else
      'sll' if s.cfg.opcode == CFG.SLL else
      'srl' if s.cfg.opcode == CFG.SRL else
      'and' if s.cfg.opcode == CFG.AND else
      'mul' if s.cfg.opcode == CFG.MUL else
      'nop' if s.cfg.opcode == CFG.NOP else
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

    q_str = f'{s.in_qs[0].deq}|{s.in_qs[1].deq}{s.in_qs[2].deq}{s.in_qs[3].deq}'
    op_and_node_deq_rdy = f'{s.ctrl.operands_deq_rdy}&{s.ctrl.node_recv_rdy}'
    deq_branch = f'{s.ctrl.bypass_opd}'
    other = f'{deq_branch}|{s.dpath.node.line_trace()}'

    cfg_str = f'{op_str}:{src_a}.{src_b}>{dst_comp}:{src_bps}>{dst_bps}'
    return f'{recv_str}({cfg_str}){send_str}'
