//------------------------------------------------------------------------
// BisynchronousNormalQueue.t.v
//------------------------------------------------------------------------
// Smoke test
//
// Author : Christopher Torng
// Date   : July 22, 2019
//

`timescale 1ns/1ps

`ifndef CLOCK_PERIOD
  `define CLOCK_PERIOD 2.0
`endif

module th;

  // Number of each type of test

  localparam n_directed = 8;
  localparam n_random   = 100;

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

  initial
    $display( "Simulating with clock period: %f", `CLOCK_PERIOD );

  //----------------------------------------------------------------------
  // Instantiate
  //----------------------------------------------------------------------

  // Source

  logic        src_val;
  logic        src_rdy;
  logic [15:0] src_msg;
  logic        src_done;

  Source #(
    .width  ( 16 ),
    .n_msgs ( n_directed + n_random )
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
  logic [15:0] sink_msg;
  logic        sink_done;

  Sink #(
    .width  ( 16 ),
    .n_msgs ( n_directed + n_random )
  ) sink (
    .clk   ( clk2      ),
    .reset ( reset     ),
    .val   ( sink_val  ),
    .rdy   ( sink_rdy  ),
    .msg   ( sink_msg  ),
    .done  ( sink_done )
  );

  // Design

  BisynchronousNormalQueue #(
    .p_data_width  ( 16 ),
    .p_num_entries ( 2  )
  ) fifo (
    .w_clk ( clk1     ),
    .r_clk ( clk2     ),
    .reset ( reset    ),
    .w_val ( src_val  ),
    .w_rdy ( src_rdy  ),
    .w_msg ( src_msg  ),
    .r_val ( sink_val ),
    .r_rdy ( sink_rdy ),
    .r_msg ( sink_msg )
  );

  //----------------------------------------------------------------------
  // Test vectors
  //----------------------------------------------------------------------

  // Helper task to load the source and sink memories

  task load;
    input [31:0] i;
    input [15:0] data;
    src.mem[i]  = data;
    sink.mem[i] = data;
  endtask

  // Directed testing

  initial begin
    //    idx    data
    load(   0, 16'd00  );
    load(   1, 16'd05  );
    load(   2, 16'd10  );
    load(   3, 16'd99  );
    load(   4, 16'd99  );
    load(   5, 16'd42  );
    load(   6, 16'd82  );
    load(   7, 16'd23  );
  end

  // Random testing

  logic [15:0] tmp;

  initial begin
    for ( integer i = 0; i < n_random; i = i + 1 ) begin
      tmp = $random % (1'b1 << 16);
      load( n_directed + i, tmp );
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

    // Reset

    clk_reset = 1'b1;
    reset     = 1'b1;

    // Deassert clock reset

    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD/2);
    clk_reset = 1'b0;
    #(`CLOCK_PERIOD/2);

    // Deassert reset halfway through a clock period to avoid races

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


