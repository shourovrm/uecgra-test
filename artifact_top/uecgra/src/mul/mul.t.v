//------------------------------------------------------------------------
// mul.t.v
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

  logic reset = 1'b1;
  logic clk   = 1'b1;

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
    .p_nmsgs ( p_ndirected + p_nrandom )
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
  logic [31:0] sink_msg;
  logic        sink_done;

  Sink #(
    .p_width ( 32 ),
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

  mul #(
    .p_width   ( 16 ),
    .p_ncycles ( 3  )
  ) dut (
    .clk      ( clk      ),
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
    input [15:0] a;
    input [15:0] b;
    input [31:0] result;
    src.mem[i]  = { a, b };
    sink.mem[i] = result;
  endtask

  // Directed testing

  initial begin
    //    idx        a        b    result
    load(   0,  16'd05,  16'd10,  32'd050  );
    load(   1,  16'd02,  16'd10,  32'd020  );
    load(   2,  16'd18,  16'd14,  32'd252  );
    load(   3,  16'd03,  16'd13,  32'd039  );
  end

  // Random testing

  logic [15:0] tmp1;
  logic [15:0] tmp2;
  logic [31:0] result;

  initial begin
    for ( integer i = 0; i < p_nrandom; i = i + 1 ) begin
      tmp1   = $random % (1'b1 << 8);
      tmp2   = $random % (1'b1 << 8);
      result = tmp1 * tmp2;
      load( p_ndirected + i, tmp1, tmp2, result );
    end
  end

  //----------------------------------------------------------------------
  // Run
  //----------------------------------------------------------------------

  initial begin

    // Verbosity

    src.verbose  = 0;
    sink.verbose = 1;

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

