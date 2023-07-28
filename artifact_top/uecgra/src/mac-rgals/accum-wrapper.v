//========================================================================
// accum_wrapper
//========================================================================
// Wraps accum with rgals circuitry
//
// Author : Christopher Torng
// Date   : July 22, 2019
//

module accum_wrapper #(
  parameter p_width = 4,
  parameter p_nmsgs = 4
)(
  input  logic               clk_m,
  input  logic               clk1,
  input  logic               clk2,
  input  logic               clk_reset,
  input  logic               clksel_val,
  output logic               clksel_rdy,
  input  logic               clksel_msg,
  output logic               clk_out,
  input  logic               reset,
  input  logic               req_val,
  output logic               req_rdy,
  input  logic [p_width-1:0] req_msg,
  output logic               resp_val,
  input  logic               resp_rdy,
  output logic [p_width-1:0] resp_msg
);

  ClockSwitcher clkswitcher (
    .clk1       ( clk1       ),
    .clk2       ( clk2       ),
    .clk_reset  ( clk_reset  ),
    .switch_val ( clksel_val ),
    .switch_rdy ( clksel_rdy ),
    .switch_msg ( clksel_msg ),
    .clk_out    ( clk_out    )
  );

  accum #(
    .p_width  ( p_width  ),
    .p_nmsgs  ( p_nmsgs  )
  ) accum1 (
    .clk_m    ( clk_m    ),
    .clk      ( clk_out  ),
    .reset    ( reset    ),
    .req_val  ( req_val  ),
    .req_rdy  ( req_rdy  ),
    .req_msg  ( req_msg  ),
    .resp_val ( resp_val ),
    .resp_rdy ( resp_rdy ),
    .resp_msg ( resp_msg )
  );

endmodule

