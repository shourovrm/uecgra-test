//------------------------------------------------------------------------
// ClockCounter.v
//------------------------------------------------------------------------
// Counter that counts the input clock from the very first cycle after
// clock reset.
//
// Author : Christopher Torng, Peitian Pan

module ClockCounter
#(
  parameter count_to,
  parameter nbits
)
(
  input  wire             clk,
  input  wire             clk_reset,
  output reg  [nbits-1:0] clk_cnt
);

  // The UE suppressor counter has to reset to zero and begin counting
  // precisely aligned with the divided clocks. However, in order to reset
  // synchronously to zero, it needs to be clocked somehow before the
  // divided clocks are even generated.
  //
  // FIXME: for now, this will just be asynchronously reset

  // The counter is responsible for deciding in the clock domain
  // which cycle is safe to transmit data

  always @ ( posedge clk or posedge clk_reset ) begin
    if ( clk_reset ) begin
      clk_cnt <= nbits'( count_to - 1'b1 );
    end
    else begin
      if ( 32'( clk_cnt ) == count_to - 1'b1 ) begin
        clk_cnt <= '0;
      end
      else begin
        clk_cnt <= clk_cnt + 1'b1;
      end
    end
  end

endmodule

