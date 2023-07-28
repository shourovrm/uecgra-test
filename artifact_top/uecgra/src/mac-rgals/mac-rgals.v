//========================================================================
// mac_rgals
//========================================================================
// Multiply-accumulator with val/rdy protocol for input and output.
//
// Note:
//   [clk] is the external main clock.
//   [clk1] is the internal clock for mul.
//   [clk2] is the internal clock for accum.
//
// Author : Christopher Torng
// Date   : July 18, 2019
//

module mac_rgals #(
  parameter p_width = 8
)(
  input  logic                 clk,
  input  logic                 clk_reset,
  input  logic                 mul_clksel_val,
  output logic                 mul_clksel_rdy,
  input  logic                 mul_clksel_msg,
  input  logic                 accum_clksel_val,
  output logic                 accum_clksel_rdy,
  input  logic                 accum_clksel_msg,
  input  logic                 reset,
  input  logic                 req_val,
  output logic                 req_rdy,
  input  logic [2*p_width-1:0] req_msg,
  output logic                 resp_val,
  input  logic                 resp_rdy,
  output logic   [p_width-1:0] resp_msg
);

  //----------------------------------------------------------------------
  // Clock dividers
  //----------------------------------------------------------------------

  localparam p_clk1_div = 3;
  localparam p_clk2_div = 5;

  wire clk1;
  wire clk2;

  ClockDivider #( p_clk1_div ) clk_div_1 (
    .clk         ( clk       ),
    .clk_reset   ( clk_reset ),
    .clk_divided ( clk1      )
  );

  ClockDivider #( p_clk2_div ) clk_div_2 (
    .clk         ( clk       ),
    .clk_reset   ( clk_reset ),
    .clk_divided ( clk2      )
  );

  //----------------------------------------------------------------------
  // Multiplier
  //----------------------------------------------------------------------

  logic                 mul_clk_out;

  // logic                 mulreq_val;
  // logic                 mulreq_rdy;
  // logic [2*p_width-1:0] mulreq_msg;

  logic                 mulresp_val;
  logic                 mulresp_rdy;
  logic [2*p_width-1:0] mulresp_msg;

  // Clock Domain Crossing

  // BisynchronousNormalQueue #(
  //   .p_data_width  ( 2*p_width ),
  //   .p_num_entries ( 2         )
  // ) fifo_src (
  //   .w_clk ( clk         ),
  //   .r_clk ( mul_clk_out ),
  //   .reset ( reset       ),
  //   .w_val ( req_val     ),
  //   .w_rdy ( req_rdy     ),
  //   .w_msg ( req_msg     ),
  //   .r_val ( mulreq_val  ),
  //   .r_rdy ( mulreq_rdy  ),
  //   .r_msg ( mulreq_msg  )
  // );

  // Mul

  mul_wrapper #(
    .p_width    ( p_width ),
    .p_ncycles  ( 3       )
  ) mul1 (
    .clk_m      ( clk            ),
    .clk1       ( clk1           ),
    .clk2       ( clk2           ),
    .clk_reset  ( clk_reset      ),
    .clksel_val ( mul_clksel_val ),
    .clksel_rdy ( mul_clksel_rdy ),
    .clksel_msg ( mul_clksel_msg ),
    .clk_out    ( mul_clk_out    ),
    .reset      ( reset          ),
    .req_val    ( req_val        ),
    .req_rdy    ( req_rdy        ),
    .req_msg    ( req_msg        ),
    .resp_val   ( mulresp_val    ),
    .resp_rdy   ( mulresp_rdy    ),
    .resp_msg   ( mulresp_msg    )
  );

  logic [p_width-1:0] mulresp_msg_trunc;

  assign mulresp_msg_trunc = mulresp_msg[p_width-1:0];

  //----------------------------------------------------------------------
  // Accumulator
  //----------------------------------------------------------------------

  logic               accum_clk_out;

  // logic               accumreq_val;
  // logic               accumreq_rdy;
  // logic [p_width-1:0] accumreq_msg;

  logic               accumresp_val;
  logic               accumresp_rdy;
  logic [p_width-1:0] accumresp_msg;

  // Clock Domain Crossing

  // BisynchronousNormalQueue #(
  //   .p_data_width  ( p_width ),
  //   .p_num_entries ( 2       )
  // ) fifo (
  //   .w_clk ( mul_clk_out   ),
  //   .r_clk ( accum_clk_out ),
  //   .reset ( reset         ),
  //   .w_val ( mulresp_val   ),
  //   .w_rdy ( mulresp_rdy   ),
  //   .w_msg ( mulresp_msg_trunc ),
  //   .r_val ( accumreq_val  ),
  //   .r_rdy ( accumreq_rdy  ),
  //   .r_msg ( accumreq_msg  )
  // );

  // Accumulator + Clock Switcher

  accum_wrapper #(
    .p_width    ( p_width ),
    .p_nmsgs    ( 4       )
  ) accum1 (
    .clk_m      ( mul_clk_out       ),
    .clk1       ( clk1              ),
    .clk2       ( clk2              ),
    .clk_reset  ( clk_reset         ),
    .clksel_val ( accum_clksel_val  ),
    .clksel_rdy ( accum_clksel_rdy  ),
    .clksel_msg ( accum_clksel_msg  ),
    .clk_out    ( accum_clk_out     ),
    .reset      ( reset             ),
    .req_val    ( mulresp_val       ),
    .req_rdy    ( mulresp_rdy       ),
    .req_msg    ( mulresp_msg_trunc ),
    .resp_val   ( accumresp_val     ),
    .resp_rdy   ( accumresp_rdy     ),
    .resp_msg   ( accumresp_msg     )
  );

  // Clock Domain Crossing

  BisynchronousNormalQueue #(
    .p_data_width  ( p_width ),
    .p_num_entries ( 2       )
  ) fifo_sink (
    .w_clk ( accum_clk_out ),
    .r_clk ( clk           ),
    .reset ( reset         ),
    .w_val ( accumresp_val ),
    .w_rdy ( accumresp_rdy ),
    .w_msg ( accumresp_msg ),
    .r_val ( resp_val      ),
    .r_rdy ( resp_rdy      ),
    .r_msg ( resp_msg      )
  );

endmodule
