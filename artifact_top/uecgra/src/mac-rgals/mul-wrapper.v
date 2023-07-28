//========================================================================
// mul_wrapper
//========================================================================
// Wraps mul with rgals circuitry
//
// Author : Christopher Torng, Yanghui Ou
// Date   : July 22, 2019
//

module mul_wrapper #(
  parameter p_width   = 4,
  parameter p_ncycles = 3
)(
  input  logic                 clk_m,
  input  logic                 clk1,
  input  logic                 clk2,
  input  logic                 clk_reset,
  input  logic                 clksel_val,
  output logic                 clksel_rdy,
  input  logic                 clksel_msg,
  output logic                 clk_out,
  input  logic                 reset,
  input  logic                 req_val,
  output logic                 req_rdy,
  input  logic [2*p_width-1:0] req_msg,
  output logic                 resp_val,
  input  logic                 resp_rdy,
  output logic [2*p_width-1:0] resp_msg
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

  mul #(
    .p_width   ( p_width   ),
    .p_ncycles ( p_ncycles )
  ) mul1 (
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

