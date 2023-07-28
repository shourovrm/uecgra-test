//------------------------------------------------------------------------
// Sink.t.v
//------------------------------------------------------------------------
// Smoke test the sink by sending it messages
//
// Author : Christopher Torng
// Date   : July 18, 2019
//

`timescale 1ns/1ps

`ifndef CLOCK_PERIOD
  `define CLOCK_PERIOD 2.0
`endif

module th;

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
  // Instantiate sink
  //----------------------------------------------------------------------

  logic        sink_val;
  logic        sink_rdy;
  logic [15:0] sink_msg;
  logic        sink_done;

  Sink #(
    .p_width ( 16 ),
    .p_nmsgs ( 4  )
  ) sink (
    .clk   ( clk       ),
    .reset ( reset     ),
    .val   ( sink_val  ),
    .rdy   ( sink_rdy  ),
    .msg   ( sink_msg  ),
    .done  ( sink_done )
  );

  //----------------------------------------------------------------------
  // Test vectors
  //----------------------------------------------------------------------

  // Messages

  reg [15:0] mem [16:0];

  initial begin
    mem[0] = { 16'd5  };
    mem[1] = { 16'd2  };
    mem[2] = { 16'd18 };
    mem[3] = { 16'd3  };
  end

  // Explicitly load sink

  initial begin
    sink.mem[0] = mem[0];
    sink.mem[1] = mem[1];
    sink.mem[2] = mem[2];
    sink.mem[3] = mem[3];
  end

  //----------------------------------------------------------------------
  // Test
  //----------------------------------------------------------------------

  integer i;

  initial begin

    // Deassert reset halfway through a clock period to avoid races

    reset = 1'b1;
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD/2);
    reset = 1'b0;

    // Send message

    sink_val = 1'b1;

    i = 0;
    while ( !sink_done ) begin
      sink_msg = mem[i];
      #(`CLOCK_PERIOD);
      if ( sink_val & sink_rdy ) begin
        i = i + 1;
      end
    end

    $display( "Done!\n" );
    $finish;

  end

endmodule

