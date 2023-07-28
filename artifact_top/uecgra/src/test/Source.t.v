//------------------------------------------------------------------------
// Source.t.v
//------------------------------------------------------------------------
// Smoke test the source by checking its messages
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
  // Instantiate source
  //----------------------------------------------------------------------

  logic        src_val;
  logic        src_rdy;
  logic [31:0] src_msg;
  logic        src_done;

  Source #(
    .p_width ( 32 ),
    .p_nmsgs ( 4  )
  ) src (
    .clk   ( clk      ),
    .reset ( reset    ),
    .val   ( src_val  ),
    .rdy   ( src_rdy  ),
    .msg   ( src_msg  ),
    .done  ( src_done )
  );

  //----------------------------------------------------------------------
  // Test vectors
  //----------------------------------------------------------------------

  // Messages

  reg [31:0] mem [16:0];

  initial begin
    mem[0] = { 16'd15, 16'd10 };
    mem[1] = { 16'd22, 16'd10 };
    mem[2] = { 16'd36, 16'd18 };
    mem[3] = { 16'd36, 16'd21 };
  end

  // Explicitly load source

  initial begin
    src.mem[0] = mem[0];
    src.mem[1] = mem[1];
    src.mem[2] = mem[2];
    src.mem[3] = mem[3];
  end

  //----------------------------------------------------------------------
  // Test
  //----------------------------------------------------------------------

  integer i;

  initial begin

    src_rdy = 1'b0;

    // Deassert reset halfway through a clock period to avoid races

    reset = 1'b1;
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD/2);
    reset = 1'b0;
    #(`CLOCK_PERIOD);

    // Receive message

    src_rdy = 1'b1;

    i = 0;
    while ( !src_done ) begin
      if ( src_val & src_rdy ) begin
        if ( src_msg === mem[i] ) begin
          $display( "%d: [ passed ] Entry %d (actual 0x%h, expect 0x%h)",
                         $time, i, src_msg, mem[i] );
        end
        else begin
          $display( "%d: [ failed ] Entry %d (actual 0x%h, expect 0x%h)",
                         $time, i, src_msg, mem[i] );
        end
      end
      #(`CLOCK_PERIOD);
      i = i + 1;
    end

    $display( "Done!\n" );
    $finish;

  end

endmodule

