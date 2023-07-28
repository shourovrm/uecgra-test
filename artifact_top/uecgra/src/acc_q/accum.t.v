//------------------------------------------------------------------------
// accum.t.v
//------------------------------------------------------------------------
// Smoke test
//
// Author : Christopher Torng, Yanghui Ou
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

  // Dedicated reset for clock dividers to align all divided clocks

  logic clk_reset = 1'b1;

  // Clock and reset

  logic reset = 1'b1;
  logic clk   = 1'b1;

  always #(`CLOCK_PERIOD/2.0) clk = ~clk;

  // Clock dividers

  localparam p_clk1_div = 3;
  localparam p_clk2_div = 5;

  logic clk1;
  logic clk2;

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
    .clk   ( clk1     ),
    .reset ( reset    ),
    .val   ( src_val  ),
    .rdy   ( src_rdy  ),
    .msg   ( src_msg  ),
    .done  ( src_done )
  );

  // Sink

  logic        sink_val;
  logic        sink_rdy;
  logic [31:0] sink_msg;
  logic        sink_done;

  Sink #(
    .p_width ( 32 ),
    .p_nmsgs ( p_ndirected + p_nrandom )
  ) sink (
    .clk   ( clk2      ),
    .reset ( reset     ),
    .val   ( sink_val  ),
    .rdy   ( sink_rdy  ),
    .msg   ( sink_msg  ),
    .done  ( sink_done )
  );

  // Design

  accum #(
    .p_width  ( 32 ),
    .p_nmsgs  ( 4  )
  ) dut (
    .clk_m    ( clk1     ),
    .clk      ( clk2     ),
    .reset    ( reset    ),
    .req_val  ( src_val  ),
    .req_rdy  ( src_rdy  ),
    .req_msg  ( src_msg  ),
    .resp_val ( sink_val ),
    .resp_rdy ( sink_rdy ),
    .resp_msg ( sink_msg )
  );

  //----------------------------------------------------------------------
  // Test vectors
  //----------------------------------------------------------------------

  // Helper task to load the source and sink memories

  task load;
    input [31:0] i;
    input [31:0] x0;
    input [31:0] x1;
    input [31:0] x2;
    input [31:0] x3;
    input [31:0] result;
    src.mem[i*4+0] = x0;
    src.mem[i*4+1] = x1;
    src.mem[i*4+2] = x2;
    src.mem[i*4+3] = x3;
    sink.mem[i] = result;
  endtask

  // Directed testing

  initial begin
    //    idx       x0       x1       x2       x3    result
    load(   0,  32'd05,  32'd10,  32'd05,  32'd10,  32'd030  );
    load(   1,  32'd02,  32'd10,  32'd03,  32'd11,  32'd026  );
    load(   2,  32'd18,  32'd14,  32'd08,  32'd04,  32'd044  );
    load(   3,  32'd93,  32'd13,  32'd03,  32'd01,  32'd110  );
  end

  // Random testing

  logic [31:0] tmp1;
  logic [31:0] tmp2;
  logic [31:0] tmp3;
  logic [31:0] tmp4;
  logic [31:0] result;

  initial begin
    for ( integer i = 0; i < p_nrandom; i = i + 1 ) begin
      tmp1   = $random % (1'b1 << 8);
      tmp2   = $random % (1'b1 << 8);
      tmp3   = $random % (1'b1 << 8);
      tmp4   = $random % (1'b1 << 8);
      result = tmp1 + tmp2 + tmp3 + tmp4;
      load( p_ndirected + i, tmp1, tmp2, tmp3, tmp4, result );
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

    // Deassert reset halfway through a clock period to avoid races

    clk_reset = 1'b1;
    reset = 1'b1;

    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD/2);
    clk_reset = 1'b0;
    #(`CLOCK_PERIOD/2);

    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD);
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

