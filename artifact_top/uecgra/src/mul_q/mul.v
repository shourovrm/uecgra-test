//========================================================================
// mul.v
//========================================================================
// Multiplier with val/rdy protocol for input and output, and a
// bisynchronous normal queue as input buffer.
//
// Notes:
//
// - Width parameter. The p_width parameter is the bitwidth of a single
//   operand. The input packs two operands together, so req_msg is
//   2*p_width. The output is also 2*p_width (no truncation).
//
// - This is an N-cycle occupancy multiply operator, and the design is
//   input registered.
//
// - [clk_m] stands for master clock. It is the clock of the master who
//   sends requests to mul.
//
// Author : Christopher Torng, Yanghui Ou
// Date   : July 18, 2019
//

module mul #(
  parameter p_width   = 4,
  parameter p_ncycles = 3,
  // Derived parameters. Do not set these from outside!
  parameter c_ncycles_width = $clog2( p_ncycles + 1 ) // plus one for INIT
)(
  input  logic                 clk_m,
  input  logic                 clk,
  input  logic                 reset,
  input  logic                 req_val,
  output logic                 req_rdy,
  input  logic [2*p_width-1:0] req_msg,
  output logic                 resp_val,
  input  logic                 resp_rdy,
  output logic [2*p_width-1:0] resp_msg
);

  //----------------------------------------------------------------------
  // Control
  //----------------------------------------------------------------------
  // This is an N-cycle occupancy multiply operator. The block is
  // input-registered, so computation begins after the edge the request is
  // received on.

  logic req_go;
  logic resp_go;
  logic q_val;
  logic q_rdy;
  logic [2*p_width-1:0] q_msg;

  assign req_go  = q_val;
  assign resp_go = resp_val & resp_rdy;

  // State

  localparam INIT  = 'd0;
  localparam START = 1'b1;
  localparam DONE  = p_ncycles;

  logic [c_ncycles_width-1:0] state;
  logic [c_ncycles_width-1:0] next_state;

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
      next_state = state + 1'b1;
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

  // Control signals -- Handshake

  assign resp_val = ( state == DONE );
  assign q_rdy  = ( ( state == DONE ) & resp_go );

  //----------------------------------------------------------------------
  // Datapath
  //----------------------------------------------------------------------

  // BisynchronousNormalQueue as input buffer

  BisynchronousNormalQueue #(
    .p_data_width ( p_width*2 ),
    .p_num_entries( 2         )
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

  // Multiplier

  logic [p_width-1:0] a;
  logic [p_width-1:0] b;

  assign a = q_msg[p_width-1:0];
  assign b = q_msg[2*p_width-1:p_width];

  logic [2*p_width-1:0] product;

  assign product = a * b;

  // Response message

  assign resp_msg = product;

endmodule

