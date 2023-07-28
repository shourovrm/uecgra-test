"""
==========================================================================
TileStaticCtrl.py
==========================================================================
Ctrl unit for static elastic CGRA tile.

Author : Yanghui Ou
  Date : August 8, 2019

"""
from pymtl3 import *

from .enums import CfgMsg, InputMux, OutputMux, RegMux, TileDirection as TD
from .RecurInitUnit import RecurInitUnit

class TileStaticCtrl( Component ):

  def construct( s, Type, CfgMsgType, elasticity="elastic" ):

    # Local parameters

    TD_NORTH = TD.NORTH
    TD_SOUTH = TD.SOUTH
    TD_WEST  = TD.WEST
    TD_EAST  = TD.EAST
    TD_SELF  = TD.SELF

    CfgMsg_SRC_NORTH = CfgMsg.SRC_NORTH
    CfgMsg_SRC_SOUTH = CfgMsg.SRC_SOUTH
    CfgMsg_SRC_WEST  = CfgMsg.SRC_WEST
    CfgMsg_SRC_EAST  = CfgMsg.SRC_EAST
    CfgMsg_SRC_SELF  = CfgMsg.SRC_SELF

    CfgMsg_DST_NORTH = CfgMsg.DST_NORTH
    CfgMsg_DST_SOUTH = CfgMsg.DST_SOUTH
    CfgMsg_DST_WEST  = CfgMsg.DST_WEST
    CfgMsg_DST_EAST  = CfgMsg.DST_EAST
    CfgMsg_DST_SELF  = CfgMsg.DST_SELF
    CfgMsg_DST_NONE  = CfgMsg.DST_NONE

    CfgMsg_Q_TYPE = CfgMsg.OP_Q_TYPE
    CfgMsg_B_TYPE = CfgMsg.OP_B_TYPE

    CfgMsg_NOP = CfgMsg.NOP
    CfgMsg_CP0 = CfgMsg.CP0
    CfgMsg_CP1 = CfgMsg.CP1
    CfgMsg_PHI = CfgMsg.PHI

    IM_NORTH = InputMux.NORTH
    IM_SOUTH = InputMux.SOUTH
    IM_WEST  = InputMux.WEST
    IM_EAST  = InputMux.EAST
    IM_SELF  = InputMux.SELF

    OM_COMPUTE = OutputMux.COMPUTE
    OM_BYPASS  = OutputMux.BYPASS
    OM_BPS_ALT = OutputMux.BPS_ALT
    RM_COMPUTE = RegMux.COMPUTE
    RM_BYPASS  = RegMux.BYPASS
    RM_BPS_ALT = RegMux.BPS_ALT
    RM_CONST   = RegMux.CONST

    # Clock and reset

    s.clk   = InPort( Bits1 )
    s.reset = InPort( Bits1 )

    # Interface

    s.deq_en_n  = OutPort( Bits1 )
    s.deq_en_s  = OutPort( Bits1 )
    s.deq_en_w  = OutPort( Bits1 )
    s.deq_en_e  = OutPort( Bits1 )

    s.deq_rdy_n = InPort ( Bits1 )
    s.deq_rdy_s = InPort ( Bits1 )
    s.deq_rdy_w = InPort ( Bits1 )
    s.deq_rdy_e = InPort ( Bits1 )

    s.send_en_n  = OutPort( Bits1 )
    s.send_en_s  = OutPort( Bits1 )
    s.send_en_w  = OutPort( Bits1 )
    s.send_en_e  = OutPort( Bits1 )

    s.send_rdy_n = InPort ( Bits1 )
    s.send_rdy_s = InPort ( Bits1 )
    s.send_rdy_w = InPort ( Bits1 )
    s.send_rdy_e = InPort ( Bits1 )

    s.cfg    = InPort( CfgMsgType )
    s.cfg_en = InPort( Bits1      )

    s.branch_cond = InPort( Type )

    s.node_cfg = OutPort( Bits5 )
    s.node_cfg_func = OutPort( Bits5 )

    s.acc_reg_en = OutPort( Bits1 )

    s.node_recv_en  = OutPort( Bits1 )
    s.node_recv_rdy = InPort ( Bits1 )
    s.node_send_en  = InPort ( Bits1 )
    s.node_send_rdy = OutPort( Bits1 )

    s.opd_a_mux_sel  = OutPort( Bits3 )
    s.opd_b_mux_sel  = OutPort( Bits3 )
    s.bypass_mux_sel = OutPort( Bits3 )
    s.altbps_mux_sel = OutPort( Bits3 )

    s.acc_mux_sel    = OutPort( Bits2 )
    s.send_mux_n_sel = OutPort( Bits2 )
    s.send_mux_s_sel = OutPort( Bits2 )
    s.send_mux_w_sel = OutPort( Bits2 )
    s.send_mux_e_sel = OutPort( Bits2 )

    # Recurrence init unit

    s.riu = RecurInitUnit()(
      clk   = s.clk,
      reset = s.reset,
    )

    # Convenience wires

    s.use_north_q = Wire( Bits1 )
    s.use_south_q = Wire( Bits1 )
    s.use_west_q  = Wire( Bits1 )
    s.use_east_q  = Wire( Bits1 )

    s.deq_rdys         = Wire( Bits4 )
    s.opd_a_deq_rdy    = Wire( Bits1 )
    s.opd_b_deq_rdy    = Wire( Bits1 )
    s.operands_deq_rdy = Wire( Bits1 )

    s.send_rdys        = Wire( Bits5 )
    s.node_send_rdys   = Wire( Bits5 )

    s.bypass_send_rdy  = Wire( Bits1 )
    s.bypass_send_rdys = Wire( Bits5 )
    s.bypass_deq_rdy   = Wire( Bits1 )
    s.bypass_opd       = Wire( Bits1 )

    s.altbps_send_rdy  = Wire( Bits1 )
    s.altbps_send_rdys = Wire( Bits5 )
    s.altbps_deq_rdy   = Wire( Bits1 )
    s.altbps_opd       = Wire( Bits1 )

    # Wires for branch
    s.is_branch    = Wire( Bits1 )
    s.branch_taken = Wire( Bits1 )
    s.br_src_data  = Wire( Bits3 )
    s.br_src_bool  = Wire( Bits3 )
    s.br_dst_true  = Wire( Bits5 )
    s.br_dst_false = Wire( Bits5 )
    s.br_deq_rdy   = Wire( Bits1 )
    s.br_send_rdy  = Wire( Bits1 )
    s.br_go_n      = Wire( Bits1 )
    s.br_go_s      = Wire( Bits1 )
    s.br_go_w      = Wire( Bits1 )
    s.br_go_e      = Wire( Bits1 )
    s.br_go_self   = Wire( Bits1 )

    # Logic

    s.deq_rdys[ TD_NORTH ] //= s.deq_rdy_n
    s.deq_rdys[ TD_SOUTH ] //= s.deq_rdy_s
    s.deq_rdys[ TD_WEST  ] //= s.deq_rdy_w
    s.deq_rdys[ TD_EAST  ] //= s.deq_rdy_e

    s.send_rdys[ TD_NORTH ] //= s.send_rdy_n
    s.send_rdys[ TD_SOUTH ] //= s.send_rdy_s
    s.send_rdys[ TD_WEST  ] //= s.send_rdy_w
    s.send_rdys[ TD_EAST  ] //= s.send_rdy_e
    s.send_rdys[ TD_SELF  ] //= b1(1)

    # Connections for branch
    s.br_src_data  //= s.cfg.src_opd_a
    s.br_src_bool  //= s.cfg.src_opd_b
    s.br_dst_true  //= s.cfg.dst_compute
    s.br_dst_false //= s.cfg.func

    #=====================================================================
    # Update blocks
    #=====================================================================

    @s.update
    def up_is_branch():
      s.is_branch = ( s.cfg.opcode == CfgMsg_B_TYPE )

    @s.update
    def up_branch_taken():
      s.branch_taken = s.branch_cond > Type(0)

    @s.update
    def up_br_deq_rdy():
      if s.is_branch:
        s.br_deq_rdy = s.deq_rdys[ s.cfg.src_opd_a[0:2] ] & s.deq_rdys[ s.cfg.src_opd_b[0:2] ]
      else:
        s.br_deq_rdy = b1(0)

    @s.update
    def up_br_dst():
      s.br_go_n    = s.br_dst_true [ TD_NORTH ] &  s.branch_taken | \
                     s.br_dst_false[ TD_NORTH ] & ~s.branch_taken
      s.br_go_s    = s.br_dst_true [ TD_SOUTH ] &  s.branch_taken | \
                     s.br_dst_false[ TD_SOUTH ] & ~s.branch_taken
      s.br_go_w    = s.br_dst_true [ TD_WEST  ] &  s.branch_taken | \
                     s.br_dst_false[ TD_WEST  ] & ~s.branch_taken
      s.br_go_e    = s.br_dst_true [ TD_EAST  ] &  s.branch_taken | \
                     s.br_dst_false[ TD_EAST  ] & ~s.branch_taken
      s.br_go_self = s.br_dst_true [ TD_SELF  ] &  s.branch_taken | \
                     s.br_dst_false[ TD_SELF  ] & ~s.branch_taken

    # NOTE: branch does not support broadcasting!
    @s.update
    def up_br_send_rdy():
      if s.is_branch:
        # Branch taken
        if s.branch_taken:
          if s.br_dst_true == CfgMsg_DST_NORTH:
            s.br_send_rdy = s.send_rdy_n
          elif s.br_dst_true == CfgMsg_DST_SOUTH:
            s.br_send_rdy = s.send_rdy_s
          elif s.br_dst_true == CfgMsg_DST_WEST:
            s.br_send_rdy = s.send_rdy_w
          elif s.br_dst_true == CfgMsg_DST_EAST:
            s.br_send_rdy = s.send_rdy_e
          else:
            s.br_send_rdy = b1(1)

        # Branch not taken
        else:
          if s.br_dst_false == CfgMsg_DST_NORTH:
            s.br_send_rdy = s.send_rdy_n
          elif s.br_dst_false == CfgMsg_DST_SOUTH:
            s.br_send_rdy = s.send_rdy_s
          elif s.br_dst_false == CfgMsg_DST_WEST:
            s.br_send_rdy = s.send_rdy_w
          elif s.br_dst_false == CfgMsg_DST_EAST:
            s.br_send_rdy = s.send_rdy_e
          else:
            s.br_send_rdy = b1(1)
      else:
        s.br_send_rdy = b1(0)

    # Dynamically choose between cp0 and cp1 if configured as PHI node or
    # branch
    @s.update
    def up_node_cfg():
      s.node_cfg = s.cfg.func
      if s.is_branch:
        s.node_cfg = CfgMsg_CP0
      elif s.cfg.func == CfgMsg_PHI:
        if s.opd_a_deq_rdy:
          s.node_cfg = CfgMsg_CP0
        elif s.opd_b_deq_rdy:
          s.node_cfg = CfgMsg_CP1

    # the `func` field of configuration signal
    @s.update
    def up_node_cfg_func():
      s.node_cfg_func = s.cfg.func

    #---------------------------------------------------------------------
    # Convenience wires
    #---------------------------------------------------------------------

    @s.update
    def up_use_logic():
      s.use_north_q = ( s.cfg.src_opd_a  == CfgMsg_SRC_NORTH ) | \
                      ( s.cfg.src_opd_b  == CfgMsg_SRC_NORTH )
      s.use_south_q = ( s.cfg.src_opd_a  == CfgMsg_SRC_SOUTH ) | \
                      ( s.cfg.src_opd_b  == CfgMsg_SRC_SOUTH )
      s.use_west_q  = ( s.cfg.src_opd_a  == CfgMsg_SRC_WEST  ) | \
                      ( s.cfg.src_opd_b  == CfgMsg_SRC_WEST  )
      s.use_east_q  = ( s.cfg.src_opd_a  == CfgMsg_SRC_EAST  ) | \
                      ( s.cfg.src_opd_b  == CfgMsg_SRC_EAST  )

    @s.update
    def up_opd_a_deq_rdy():
      if s.cfg.src_opd_a == CfgMsg_SRC_SELF:
        s.opd_a_deq_rdy = s.riu.deq_rdy if s.cfg.func == CfgMsg_PHI else b1(1)
      else:
        s.opd_a_deq_rdy = s.deq_rdys[ s.cfg.src_opd_a[0:2] ]

    @s.update
    def up_opd_b_deq_rdy():
      if s.cfg.src_opd_b == CfgMsg_SRC_SELF:
        s.opd_b_deq_rdy = s.riu.deq_rdy if s.cfg.func == CfgMsg_PHI else b1(1)
      else:
        s.opd_b_deq_rdy = s.deq_rdys[ s.cfg.src_opd_b[0:2] ]

    if elasticity == "elastic":
      @s.update
      def up_opeands_rdy():
        s.operands_deq_rdy = s.opd_a_deq_rdy & s.opd_b_deq_rdy

    elif elasticity == "inelastic":
      # Inelastic CGRA only looks at one of the two operand ready signals
      # because the compiler should ensure paths are balanced
      @s.update
      def up_opeands_rdy():
        s.operands_deq_rdy = s.opd_a_deq_rdy

    # Whether we are forwarding an operand? If so, the forwarded data must
    # be sent when it is consumed by the compute unit.
    # TODO : figure out what we should do when forwarding data from the
    # accumulate register and using the register at the same time?
    @s.update
    def up_bypass_opd():
      s.bypass_opd = ( s.cfg.src_bypass == s.cfg.src_opd_a ) | \
                     ( s.cfg.src_bypass == s.cfg.src_opd_b )
      if s.cfg.dst_bypass == CfgMsg_DST_NONE:
        s.bypass_opd = b1(0)

    @s.update
    def up_bypass_deq_rdy():
      if s.bypass_opd:
        s.bypass_deq_rdy = s.operands_deq_rdy
      elif s.cfg.src_bypass == CfgMsg_SRC_SELF:
        s.bypass_deq_rdy = b1(1)
      else:
        s.bypass_deq_rdy = s.deq_rdys[ s.cfg.src_bypass[0:2] ]

    @s.update
    def up_bypass_send_rdy():
      for i in range( 5 ):
        if s.cfg.dst_bypass[ i ]:
          s.bypass_send_rdys[i] = s.send_rdys[i]
        else:
          s.bypass_send_rdys[i] = b1(1)

      if s.cfg.dst_bypass == CfgMsg_DST_NONE:
        s.bypass_send_rdy = b1(0)
      else:
        s.bypass_send_rdy = reduce_and( s.bypass_send_rdys )

    @s.update
    def up_altbps_opd():
      s.altbps_opd = ( s.cfg.src_altbps == s.cfg.src_opd_a ) | \
                     ( s.cfg.src_altbps == s.cfg.src_opd_b )
      if s.cfg.dst_altbps == CfgMsg_DST_NONE:
        s.altbps_opd = b1(0)

    @s.update
    def up_altbps_deq_rdy():
      if s.altbps_opd:
        s.altbps_deq_rdy = s.operands_deq_rdy
      elif s.cfg.src_altbps == CfgMsg_SRC_SELF:
        s.altbps_deq_rdy = b1(1)
      else:
        s.altbps_deq_rdy = s.deq_rdys[ s.cfg.src_altbps[0:2] ]

    @s.update
    def up_altbps_send_rdy():
      for i in range( 5 ):
        if s.cfg.dst_altbps[ i ]:
          s.altbps_send_rdys[i] = s.send_rdys[i]
        else:
          s.altbps_send_rdys[i] = b1(1)

      if s.cfg.dst_altbps == CfgMsg_DST_NONE:
        s.altbps_send_rdy = b1(0)
      else:
        s.altbps_send_rdy = reduce_and( s.altbps_send_rdys )

    #---------------------------------------------------------------------
    # deq signals
    #---------------------------------------------------------------------

    @s.update
    def up_riu_deq_en():
      s.riu.deq_en = ( s.cfg.func == CfgMsg_PHI ) & s.node_recv_rdy & \
                     s.riu.deq_rdy & ~s.cfg_en & ~s.is_branch

    @s.update
    def up_deq_en_n():
      # Kills enable signal during configuration
      if s.cfg_en:
        s.deq_en_n = b1(0)

      # Bypass operand
      elif s.bypass_opd & ( s.cfg.src_bypass == CfgMsg_SRC_NORTH ):
        s.deq_en_n = s.bypass_deq_rdy & s.bypass_send_rdy & s.node_recv_rdy

      # Bypass non-operand
      elif s.cfg.src_bypass == CfgMsg_SRC_NORTH:
        s.deq_en_n = s.bypass_deq_rdy & s.bypass_send_rdy

      # Alternative bypass operand
      elif s.altbps_opd & ( s.cfg.src_altbps == CfgMsg_SRC_NORTH ) :
        s.deq_en_n = s.altbps_deq_rdy & s.altbps_send_rdy & s.node_recv_rdy

      # Alternative bypass non-operand
      elif s.cfg.src_altbps == CfgMsg_SRC_NORTH:
        s.deq_en_n = s.altbps_deq_rdy & s.altbps_send_rdy

      # Operand without bypassing
      elif s.use_north_q:
        # For phi node only either of src needs to be ready
        if s.cfg.func == CfgMsg_PHI:
          s.deq_en_n = s.deq_rdy_n
        else:
          s.deq_en_n = s.operands_deq_rdy & s.node_recv_rdy

      # Not selected
      else:
        s.deq_en_n = b1(0)

    @s.update
    def up_deq_en_s():
      # Kills enable signal during configuration
      if s.cfg_en:
        s.deq_en_s = b1(0)
      # Bypass operand
      elif s.bypass_opd & ( s.cfg.src_bypass == CfgMsg_SRC_SOUTH ):
        s.deq_en_s = s.bypass_deq_rdy & s.bypass_send_rdy & s.node_recv_rdy

      # Bypass non-operand
      elif s.cfg.src_bypass == CfgMsg_SRC_SOUTH:
        s.deq_en_s = s.bypass_deq_rdy & s.bypass_send_rdy

      # Alternative bypass operand
      elif s.altbps_opd & ( s.cfg.src_altbps == CfgMsg_SRC_SOUTH ):
        s.deq_en_s = s.altbps_deq_rdy & s.altbps_send_rdy & s.node_recv_rdy

      # Alternative bypass non-operand
      elif s.cfg.src_altbps == CfgMsg_SRC_SOUTH:
        s.deq_en_s = s.altbps_deq_rdy & s.altbps_send_rdy

      # Operand without bypassing
      elif s.use_south_q:
        # For phi node only either of src needs to be ready
        if s.cfg.func == CfgMsg_PHI:
          s.deq_en_s = s.deq_rdy_s
        else:
          s.deq_en_s = s.operands_deq_rdy & s.node_recv_rdy

      # Not selected
      else:
        s.deq_en_s = b1(0)

    @s.update
    def up_deq_en_w():
      # Kills enable signal during configuration
      if s.cfg_en:
        s.deq_en_w = b1(0)
      # Bypass operand
      elif s.bypass_opd & ( s.cfg.src_bypass == CfgMsg_SRC_WEST ):
        s.deq_en_w = s.bypass_deq_rdy & s.bypass_send_rdy & s.node_recv_rdy

      # Bypass non-operand
      elif s.cfg.src_bypass == CfgMsg_SRC_WEST:
        s.deq_en_w = s.bypass_deq_rdy & s.bypass_send_rdy

      # Alternative bypass operand
      elif s.altbps_opd & ( s.cfg.src_altbps == CfgMsg_SRC_WEST ):
        s.deq_en_w = s.altbps_deq_rdy & s.altbps_send_rdy & s.node_recv_rdy

      # Alternative bypass non-operand
      elif s.cfg.src_altbps == CfgMsg_SRC_WEST:
        s.deq_en_w = s.altbps_deq_rdy & s.altbps_send_rdy

      # Operand without bypassing
      elif s.use_west_q:
        # For phi node only either of src needs to be ready
        if s.cfg.func == CfgMsg_PHI:
          s.deq_en_w = s.deq_rdy_w
        else:
          s.deq_en_w = s.operands_deq_rdy & s.node_recv_rdy

      # Not selected
      else:
        s.deq_en_w = b1(0)

    @s.update
    def up_deq_en_e():
      # Kills enable signal during configuration
      if s.cfg_en:
        s.deq_en_e = b1(0)
      # Bypass operand
      elif s.bypass_opd & ( s.cfg.src_bypass == CfgMsg_SRC_EAST ):
        s.deq_en_e = s.bypass_deq_rdy & s.bypass_send_rdy & s.node_recv_rdy

      # Bypass non-operand
      elif s.cfg.src_bypass == CfgMsg_SRC_EAST:
        s.deq_en_e = s.bypass_deq_rdy & s.bypass_send_rdy

      # Alternative bypass operand
      elif s.altbps_opd & ( s.cfg.src_altbps == CfgMsg_SRC_EAST ):
        s.deq_en_e = s.altbps_deq_rdy & s.altbps_send_rdy & s.node_recv_rdy

      # Alternative bypass non-operand
      elif s.cfg.src_altbps == CfgMsg_SRC_EAST:
        s.deq_en_e = s.altbps_deq_rdy & s.altbps_send_rdy

      # Operand without bypassing
      elif s.use_east_q:
        # For phi node only either of src needs to be ready
        if s.cfg.func == CfgMsg_PHI:
          s.deq_en_e = s.deq_rdy_e
        else:
          s.deq_en_e = s.operands_deq_rdy & s.node_recv_rdy

      # Not selected
      else:
        s.deq_en_e = b1(0)

    #---------------------------------------------------------------------
    # Input muxes
    #---------------------------------------------------------------------

    s.opd_a_mux_sel  //= s.cfg.src_opd_a
    s.opd_b_mux_sel  //= s.cfg.src_opd_b
    s.bypass_mux_sel //= s.cfg.src_bypass
    s.altbps_mux_sel //= s.cfg.src_altbps

    #---------------------------------------------------------------------
    # en signal of acc reg
    #---------------------------------------------------------------------

    @s.update
    def up_acc_reg_en():
      if s.cfg_en:
        # NOTE: THIS IS TEMPORARY
        s.acc_reg_en = b1(1)
      elif s.cfg.dst_compute[ TD_SELF ]:
        s.acc_reg_en = s.node_send_en
      elif s.cfg.dst_bypass[ TD_SELF ]:
        s.acc_reg_en = s.bypass_deq_rdy
      elif s.cfg.dst_altbps[ TD_SELF ]:
        s.acc_reg_en = s.altbps_deq_rdy
      else:
        s.acc_reg_en = b1(0)

    #---------------------------------------------------------------------
    # recv_en signal of compute unit
    #---------------------------------------------------------------------

    @s.update
    def up_node_recv_en():
      if s.cfg_en:
        s.node_recv_en = b1(0)
      elif s.cfg.func == CfgMsg_NOP:
        s.node_recv_en = b1(0)
      else:
        # For PHI node only one operand needs to be ready
        if s.cfg.func == CfgMsg_PHI:
          if ~s.bypass_opd & ~s.altbps_opd:
            s.node_recv_en = ( s.opd_a_deq_rdy | s.opd_b_deq_rdy ) & s.node_recv_rdy
          elif s.bypass_opd:
            s.node_recv_en = ( s.opd_a_deq_rdy | s.opd_b_deq_rdy ) & s.bypass_deq_rdy & s.node_recv_rdy
          elif s.altbps_opd:
            s.node_recv_en = ( s.opd_a_deq_rdy | s.opd_b_deq_rdy ) & s.altbps_deq_rdy & s.node_recv_rdy
          else: # s.bypass_opd & s.altbps_opd
            s.node_recv_en = ( s.opd_a_deq_rdy | s.opd_b_deq_rdy ) & s.bypass_deq_rdy & s.altbps_deq_rdy & s.node_recv_rdy

        elif s.bypass_opd:
          s.node_recv_en = s.operands_deq_rdy & s.bypass_deq_rdy & s.node_recv_rdy
        elif s.altbps_opd:
          s.node_recv_en = s.operands_deq_rdy & s.altbps_deq_rdy & s.node_recv_rdy
        else:
          s.node_recv_en = s.operands_deq_rdy & s.node_recv_rdy

    #---------------------------------------------------------------------
    # send_rdy signal of compute unit
    #---------------------------------------------------------------------
    # Consider bypass operand here.

    @s.update
    def up_node_send_rdy():
      for i in range( 5 ):
        if s.cfg.dst_compute[i]:
          s.node_send_rdys[i] = s.send_rdys[i]
        else:
          s.node_send_rdys[i] = b1(1)

      if s.is_branch:
        if s.bypass_opd:
          s.node_send_rdy = s.br_send_rdy & s.bypass_send_rdy
        elif s.altbps_opd:
          s.node_send_rdy = s.br_send_rdy & s.altbps_send_rdy
        else:
          s.node_send_rdy = s.br_send_rdy

      elif s.cfg.dst_compute == CfgMsg_DST_NONE:
        s.node_send_rdy = b1(0)

      else:
        # FIXME: This part is tricky and may not be correct.
        if s.bypass_opd & s.altbps_opd:
          s.node_send_rdy = reduce_and( s.node_send_rdys ) & s.bypass_send_rdy & s.altbps_send_rdy
        elif s.bypass_opd:
          s.node_send_rdy = reduce_and( s.node_send_rdys ) & s.bypass_send_rdy
        elif s.altbps_opd:
          s.node_send_rdy = reduce_and( s.node_send_rdys ) & s.altbps_send_rdy

        # FIXME: Why do I AND the bypass_send_rdy here?
        elif s.cfg.dst_bypass != CfgMsg_DST_NONE:
          s.node_send_rdy = reduce_and( s.node_send_rdys ) # & s.bypass_send_rdy
        elif s.cfg.dst_altbps != CfgMsg_DST_NONE:
          s.node_send_rdy = reduce_and( s.node_send_rdys ) # & s.altbps_send_rdy

        else:
          s.node_send_rdy = reduce_and( s.node_send_rdys )

    #---------------------------------------------------------------------
    # Output muxess.acc_mux_sel
    #---------------------------------------------------------------------
    # For output muxes, if compute and bypass both goes high, prioritize
    # compute.

    @s.update
    def up_acc_mux_sel():
      if s.cfg_en:
        s.acc_mux_sel = b2( RM_CONST )

      # Branch
      elif s.is_branch:
        s.acc_mux_sel = b2(0)
        if s.cfg.dst_bypass[ TD_SELF ]:
          s.acc_mux_sel = b2( RM_BYPASS )
        if s.cfg.dst_altbps[ TD_SELF ]:
          s.acc_mux_sel = b2( RM_BPS_ALT )
        if s.br_dst_true[ TD_SELF ] | s.br_dst_true[ TD_SELF ]:
          s.acc_mux_sel = b2( RM_COMPUTE )

      # Other operations
      else:
        s.acc_mux_sel = b2(0)
        if s.cfg.dst_bypass[ TD_SELF ]:
          s.acc_mux_sel = b2( RM_BYPASS )
        if s.cfg.dst_altbps[ TD_SELF ]:
          s.acc_mux_sel = b2( RM_BPS_ALT )
        if s.cfg.dst_compute[ TD_SELF ]:
          s.acc_mux_sel = b2( RM_COMPUTE )

    @s.update
    def up_send_mux_n_sel():
      # Branch
      if s.is_branch:
        s.send_mux_n_sel = b2(0)
        if s.cfg.dst_bypass[ TD_NORTH ]:
          s.send_mux_n_sel = b2( OM_BYPASS )
        if s.cfg.dst_altbps[ TD_NORTH ]:
          s.send_mux_n_sel = b2( OM_BPS_ALT )
        if s.br_dst_true[ TD_NORTH ] | s.br_dst_true[ TD_NORTH ]:
          s.send_mux_n_sel = b2( OM_COMPUTE )
      # Other
      else:
        s.send_mux_n_sel = b2(0)
        if s.cfg.dst_bypass[ TD_NORTH ]:
          s.send_mux_n_sel = b2( OM_BYPASS )
        if s.cfg.dst_altbps[ TD_NORTH ]:
          s.send_mux_n_sel = b2( OM_BPS_ALT )
        if s.cfg.dst_compute[ TD_NORTH ]:
          s.send_mux_n_sel = b2( OM_COMPUTE )

    @s.update
    def up_send_mux_s_sel():
      # Branch
      if s.is_branch:
        s.send_mux_s_sel = b2(0)
        if s.cfg.dst_bypass[ TD_SOUTH ]:
          s.send_mux_s_sel = b2( OM_BYPASS )
        if s.cfg.dst_altbps[ TD_SOUTH ]:
          s.send_mux_s_sel = b2( OM_BPS_ALT )
        if s.br_dst_true[ TD_SOUTH ] | s.br_dst_true[ TD_SOUTH ]:
          s.send_mux_s_sel = b2( OM_COMPUTE )
      # Other
      else:
        s.send_mux_s_sel = b2(0)
        if s.cfg.dst_bypass[ TD_SOUTH ]:
          s.send_mux_s_sel = b2( OM_BYPASS )
        if s.cfg.dst_altbps[ TD_SOUTH ]:
          s.send_mux_s_sel = b2( OM_BPS_ALT )
        if s.cfg.dst_compute[ TD_SOUTH ]:
          s.send_mux_s_sel = b2( OM_COMPUTE )

    @s.update
    def up_send_mux_w_sel():
      # Branch
      if s.is_branch:
        s.send_mux_w_sel = b2(0)
        if s.cfg.dst_bypass[ TD_WEST ]:
          s.send_mux_w_sel = b2( OM_BYPASS )
        if s.cfg.dst_altbps[ TD_WEST ]:
          s.send_mux_w_sel = b2( OM_BPS_ALT )
        if s.br_dst_true[ TD_WEST ] | s.br_dst_true[ TD_WEST ]:
          s.send_mux_w_sel = b2( OM_COMPUTE )
      # Other
      else:
        s.send_mux_w_sel = b2(0)
        if s.cfg.dst_bypass[ TD_WEST ]:
          s.send_mux_w_sel = b2( OM_BYPASS )
        if s.cfg.dst_altbps[ TD_WEST ]:
          s.send_mux_w_sel = b2( OM_BPS_ALT )
        if s.cfg.dst_compute[ TD_WEST ]:
          s.send_mux_w_sel = b2( OM_COMPUTE )

    @s.update
    def up_send_mux_e_sel():
      # Branch
      if s.is_branch:
        s.send_mux_e_sel = b2(0)
        if s.cfg.dst_bypass[ TD_EAST ]:
          s.send_mux_e_sel = b2( OM_BYPASS )
        if s.cfg.dst_altbps[ TD_EAST ]:
          s.send_mux_e_sel = b2( OM_BPS_ALT )
        if s.br_dst_true[ TD_EAST ] | s.br_dst_true[ TD_EAST ]:
          s.send_mux_e_sel = b2( OM_COMPUTE )
      # Other
      else:
        s.send_mux_e_sel = b2(0)
        if s.cfg.dst_bypass[ TD_EAST ]:
          s.send_mux_e_sel = b2( OM_BYPASS )
        if s.cfg.dst_altbps[ TD_EAST ]:
          s.send_mux_e_sel = b2( OM_BPS_ALT )
        if s.cfg.dst_compute[ TD_EAST ]:
          s.send_mux_e_sel = b2( OM_COMPUTE )

    #---------------------------------------------------------------------
    # send_en signals
    #---------------------------------------------------------------------

    @s.update
    def up_send_en_n():
      # Kills enable signal during configuration
      s.send_en_n = b1(0)
      if ~s.cfg_en:
        # Bypass
        if s.bypass_opd & s.cfg.dst_bypass[ TD_NORTH ]:
          s.send_en_n = s.node_send_en
        elif s.cfg.dst_bypass[ TD_NORTH ]:
          s.send_en_n = s.bypass_deq_rdy & s.bypass_send_rdy

        # Alternative bypass
        if s.altbps_opd & s.cfg.dst_altbps[ TD_NORTH ]:
          s.send_en_n = s.node_send_en
        elif s.cfg.dst_altbps[ TD_NORTH ]:
          s.send_en_n = s.altbps_deq_rdy & s.altbps_send_rdy

        # Branch
        if s.is_branch:
          if ( s.branch_cond != Type(0) and s.br_dst_true [ TD_NORTH ] ) or \
             ( s.branch_cond == Type(0) and s.br_dst_false[ TD_NORTH ] ):
            s.send_en_n = s.node_send_en & s.br_go_n
        # Other
        elif s.cfg.dst_compute[ TD_NORTH ]:
            s.send_en_n = s.node_send_en

    @s.update
    def up_send_en_s():
      # Kills enable signal during configuration
      s.send_en_s = b1(0)
      if ~s.cfg_en:
        # Bypass
        if s.bypass_opd & s.cfg.dst_bypass[ TD_SOUTH ]:
          s.send_en_s = s.node_send_en
        elif s.cfg.dst_bypass[ TD_SOUTH ]:
          s.send_en_s = s.bypass_deq_rdy & s.bypass_send_rdy

        # Alternative bypass
        if s.altbps_opd & s.cfg.dst_altbps[ TD_SOUTH ]:
          s.send_en_s = s.node_send_en
        elif s.cfg.dst_altbps[ TD_SOUTH ]:
          s.send_en_s = s.altbps_deq_rdy & s.altbps_send_rdy

        # Branch
        if s.is_branch:
          if ( s.branch_cond != Type(0) and s.br_dst_true [ TD_SOUTH ] ) or \
             ( s.branch_cond == Type(0) and s.br_dst_false[ TD_SOUTH ] ):
            s.send_en_s = s.node_send_en & s.br_go_s
        # Other
        elif s.cfg.dst_compute[ TD_SOUTH ]:
            s.send_en_s = s.node_send_en

    @s.update
    def up_send_en_w():
      # Kills enable signal during configuration
      s.send_en_w = b1(0)
      if ~s.cfg_en:
        # Bypass
        if s.bypass_opd & s.cfg.dst_bypass[ TD_WEST ]:
          s.send_en_w = s.node_send_en
        elif s.cfg.dst_bypass[ TD_WEST ]:
          s.send_en_w = s.bypass_deq_rdy & s.bypass_send_rdy

        # Alternative bypass
        if s.altbps_opd & s.cfg.dst_altbps[ TD_WEST ]:
          s.send_en_w = s.node_send_en
        elif s.cfg.dst_altbps[ TD_WEST ]:
          s.send_en_w = s.altbps_deq_rdy & s.altbps_send_rdy

        # Branch
        if s.is_branch:
          if ( s.branch_cond != Type(0) and s.br_dst_true [ TD_WEST ] ) or \
             ( s.branch_cond == Type(0) and s.br_dst_false[ TD_WEST ] ):
            s.send_en_w = s.node_send_en & s.br_go_w
        # Other
        elif s.cfg.dst_compute[ TD_WEST ]:
            s.send_en_w = s.node_send_en

    @s.update
    def up_send_en_e():
      # Kills enable signal during configuration
      s.send_en_e = b1(0)
      if ~s.cfg_en:
        # Bypass
        if s.bypass_opd & s.cfg.dst_bypass[ TD_EAST ]:
          s.send_en_e = s.node_send_en
        elif s.cfg.dst_bypass[ TD_EAST ]:
          s.send_en_e = s.bypass_deq_rdy & s.bypass_send_rdy

        # Alternative bypass
        if s.altbps_opd & s.cfg.dst_altbps[ TD_EAST ]:
          s.send_en_e = s.node_send_en
        elif s.cfg.dst_altbps[ TD_EAST ]:
          s.send_en_e = s.altbps_deq_rdy & s.altbps_send_rdy

        # Branch
        if s.is_branch:
          if ( s.branch_cond != Type(0) and s.br_dst_true [ TD_EAST ] ) or \
             ( s.branch_cond == Type(0) and s.br_dst_false[ TD_EAST ] ):
            s.send_en_e = s.node_send_en & s.br_go_e
        # Other
        elif s.cfg.dst_compute[ TD_EAST ]:
            s.send_en_e = s.node_send_en
