//------------------------------------------------------------------------
// mac.t.v
//------------------------------------------------------------------------
// Smoke test
//
// Author : Christopher Torng
// Date   : July 18, 2019
//

`timescale 1ns/1ps

`ifndef CLOCK_PERIOD
  `define CLOCK_PERIOD 2.0
`endif

module th;

  // Number of each type of test

  localparam p_ndirected = 4;
  localparam p_nrandom   = 100;

  //----------------------------------------------------------------------
  // Setup
  //----------------------------------------------------------------------

  // Clock and reset

  logic clk_reset = 1'b1;
  logic reset     = 1'b1;
  logic clk       = 1'b1;

  always #(`CLOCK_PERIOD/2.0) clk = ~clk;

  initial
    $display( "Simulating with clock period: %f", `CLOCK_PERIOD );

  //----------------------------------------------------------------------
  // Instantiate
  //----------------------------------------------------------------------

  // Source

  logic        src_val;
  logic        src_rdy;
  logic [31:0] src_msg;
  logic        src_done;

  Source #(
    .p_width ( 32 ),
    .p_nmsgs ( 4*p_ndirected + 4*p_nrandom )
  ) src (
    .clk   ( clk      ),
    .reset ( reset    ),
    .val   ( src_val  ),
    .rdy   ( src_rdy  ),
    .msg   ( src_msg  ),
    .done  ( src_done )
  );

  // Sink

  logic        sink_val;
  logic        sink_rdy;
  logic [15:0] sink_msg;
  logic        sink_done;

  Sink #(
    .p_width ( 16 ),
    .p_nmsgs ( p_ndirected + p_nrandom )
  ) sink (
    .clk   ( clk       ),
    .reset ( reset     ),
    .val   ( sink_val  ),
    .rdy   ( sink_rdy  ),
    .msg   ( sink_msg  ),
    .done  ( sink_done )
  );

  // Design

  logic mul_clksel_val;
  logic mul_clksel_rdy;
  logic mul_clksel_msg;
  logic accum_clksel_val;
  logic accum_clksel_rdy;
  logic accum_clksel_msg;

  mac_rgals #(
    .p_width  ( 16 )
  ) dut (
    .clk              ( clk              ),
    .clk_reset        ( clk_reset        ),
    .mul_clksel_val   ( mul_clksel_val   ),
    .mul_clksel_rdy   ( mul_clksel_rdy   ),
    .mul_clksel_msg   ( mul_clksel_msg   ),
    .accum_clksel_val ( accum_clksel_val ),
    .accum_clksel_rdy ( accum_clksel_rdy ),
    .accum_clksel_msg ( accum_clksel_msg ),
    .reset            ( reset            ),
    .req_val          ( src_val          ),
    .req_rdy          ( src_rdy          ),
    .req_msg          ( src_msg          ),
    .resp_val         ( sink_val         ),
    .resp_rdy         ( sink_rdy         ),
    .resp_msg         ( sink_msg         )
  );

  //----------------------------------------------------------------------
  // Test vectors
  //----------------------------------------------------------------------

  // Helper task to load the source and sink memories

  task load;
    input [31:0] i;
    input [15:0] x0_a;
    input [15:0] x0_b;
    input [15:0] x1_a;
    input [15:0] x1_b;
    input [15:0] x2_a;
    input [15:0] x2_b;
    input [15:0] x3_a;
    input [15:0] x3_b;
    input [15:0] result;
    src.mem[i*4+0] = { x0_a, x0_b };
    src.mem[i*4+1] = { x1_a, x1_b };
    src.mem[i*4+2] = { x2_a, x2_b };
    src.mem[i*4+3] = { x3_a, x3_b };
    sink.mem[i] = result;
  endtask

  // Directed testing
  //
  // ( x0_a * x0_b ) + ( x1_a * x1_b ) + ( x2_a * x2_b ) + ( x3_a * x3_b ) = result

  initial begin
    //    idx     x0_a     x0_b     x1_a     x1_a     x2_a     x2_b     x3_a     x3_a    result
    load(   0,  16'd00,  16'd00,  16'd00,  16'd00,  16'd00,  16'd00,  16'd00,  16'd00,  16'd000  );
    load(   1,  16'd05,  16'd10,  16'd02,  16'd04,  16'd04,  16'd08,  16'd02,  16'd01,  16'd092  );
    load(   2,  16'd05,  16'd10,  16'd01,  16'd01,  16'd01,  16'd01,  16'd02,  16'd00,  16'd052  );
    load(   3,  16'd10,  16'd10,  16'd08,  16'd08,  16'd00,  16'd00,  16'd00,  16'd91,  16'd164  );
  end

  // Random testing

  logic [15:0] tmp1_a;
  logic [15:0] tmp1_b;
  logic [15:0] tmp2_a;
  logic [15:0] tmp2_b;
  logic [15:0] tmp3_a;
  logic [15:0] tmp3_b;
  logic [15:0] tmp4_a;
  logic [15:0] tmp4_b;
  logic [15:0] result;

  initial begin
    for ( integer i = 0; i < p_nrandom; i = i + 1 ) begin
      tmp1_a = $random % (1'b1 << 8);
      tmp1_b = $random % (1'b1 << 8);
      tmp2_a = $random % (1'b1 << 8);
      tmp2_b = $random % (1'b1 << 8);
      tmp3_a = $random % (1'b1 << 8);
      tmp3_b = $random % (1'b1 << 8);
      tmp4_a = $random % (1'b1 << 8);
      tmp4_b = $random % (1'b1 << 8);
      result = tmp1_a*tmp1_b + tmp2_a*tmp2_b + tmp3_a*tmp3_b + tmp4_a*tmp4_b;
      load( p_ndirected + i, tmp1_a, tmp1_b, tmp2_a, tmp2_b,
                             tmp3_a, tmp3_b, tmp4_a, tmp4_b, result );
    end
  end

  //----------------------------------------------------------------------
  // Run
  //----------------------------------------------------------------------

  initial begin

    // Enable VPD dumping

    $vcdpluson;

    // Verbosity

    src.verbose  = 0;
    sink.verbose = 1;

    // Reset sequence

    reset     = 1'b1;
    clk_reset = 1'b1;

    // Deassert clk_reset and set clock selects

    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD/2);
    clk_reset        = 1'b0;
    mul_clksel_val   = 1'b1;
    mul_clksel_msg   = 1'b0;
    accum_clksel_val = 1'b1;
    accum_clksel_msg = 1'b1;
    #(`CLOCK_PERIOD*10); // wait for clocks to settle
    mul_clksel_val   = 1'b0;
    accum_clksel_val = 1'b0;
    #(`CLOCK_PERIOD/2);

    // Deassert reset halfway through a clock period to avoid races

    #(`CLOCK_PERIOD/2);
    reset = 1'b0;

    // Wait for source and sink to be done

    while ( !( src_done & sink_done ) ) begin
      #(`CLOCK_PERIOD);
    end

    $display( "Done!\n" );

    // Disable VPD dumping

    $vcdplusoff;
    $finish;

  end

endmodule

