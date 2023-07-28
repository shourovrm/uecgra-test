//========================================================================
// mul
//========================================================================
// Multiplier with val/rdy protocol for input and output
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
// Author : Christopher Torng
// Date   : July 18, 2019
//

module mul #(
  parameter p_width   = 4,
  parameter p_ncycles = 3,
  // Do not set these from outside!
  parameter p_ncycles_width = $clog2( p_ncycles + 1 ) // plus one for INIT
)(
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

  assign req_go  = req_val  & req_rdy;
  assign resp_go = resp_val & resp_rdy;

  // State

  localparam INIT  = '0;
  localparam START = 1'b1;
  localparam DONE  = p_ncycles;

  logic [p_ncycles_width-1:0] state;
  logic [p_ncycles_width-1:0] next_state;

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

  // Control signals -- Datapath

  logic msg_reg_en;

  assign msg_reg_en = req_go;

  // Control signals -- Handshake

  assign req_rdy  = ( state == INIT ) | ( ( state == DONE ) & resp_go );
  assign resp_val = ( state == DONE );

  //----------------------------------------------------------------------
  // Datapath
  //----------------------------------------------------------------------

  // Input register for the input message

  logic [2*p_width-1:0] msg_reg;

  always @ ( posedge clk ) begin
    if ( reset ) begin
      msg_reg <= '0;
    end
    else if ( msg_reg_en ) begin
      msg_reg <= req_msg;
    end
  end

  // Multiplier

  logic [p_width-1:0] a;
  logic [p_width-1:0] b;

  assign a = msg_reg[p_width-1:0];
  assign b = msg_reg[2*p_width-1:p_width];

  logic [2*p_width-1:0] product;

  assign product = a * b;

  // Response message

  assign resp_msg = product;

endmodule

