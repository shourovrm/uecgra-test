//------------------------------------------------------------------------
// ClockSwitcher
//------------------------------------------------------------------------
// Glitchless clock switching circuit with val/rdy protocol for switching
// to a different clock (the switch_msg is the new clk_sel).
//
// - select is 1'b0 = clk1
// - select is 1'b1 = clk2
//
// Author : Christopher Torng, Peitian Pan
// Date   : July 22, 2019
//

module ClockSwitcher
(
  input  logic clk1,
  input  logic clk2,
  input  logic clk_reset,
  input  logic switch_val,
  output logic switch_rdy,
  input  logic switch_msg,
  output logic clk_out
);

  // Handshake

  logic switch_go;

  assign switch_rdy = 1'b1;
  assign switch_go = switch_val & switch_rdy;

  // Clock select register (configuration register)
  //
  // NOTE: Currently asynchronously resetting this. Maybe there is
  // a better way to get clk_sel to reset, but it is posedge triggered by
  // clk_out, which (recursively) depends on clk_sel. The clk_out is low
  // until reset is deasserted, so there is no posedge to synchronously
  // reset this register with. So we have to asynchronously reset it...
  //
  // Why is this posedge clk_out and not negedge clk_out? Negedge would
  // give a full cycle to get from here through the clock selection logic.
  // Posedge gives the full cycle to whatever is driving the switch_msg.
  // We know very well what logic is in the clock selection, and it's
  // basically two gates. Half a clock period is definitely enough for two
  // gates. We should leave this as posedge clk_out to give that extra
  // time to whatever drives switch_msg instead.

  logic clk_sel;

  always @ ( posedge clk_out or posedge clk_reset ) begin
    if ( clk_reset ) begin
      clk_sel <= 1'b0;
    end
    else if ( switch_go ) begin
      clk_sel <= switch_msg;
    end
  end

  // Glitch-free clock selection
  //
  // Read these for details:
  //
  // - https://www.eetimes.com/document.asp?doc_id=1202359
  // - https://ieeexplore.ieee.org/xpls/icp.jsp?arnumber=6674704
  // - https://patents.google.com/patent/US5357146A/en
  //
  // The scheme is to pass the mux select through negative edge-triggered
  // flops. This guarantees that any state changes happen when clocks are
  // low, preventing glitches. The flops also have feedback which works to
  // deselect the current clock before the new clock is selected.
  //
  // Two stages of flops could be used as brute-force synchronizers if
  // needed, but in our case because our clock sources are coming from
  // dividers and our select is registered in one of the two domains,
  // there is no need to synchronize.
  //
  // - clk_sel == 1'b0 : select clk1
  // - clk_sel == 1'b1 : select clk2
  //

  // Clock reset
  //
  // These flops are also asynchronously reset. If they are hooked to the
  // normal logic reset, then the clk_out will not be generated until
  // _after_ both clk_reset and reset are deasserted. That means that this
  // entire block will not be clocked, and so other synchronous registers
  // in the block will not be reset yet. It would basically mean that we
  // need a third phase of reset (first to generate divided and aligned
  // clk1 and clk2, second for this module to generate a clk_out for the
  // block, and third to actually reset the logic with the clk_out from
  // this block.
  //
  // Instead, we have just two phases of reset thanks to asynchronously
  // reset flops here.
  //
  // 1. clk_reset
  //
  // Generate aligned divided clk1/clk2 + select clk_out from switcher
  //
  // 2. reset
  //
  // Use clk_out to reset state synchronously within the block
  //

  logic clk1_select;
  logic clk2_select;

  always @ ( negedge clk1 or posedge clk_reset ) begin
    if ( clk_reset ) begin
      clk1_select <= 1'b0;
    end
    else begin
      clk1_select <= ~clk_sel & ~clk2_select;
    end
  end

  always @ ( negedge clk2 or posedge clk_reset ) begin
    if ( clk_reset ) begin
      clk2_select <= 1'b0;
    end
    else begin
      clk2_select <= clk_sel & ~clk1_select;
    end
  end

  // Output clock

  assign clk_out = ( clk1 & clk1_select ) | ( clk2 & clk2_select );

endmodule

//------------------------------------------------------------------------
// ClockSwitcher_3
//------------------------------------------------------------------------
// A clock switcher that switches from 3 input clocks.
//
// - select is 2'b00 = clk1
// - select is 2'b01 = clk2
// - select is 2'b10 = clk3
// - select is 2'b11 = clk_out is LOW
//
// Author : Christopher Torng, Peitian Pan
// Date   : Aug 18, 2019
//

module ClockSwitcher_3
(
  input  logic        clk1, // fast
  input  logic        clk2, // slow
  input  logic        clk3, // nominal

  input  logic        clk_reset,
  input  logic        switch_val,
  output logic        switch_rdy,
  input  logic [1:0]  switch_msg,
  output logic        clk_out
);

  // Handshake

  logic switch_go;

  assign switch_rdy = 1'b1;
  assign switch_go = switch_val & switch_rdy;

  // Clock select register (configuration register)
  //
  // NOTE: Currently asynchronously resetting this. Maybe there is
  // a better way to get clk_sel to reset, but it is posedge triggered by
  // clk_out, which (recursively) depends on clk_sel. The clk_out is low
  // until reset is deasserted, so there is no posedge to synchronously
  // reset this register with. So we have to asynchronously reset it...
  //
  // Why is this posedge clk_out and not negedge clk_out? Negedge would
  // give a full cycle to get from here through the clock selection logic.
  // Posedge gives the full cycle to whatever is driving the switch_msg.
  // We know very well what logic is in the clock selection, and it's
  // basically two gates. Half a clock period is definitely enough for two
  // gates. We should leave this as posedge clk_out to give that extra
  // time to whatever drives switch_msg instead.

  logic clk1_sel;
  logic clk2_sel;
  logic clk3_sel;

  // Use the slowest clock as the configuration clock to avoid super-short
  // paths from posedge of config clock to negedge of selected clock
  //
  // This is to make timing easier to meet within the clock switcher. With
  // a div2/div3/div9 ratio, using the div9 as the config clock relaxes
  // the timing constraints for the select registers down below.

  always @ ( posedge clk2 or posedge clk_reset ) begin
    if ( clk_reset ) begin
      clk1_sel <= 1'b0;
      clk2_sel <= 1'b0;
      clk3_sel <= 1'b1;
    end
    else if ( switch_go ) begin
      clk1_sel <= switch_msg == 2'b00;
      clk2_sel <= switch_msg == 2'b01;
      clk3_sel <= ( switch_msg == 2'b10 ) | ( switch_msg == 2'b11 );
    end
  end

  // Glitch-free clock selection
  //
  // Read these for details:
  //
  // - https://www.eetimes.com/document.asp?doc_id=1202359
  // - https://ieeexplore.ieee.org/xpls/icp.jsp?arnumber=6674704
  // - https://patents.google.com/patent/US5357146A/en
  //
  // The scheme is to pass the mux select through negative edge-triggered
  // flops. This guarantees that any state changes happen when clocks are
  // low, preventing glitches. The flops also have feedback which works to
  // deselect the current clock before the new clock is selected.
  //
  // Two stages of flops could be used as brute-force synchronizers if
  // needed, but in our case because our clock sources are coming from
  // dividers and our select is registered in one of the two domains,
  // there is no need to synchronize.
  //
  // - clk1_sel == 1'b1 : select clk1
  // - clk2_sel == 1'b1 : select clk2
  // - clk3_sel == 1'b1 : select clk3
  //

  // Clock reset
  //
  // These flops are also asynchronously reset. If they are hooked to the
  // normal logic reset, then the clk_out will not be generated until
  // _after_ both clk_reset and reset are deasserted. That means that this
  // entire block will not be clocked, and so other synchronous registers
  // in the block will not be reset yet. It would basically mean that we
  // need a third phase of reset (first to generate divided and aligned
  // clk1 and clk2, second for this module to generate a clk_out for the
  // block, and third to actually reset the logic with the clk_out from
  // this block.
  //
  // Instead, we have just two phases of reset thanks to asynchronously
  // reset flops here.
  //
  // 1. clk_reset
  //
  // Generate aligned divided clk1/clk2/clk3 + select clk_out from switcher
  //
  // 2. reset
  //
  // Use clk_out to reset state synchronously within the block
  //

  logic clk1_select;
  logic clk2_select;
  logic clk3_select;

  always @ ( negedge clk1 or posedge clk_reset ) begin
    if ( clk_reset ) begin
      clk1_select <= 1'b0;
    end
    else begin
      clk1_select <= clk1_sel & ~clk2_select & ~clk3_select;
    end
  end

  always @ ( negedge clk2 or posedge clk_reset ) begin
    if ( clk_reset ) begin
      clk2_select <= 1'b0;
    end
    else begin
      clk2_select <= clk2_sel & ~clk1_select & ~clk3_select;
    end
  end

  always @ ( negedge clk3 or posedge clk_reset ) begin
    if ( clk_reset ) begin
      clk3_select <= 1'b0;
    end
    else begin
      clk3_select <= clk3_sel & ~clk1_select & ~clk2_select;
    end
  end

  // Output clock

  assign clk_out = ( clk1 & clk1_select ) | ( clk2 & clk2_select ) | ( clk3 & clk3_select );

endmodule

