//========================================================================
// accum
//========================================================================
// Accumulator with val/rdy protocol
//
// Notes:
//
// - Accumulates sets of "p_nmsgs" messages. For example, if "p_nmsgs=4",
//   then every four request handshakes will have one response handshake
//   with the accumulation of the past four messages.
//
// Author : Christopher Torng, Yanghui Ou
// Date   : July 18, 2019
//

module accum #(
  parameter p_width = 4,
  parameter p_nmsgs = 4,
  // Derived paramters. Do not set these from outside!
  parameter c_nmsgs_width = $clog2( p_nmsgs + 1 ) // plus one for INIT
)(
  input  logic               clk_m,
  input  logic               clk,
  input  logic               reset,
  input  logic               req_val,
  output logic               req_rdy,
  input  logic [p_width-1:0] req_msg,
  output logic               resp_val,
  input  logic               resp_rdy,
  output logic [p_width-1:0] resp_msg
);

  //----------------------------------------------------------------------
  // Control
  //----------------------------------------------------------------------
  // This block accumulates over "p_nmsgs" transactions.

  logic req_go;
  logic resp_go;
  logic q_val;
  logic q_rdy;
  logic [p_width-1:0] q_msg;

  assign req_go  = q_val & q_rdy;
  assign resp_go = resp_val & resp_rdy;

  // State

  localparam INIT  = 'd0;
  localparam START = 1'b1;
  localparam DONE  = p_nmsgs;

  logic [c_nmsgs_width-1:0] state;
  logic [c_nmsgs_width-1:0] next_state;

  always @ ( posedge clk ) begin
    if ( reset ) begin
      state <= INIT;
    end
    else begin
      state <= next_state;
    end
  end

  // Next state

  always @ ( * ) begin
    next_state = INIT;
    // INIT -- Request handshake -> move to START
    if ( state == INIT ) begin
      next_state = INIT;
      if ( req_go ) begin
        next_state = START;
      end
    end
    // If not done, tick away until done
    else if ( state != DONE ) begin
      next_state = state;
      if ( req_go ) begin
        next_state = state + 1'b1;
      end
    end
    // DONE -- Response handshake -> move to INIT
    else if ( state == DONE ) begin
      next_state = DONE;
      if ( resp_go ) begin
        next_state = INIT;
        // Pipeline behavior
        if ( req_go ) begin
          next_state = START;
        end
      end
    end
  end

  // Control signals -- Datapath

  logic accum_clear;
  logic accum_clear_bypass;
  logic accum_en;

  assign accum_clear = resp_go & ~req_go;
  assign accum_clear_bypass = resp_go & req_go;
  assign accum_en = q_val & q_rdy;

  // always @ ( posedge clk ) begin
  //   if ( reset ) begin
  //     accum_en <= 'd0;
  //   end
  //   else begin
  //     accum_en <= req_go;
  //   end
  // end

  assign resp_val = ( state == DONE );
  assign q_rdy = ( state == INIT ) ? req_val :
                 ( state == DONE ) ? resp_go : 1'b1;

  //----------------------------------------------------------------------
  // Datapath
  //----------------------------------------------------------------------

  // BisynchronousNormalQueue as input buffer

  BisynchronousNormalQueue #(
    .p_data_width ( p_width ),
    .p_num_entries( 2       )
  ) in_q (
    .w_clk( clk_m   ),
    .r_clk( clk     ),
    .reset( reset   ),
    .w_val( req_val ),
    .w_rdy( req_rdy ),
    .w_msg( req_msg ),
    .r_val( q_val   ),
    .r_rdy( q_rdy   ),
    .r_msg( q_msg   )
  );

  // Sum and accumulation register

  logic [p_width-1:0] sum;
  logic [p_width-1:0] accum;

  assign sum = q_msg + accum;

  always @ ( posedge clk ) begin
    if ( reset ) begin
      accum <= 'd0;
    end
    else if ( accum_clear_bypass ) begin
      accum <= q_msg;
    end
    else if ( accum_clear ) begin
      accum <= 'd0;
    end
    else if ( accum_en ) begin
      accum <= sum;
    end
  end

  // Response message

  assign resp_msg = accum;

endmodule


