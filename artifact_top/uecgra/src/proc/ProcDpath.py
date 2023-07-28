#=========================================================================
# ProcDpath.py
#=========================================================================

from pymtl3      import *
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.rtl  import RegisterFile, Mux, RegEnRst, RegEn
from pymtl3.stdlib.rtl  import Adder, Incrementer
from pymtl3.stdlib.ifcs import InValRdyIfc, OutValRdyIfc

from imul.IntMul  import IntMul
from proc.ProcDpathComponentsPRTL import AluPRTL, ImmGenPRTL
from proc.TinyRV2InstPRTL         import OPCODE, RS1, RS2, RD, SHAMT

#-------------------------------------------------------------------------
# Constants
#-------------------------------------------------------------------------

c_reset_vector = 0x200
c_reset_inst   = 0

#-------------------------------------------------------------------------
# ProcDpath
#-------------------------------------------------------------------------

class ProcDpath( Component ):

  def construct( s, num_cores = 1, mul_mode = 'varlat' ):

    dtype = mk_bits(32) # All dpath components are 32-bit wide

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # Parameters

    s.core_id = InPort( dtype )

    # imem ports

    s.imemreq_msg       = OutPort( Bits77 )
    s.imemresp_msg_data = InPort ( dtype )

    # dmem ports

    s.dmemreq_msg_addr  = OutPort( dtype )
    s.dmemreq_msg_data  = OutPort( dtype )
    s.dmemresp_msg_data = InPort ( dtype )

    # mngr ports

    s.mngr2proc_data    = InPort ( dtype )
    s.proc2mngr_data    = OutPort( dtype )

    # Control signals (ctrl->dpath)

    s.reg_en_F          = InPort ( Bits1 )
    s.pc_sel_F          = InPort ( Bits2 )

    s.reg_en_D          = InPort ( Bits1 )
    s.op1_byp_sel_D     = InPort ( Bits2 )
    s.op2_byp_sel_D     = InPort ( Bits2 )
    s.op1_sel_D         = InPort ( Bits1 )
    s.op2_sel_D         = InPort ( Bits2 )
    s.csrr_sel_D        = InPort ( Bits2 )
    s.imm_type_D        = InPort ( Bits3 )
    s.imul_req_val_D    = InPort ( Bits1 )
    s.imul_req_rdy_D    = OutPort( Bits1 )

    s.reg_en_X          = InPort ( Bits1 )
    s.alu_fn_X          = InPort ( Bits4 )
    s.ex_result_sel_X   = InPort ( Bits2 )
    s.imul_resp_rdy_X   = InPort ( Bits1 )
    s.imul_resp_val_X   = OutPort( Bits1 )

    s.reg_en_M          = InPort ( Bits1 )
    s.wb_result_sel_M   = InPort ( Bits1 )

    s.reg_en_W          = InPort ( Bits1 )
    s.rf_waddr_W        = InPort ( Bits5 )
    s.rf_wen_W          = InPort ( Bits1 )
    s.stats_en_wen_W    = InPort ( Bits1 )

    # Status signals (dpath->Ctrl)

    s.inst_D            = OutPort( dtype )
    s.br_cond_eq_X      = OutPort( Bits1 )
    s.br_cond_lt_X      = OutPort( Bits1 )
    s.br_cond_ltu_X     = OutPort( Bits1 )

    # stats_en output

    s.stats_en          = OutPort( Bits1 )

    #---------------------------------------------------------------------
    # F stage
    #---------------------------------------------------------------------

    s.pc_F        = Wire( dtype )
    s.pc_plus4_F  = Wire( dtype )

    # PC+4 incrementer

    s.pc_incr_F = Incrementer( dtype, amount=4 )(
      in_ = s.pc_F,
      out = s.pc_plus4_F,
    )

    # forward delaration for branch target and jal target

    s.br_target_X  = Wire( dtype )
    s.jal_target_D = Wire( dtype )
    s.jalr_target_X = Wire( dtype )

    # PC sel mux

    s.pc_sel_mux_F = Mux( dtype, 4 )(
      in_ = { 0: s.pc_plus4_F,
              1: s.br_target_X,
              2: s.jal_target_D,
              3: s.jalr_target_X, },
      sel = s.pc_sel_F,
      out = s.imemreq_msg[11:43],
    )

    # PC register

    s.pc_reg_F = RegEnRst( dtype, reset_value=c_reset_vector-4 )(
      en  = s.reg_en_F,
      in_ = s.pc_sel_mux_F.out,
      out = s.pc_F,
    )

    #---------------------------------------------------------------------
    # D stage
    #---------------------------------------------------------------------

    # PC reg in D stage
    # This value is basically passed from F stage for the corresponding
    # instruction to use, e.g. branch to (PC+imm)

    s.pc_reg_D = m = RegEnRst( dtype )( en = s.reg_en_D, in_ = s.pc_F )

    # Instruction reg

    s.inst_D_reg = m = RegEnRst( dtype, reset_value=c_reset_inst )(
      en  = s.reg_en_D,
      in_ = s.imemresp_msg_data,
      out = s.inst_D                  # to ctrl
    )

    # Register File
    # The rf_rdata_D wires, albeit redundant in some sense, are used to
    # remind people these data are from D stage.

    s.rf_rdata0_D = Wire( dtype )
    s.rf_rdata1_D = Wire( dtype )

    s.rf_wdata_W  = Wire( dtype )

    s.rf = RegisterFile( dtype, nregs=32, rd_ports=2, wr_ports=1, const_zero=True )(
      raddr = { 0: s.inst_D[ RS1 ],
                1: s.inst_D[ RS2 ], },
      rdata = { 0: s.rf_rdata0_D,
                1: s.rf_rdata1_D, },
      wen   = { 0: s.rf_wen_W },
      waddr = { 0: s.rf_waddr_W },
      wdata = { 0: s.rf_wdata_W },
    )

    # Immediate generator

    s.imm_gen_D = ImmGenPRTL()(
      imm_type = s.imm_type_D,
      inst     = s.inst_D,
    )

    s.byp_data_X = Wire( dtype )
    s.byp_data_M = Wire( dtype )
    s.byp_data_W = Wire( dtype )

    # op1 bypass mux

    s.op1_byp_mux_D = Mux( dtype, 4 )(
      in_ = { 0: s.rf_rdata0_D,
              1: s.byp_data_X,
              2: s.byp_data_M,
              3: s.byp_data_W, },
      sel = s.op1_byp_sel_D,
    )

    # op2 bypass mux

    s.op2_byp_mux_D = Mux( dtype, 4 )(
      in_ = { 0: s.rf_rdata1_D,
              1: s.byp_data_X,
              2: s.byp_data_M,
              3: s.byp_data_W, },
      sel = s.op2_byp_sel_D,
    )

    # op1 sel mux

    s.op1_sel_mux_D = Mux( dtype, 2 )(
      in_ = { 0: s.op1_byp_mux_D.out,
              1: s.pc_reg_D.out, },
      sel = s.op1_sel_D,
    )

    # csrr sel mux

    s.csrr_sel_mux_D = Mux( dtype, 3 )(
      in_ = { 0: s.mngr2proc_data,
              2: s.core_id, },
      sel = s.csrr_sel_D,
    )

    s.csrr_sel_mux_D.in_[1] //= num_cores

    # op2 sel mux
    # This mux chooses among RS2, imm, and the output of the above csrr
    # sel mux. Basically we are using two muxes here for pedagogy.

    s.op2_sel_mux_D = Mux( dtype, 3 )(
      in_ = { 0: s.op2_byp_mux_D.out,
              1: s.imm_gen_D.imm,
              2: s.csrr_sel_mux_D.out, },
      sel = s.op2_sel_D,
    )

    # Risc-V always calcs branch/jal target by adding imm(generated above) to PC

    s.pc_plus_imm_D = Adder( dtype )(
      in0 = s.pc_reg_D.out,
      in1 = s.imm_gen_D.imm,
      out = s.jal_target_D,
    )

    #---------------------------------------------------------------------
    # X stage
    #---------------------------------------------------------------------

    # imul
    # Since on the datapath diagram it's slightly left to those registers,
    # I put it at the beginning of the X stage :)

    s.imul = m = IntMul(32, mul_mode)
    connect_pairs(
      m.req.val,        s.imul_req_val_D,
      m.req.rdy,        s.imul_req_rdy_D,
      m.req.msg[32:64], s.op1_sel_mux_D.out,
      m.req.msg[0:32],  s.op2_sel_mux_D.out,
      m.resp.val,       s.imul_resp_val_X,
      m.resp.rdy,       s.imul_resp_rdy_X,
    )

    # br_target_reg_X
    # Since branches are resolved in X stage, we register the target,
    # which is already calculated in D stage, to X stage.

    s.br_target_reg_X = RegEnRst( dtype, reset_value=0 )(
      en  = s.reg_en_X,
      in_ = s.pc_plus_imm_D.out,
      out = s.br_target_X,
    )

    # PC reg in X stage

    s.pc_reg_X = RegEnRst( dtype )(
      en  = s.reg_en_X,
      in_ = s.pc_reg_D.out,
    )

    # op1 reg

    s.op1_reg_X = RegEnRst( dtype, reset_value=0 )(
      en  = s.reg_en_X,
      in_ = s.op1_sel_mux_D.out,
    )

    # op2 reg

    s.op2_reg_X = m = RegEnRst( dtype, reset_value=0 )(
      en  = s.reg_en_X,
      in_ = s.op2_sel_mux_D.out,
    )

    # dmemreq write data reg
    # Since the op1 is the base address and op2 is the immediate so that
    # we could utilize ALU to do address calculation, we need one more
    # register to hold the R[rs2] we want to store to memory.

    s.dmem_write_data_reg_X = RegEnRst( dtype, reset_value=0 )(
      en  = s.reg_en_X,
      in_ = s.op2_byp_mux_D.out, # R[rs2]
      out = s.dmemreq_msg_data,
    )

    # ALU

    s.alu_X = AluPRTL()(
      in0     = s.op1_reg_X.out,
      in1     = s.op2_reg_X.out,
      fn      = s.alu_fn_X,
      ops_eq  = s.br_cond_eq_X,
      ops_lt  = s.br_cond_lt_X,
      ops_ltu = s.br_cond_ltu_X,
      out     = s.jalr_target_X,
    )

    # PC+4 generator

    s.pc_incr_X = Incrementer( dtype, amount=4 )( in_ = s.pc_reg_X.out )

    # X result sel mux

    s.ex_result_sel_mux_X = Mux( dtype, 3 )(
      in_ = { 0: s.alu_X.out,
              1: s.imul.resp.msg,
              2: s.pc_incr_X.out, },
      sel = s.ex_result_sel_X,
      out = ( s.byp_data_X, s.dmemreq_msg_addr ), # fan-out
    )

    #---------------------------------------------------------------------
    # M stage
    #---------------------------------------------------------------------

    # Alu execution result reg

    s.ex_result_reg_M = m = RegEnRst( dtype, reset_value=0 )(
      en  = s.reg_en_M,
      in_ = s.ex_result_sel_mux_X.out
    )

    # Writeback result selection mux

    s.wb_result_sel_mux_M = Mux( dtype, 2 )(
      in_ = { 0: s.ex_result_reg_M.out,
              1: s.dmemresp_msg_data, },
      sel = s.wb_result_sel_M,
      out = s.byp_data_M,
    )

    #---------------------------------------------------------------------
    # W stage
    #---------------------------------------------------------------------

    # Writeback result reg

    s.wb_result_reg_W = RegEnRst( dtype, reset_value=0 )(
      en  = s.reg_en_W,
      in_ = s.wb_result_sel_mux_M.out,
      out = ( s.byp_data_W, s.rf_wdata_W, s.proc2mngr_data ),
    )

    # stats_en

    s.stats_en_reg_W = RegEnRst( dtype, reset_value=0 )(
      en  = s.stats_en_wen_W,
      in_ = s.wb_result_reg_W.out,
    )
    s.stats_en_reg_W.out[0] //= s.stats_en
