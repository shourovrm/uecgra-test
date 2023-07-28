//========================================================================
// mac
//========================================================================
// Multiply-accumulator with val/rdy protocol for input and output
//
// Author : Christopher Torng
// Date   : July 18, 2019
//

module mac #(
  parameter p_width = 8
)(
  input  logic                 clk,
  input  logic                 reset,
  input  logic                 req_val,
  output logic                 req_rdy,
  input  logic [2*p_width-1:0] req_msg,
  output logic                 resp_val,
  input  logic                 resp_rdy,
  output logic   [p_width-1:0] resp_msg
);

   logic                 accumreq_val;
   logic                 accumreq_rdy;
   logic [2*p_width-1:0] accumreq_msg;

  // Multiplier

  mul #(
    .p_width   ( p_width ),
    .p_ncycles ( 3       )
  ) mul1 (
    .clk      ( clk          ),
    .reset    ( reset        ),
    .req_val  ( req_val      ),
    .req_rdy  ( req_rdy      ),
    .req_msg  ( req_msg      ),
    .resp_val ( accumreq_val ),
    .resp_rdy ( accumreq_rdy ),
    .resp_msg ( accumreq_msg )
  );

  // Accumulator

  logic [p_width-1:0] accumreq_msg_trunc;

  assign accumreq_msg_trunc = accumreq_msg[p_width-1:0];

  accum #(
    .p_width  ( p_width ),
    .p_nmsgs  ( 4       )
  ) accum1 (
    .clk      ( clk          ),
    .reset    ( reset        ),
    .req_val  ( accumreq_val ),
    .req_rdy  ( accumreq_rdy ),
    .req_msg  ( accumreq_msg_trunc ),
    .resp_val ( resp_val     ),
    .resp_rdy ( resp_rdy     ),
    .resp_msg ( resp_msg     )
  );

endmodule

