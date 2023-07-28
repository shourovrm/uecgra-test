//------------------------------------------------------------------------
// Test.t.v
//------------------------------------------------------------------------
// Smoke test the source and sink together with random values
//
// Author : Christopher Torng
// Date   : July 18, 2019
//

`timescale 1ns/1ps

`ifndef CLOCK_PERIOD
  `define CLOCK_PERIOD 2.0
`endif

module th;

  localparam p_width = 16;  // Random data bitwidth
  localparam p_nmsgs = 100; // Number of messages to send

  //----------------------------------------------------------------------
  // Setup
  //----------------------------------------------------------------------

  // Clock and reset

  logic reset = 1'b1;
  logic clk   = 1'b1;

  always #(`CLOCK_PERIOD/2.0) clk = ~clk;

  initial
    $display( "Simulating with clock period: %f", `CLOCK_PERIOD );

  //----------------------------------------------------------------------
  // Instantiate source and sink
  //----------------------------------------------------------------------

  // Source

  logic               src_val;
  logic               src_rdy;
  logic [p_width-1:0] src_msg;
  logic               src_done;

  Source #(
    .p_width ( p_width  ),
    .p_nmsgs ( p_nmsgs )
  ) src (
    .clk   ( clk      ),
    .reset ( reset    ),
    .val   ( src_val  ),
    .rdy   ( src_rdy  ),
    .msg   ( src_msg  ),
    .done  ( src_done )
  );

  // Sink

  logic               sink_val;
  logic               sink_rdy;
  logic [p_width-1:0] sink_msg;
  logic               sink_done;

  Sink #(
    .p_width ( p_width  ),
    .p_nmsgs ( p_nmsgs )
  ) sink (
    .clk   ( clk       ),
    .reset ( reset     ),
    .val   ( sink_val  ),
    .rdy   ( sink_rdy  ),
    .msg   ( sink_msg  ),
    .done  ( sink_done )
  );

  assign sink_val = src_val;
  assign sink_msg = src_msg;
  assign src_rdy  = sink_rdy;

  //----------------------------------------------------------------------
  // Test vectors
  //----------------------------------------------------------------------

  // Explicitly load src and sink

  logic [31:0] tmp;

  initial begin
    for ( integer i = 0; i < p_nmsgs; i++ ) begin
      tmp         = $random;
      src.mem[i]  = tmp[p_width-1:0];
      sink.mem[i] = tmp[p_width-1:0];
    end
  end

  //----------------------------------------------------------------------
  // Test
  //----------------------------------------------------------------------

  initial begin

    // Deassert reset halfway through a clock period to avoid races

    reset = 1'b1;
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD/2);
    reset = 1'b0;

    // Wait for source and sink to be done

    while ( !( src_done & sink_done ) ) begin
      #(`CLOCK_PERIOD);
    end

    $display( "Done!\n" );
    $finish;

  end

endmodule

