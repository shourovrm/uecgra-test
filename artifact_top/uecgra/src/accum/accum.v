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
// Author : Christopher Torng
// Date   : July 18, 2019
//

module accum #(
  parameter p_width = 4,
  parameter p_nmsgs = 4,
  // Do not set these from outside!
  parameter p_nmsgs_width = $clog2( p_nmsgs + 1 ) // plus one for INIT
)(
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

  assign req_go  = req_val  & req_rdy;
  assign resp_go = resp_val & resp_rdy;

  // State

  localparam INIT  = '0;
  localparam START = 1'b1;
  localparam DONE  = p_nmsgs;

  logic [p_nmsgs_width-1:0] state;
  logic [p_nmsgs_width-1:0] next_state;

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
  logic accum_en;
  logic msg_reg_en;

  assign accum_clear = resp_go;
  assign msg_reg_en  = req_go;

  always @ ( posedge clk ) begin
    if ( reset ) begin
      accum_en <= '0;
    end
    else begin
      accum_en <= req_go;
    end
  end

  // Control signals -- Handshake

  assign req_rdy  = !( ( state == DONE ) & !resp_rdy );
  assign resp_val = ( state == DONE );

  //----------------------------------------------------------------------
  // Datapath
  //----------------------------------------------------------------------

  // Input register for the input message

  logic [p_width-1:0] msg_reg;

  always @ ( posedge clk ) begin
    if ( reset ) begin
      msg_reg <= '0;
    end
    else if ( msg_reg_en ) begin
      msg_reg <= req_msg;
    end
  end

  // Sum and accumulation register

  logic [p_width-1:0] sum;
  logic [p_width-1:0] accum;

  assign sum = msg_reg + accum;

  always @ ( posedge clk ) begin
    if ( reset ) begin
      accum <= '0;
    end
    else if ( accum_clear ) begin
      accum <= '0;
    end
    else if ( accum_en ) begin
      accum <= sum;
    end
  end

  // Response message

  assign resp_msg = sum;

endmodule


