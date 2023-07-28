#=========================================================================
# Proc.py
#=========================================================================

from pymtl3             import *
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.ifcs import InValRdyIfc, OutValRdyIfc
from pymtl3.stdlib.rtl.valrdy_queues import BypassQueue1RTL
from pymtl3.stdlib.connects import connect_pairs
from proc.tinyrv2_encoding  import disassemble_inst
from proc.TinyRV2InstPRTL   import inst_dict

from proc.ProcDpath  import ProcDpath
from proc.ProcCtrl   import ProcCtrl
from proc.DropUnitPRTL import DropUnitPRTL

class BypassQueue2RTL( Component ):

  def construct( s, Type ):
    s.enq = InValRdyIfc( Type )
    s.deq = OutValRdyIfc( Type )
    s.q1 = BypassQueue1RTL( Type )( enq = s.enq )
    s.q2 = BypassQueue1RTL( Type )( enq = s.q1.deq, deq = s.deq )

class Proc( Component ):

  def construct( s, num_cores = 1, mul_mode = 'varlat' ):
    dtype = mk_bits(32)

    s.core_id   = InPort( dtype )

    # Proc/Mngr Interface

    s.mngr2proc = InValRdyIfc ( dtype )
    s.proc2mngr = OutValRdyIfc( dtype )

    # Instruction Memory Request/Response Interface

    s.imemreq   = OutValRdyIfc( Bits77 )
    s.imemresp  = InValRdyIfc ( Bits47 )

    # Data Memory Request/Response Interface

    s.dmemreq   = OutValRdyIfc( Bits77 )
    s.dmemresp  = InValRdyIfc ( Bits47 )

    # val_W port used for counting commited insts.

    s.commit_inst = OutPort( Bits1 )

    # stats_en

    s.stats_en    = OutPort( Bits1 )

    # Bypass queues

    s.imemreq_q   = BypassQueue2RTL( Bits77 )( deq = s.imemreq )
    s.dmemreq_q   = BypassQueue1RTL( Bits77 )( deq = s.dmemreq )
    s.proc2mngr_q = BypassQueue1RTL( dtype )( deq = s.proc2mngr )

    # imem drop unit

    s.imemresp_drop = m = DropUnitPRTL( dtype )
    connect_pairs(
      m.in_.val, s.imemresp.val,
      m.in_.rdy, s.imemresp.rdy,
      m.in_.msg, s.imemresp.msg[15:47],
    )

    # Control

    s.ctrl  = ProcCtrl()(

      # imem port
      imemresp_drop = s.imemresp_drop.drop,
      imemreq_val   = s.imemreq_q.enq.val,
      imemreq_rdy   = s.imemreq_q.enq.rdy,
      imemresp_val  = s.imemresp_drop.out.val,
      imemresp_rdy  = s.imemresp_drop.out.rdy,

      # dmem port
      dmemreq_val   = s.dmemreq_q.enq.val,
      dmemreq_rdy   = s.dmemreq_q.enq.rdy,
      dmemreq_msg_type = s.dmemreq_q.enq.msg[0:3],
      dmemresp_val  = s.dmemresp.val,
      dmemresp_rdy  = s.dmemresp.rdy,

      # proc2mngr and mngr2proc
      proc2mngr_val = s.proc2mngr_q.enq.val,
      proc2mngr_rdy = s.proc2mngr_q.enq.rdy,
      mngr2proc_val = s.mngr2proc.val,
      mngr2proc_rdy = s.mngr2proc.rdy,

      # commit inst for counting
      commit_inst = s.commit_inst
    )

    # Dpath

    s.dpath = ProcDpath( num_cores, mul_mode )(
      core_id = s.core_id,

      # imem ports
      imemreq_msg       = s.imemreq_q.enq.msg,
      imemresp_msg_data = s.imemresp_drop.out.msg,

      # dmem ports
      dmemreq_msg_addr  =  s.dmemreq_q.enq.msg[11:43],
      dmemreq_msg_data  =  s.dmemreq_q.enq.msg[45:77],
      dmemresp_msg_data = s.dmemresp.msg[15:47],

      # mngr

      mngr2proc_data = s.mngr2proc.msg,
      proc2mngr_data = s.proc2mngr_q.enq.msg,

      # stats output

      stats_en = s.stats_en,
    )

    # Ctrl <-> Dpath

    # s.connect_auto( s.ctrl, s.dpath )
    connect_pairs(
      s.ctrl.reg_en_F       , s.dpath.reg_en_F,
      s.ctrl.pc_sel_F       , s.dpath.pc_sel_F,
      s.ctrl.reg_en_D       , s.dpath.reg_en_D,
      s.ctrl.op1_byp_sel_D  , s.dpath.op1_byp_sel_D,
      s.ctrl.op2_byp_sel_D  , s.dpath.op2_byp_sel_D,
      s.ctrl.op1_sel_D      , s.dpath.op1_sel_D,
      s.ctrl.op2_sel_D      , s.dpath.op2_sel_D,
      s.ctrl.csrr_sel_D     , s.dpath.csrr_sel_D,
      s.ctrl.imm_type_D     , s.dpath.imm_type_D,
      s.ctrl.imul_req_val_D , s.dpath.imul_req_val_D,
      s.ctrl.imul_req_rdy_D , s.dpath.imul_req_rdy_D,
      s.ctrl.reg_en_X       , s.dpath.reg_en_X,
      s.ctrl.alu_fn_X       , s.dpath.alu_fn_X,
      s.ctrl.ex_result_sel_X, s.dpath.ex_result_sel_X,
      s.ctrl.imul_resp_rdy_X, s.dpath.imul_resp_rdy_X,
      s.ctrl.imul_resp_val_X, s.dpath.imul_resp_val_X,
      s.ctrl.reg_en_M       , s.dpath.reg_en_M,
      s.ctrl.wb_result_sel_M, s.dpath.wb_result_sel_M,
      s.ctrl.reg_en_W       , s.dpath.reg_en_W,
      s.ctrl.rf_waddr_W     , s.dpath.rf_waddr_W,
      s.ctrl.rf_wen_W       , s.dpath.rf_wen_W,
      s.ctrl.stats_en_wen_W , s.dpath.stats_en_wen_W,

      s.dpath.inst_D       , s.ctrl.inst_D,
      s.dpath.br_cond_eq_X , s.ctrl.br_cond_eq_X,
      s.dpath.br_cond_lt_X , s.ctrl.br_cond_lt_X,
      s.dpath.br_cond_ltu_X, s.ctrl.br_cond_ltu_X,
    )

  #-----------------------------------------------------------------------
  # Line tracing
  #-----------------------------------------------------------------------

  def line_trace( s ):
    # F stage

    if not s.ctrl.val_F:
      F_str = "{:<8s}".format( ' ' )
    elif s.ctrl.squash_F:
      F_str = "{:<8s}".format( '~' )
    elif s.ctrl.stall_F:
      F_str = "{:<8s}".format( '#' )
    else:
      F_str = "{:08x}".format( s.dpath.pc_reg_F.out.uint() )

    # D stage

    if not s.ctrl.val_D:
      D_str = "{:<23s}".format( ' ' )
    elif s.ctrl.squash_D:
      D_str = "{:<23s}".format( '~' )
    elif s.ctrl.stall_D:
      D_str = "{:<23s}".format( '#' )
    else:
      D_str = "{:<23s}".format( disassemble_inst(s.ctrl.inst_D) )

    # X stage

    if not s.ctrl.val_X:
      X_str = "{:<5s}".format( ' ' )
    elif s.ctrl.stall_X:
      X_str = "{:<5s}".format( '#' )
    else:
      X_str = "{:<5s}".format( inst_dict[s.ctrl.inst_type_X.uint()] )

    # M stage

    if not s.ctrl.val_M:
      M_str = "{:<5s}".format( ' ' )
    elif s.ctrl.stall_M:
      M_str = "{:<5s}".format( '#' )
    else:
      M_str = "{:<5s}".format( inst_dict[s.ctrl.inst_type_M.uint()] )

    # W stage

    if not s.ctrl.val_W:
      W_str = "{:<5s}".format( ' ' )
    elif s.ctrl.stall_W:
      W_str = "{:<5s}".format( '#' )
    else:
      W_str = "{:<5s}".format( inst_dict[s.ctrl.inst_type_W.uint()] )

    pipeline_str = ( F_str + "|" + D_str + "|" + X_str + "|" + M_str + "|" + W_str )

    return pipeline_str

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
