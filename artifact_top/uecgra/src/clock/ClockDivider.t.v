//------------------------------------------------------------------------
// ClockDivider.t.v
//------------------------------------------------------------------------
// Smoke test -- open the vpd waves to see the three divided clocks
//
// Author : Christopher Torng
// Date   : October 1, 2019
//

`timescale 1ns/1ps

`ifndef CLOCK_PERIOD
  `define CLOCK_PERIOD 2.0
`endif

module th;

  //----------------------------------------------------------------------
  // Setup
  //----------------------------------------------------------------------

  // Dedicated reset for clock dividers to align all divided clocks

  logic clk_reset = 1'b1;

  // Clock

  logic clk = 1'b1;

  always #(`CLOCK_PERIOD/2.0) clk = ~clk;

  // Clock dividers

  localparam p_clk1_div = 2;
  localparam p_clk2_div = 3;
  localparam p_clk3_div = 9;

  logic clk1;
  logic clk2;
  logic clk3;

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

  ClockDivider #( p_clk3_div ) clk_div_3 (
    .clk         ( clk       ),
    .clk_reset   ( clk_reset ),
    .clk_divided ( clk3      )
  );

  initial
    $display( "Simulating with clock period: %f", `CLOCK_PERIOD );


  //----------------------------------------------------------------------
  // Run
  //----------------------------------------------------------------------

  initial begin

    // Enable VPD dumping

    $vcdpluson;

    // Deassert reset halfway through a clock period to avoid races

    clk_reset = 1'b1;
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD);
    #(`CLOCK_PERIOD/2);
    clk_reset = 1'b0;

    // Run for some time

    #(`CLOCK_PERIOD*1000);

    $display( "Done!\n" );

    // Disable VPD dumping

    $vcdplusoff;
    $finish;

  end

endmodule

