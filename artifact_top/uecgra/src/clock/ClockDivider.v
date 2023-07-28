//========================================================================
// ClockDivider
//========================================================================
// This clock divider takes a "clk_reset" signal, which is used to align
// the generated clock to the first source clock edge after clk_reset is
// deasserted.
//
// Here is a quick waveform sketch of what "clk_reset" does:
//
//     clk_reset   ^^^^^^^^^^^^^^^^^|_____________________________________
//     clk         ________|^^^^^^^^|________|^^^^^^^^|________|^^^^^^^^|_
//     clk_divided __________________________|^^^^^^^^|________ (...)
//
//                 ^ clk_reset is high
//                         ^ clk ticks but clk_divided is still reset low
//                                  ^ clk_reset deasserts
//                                           ^ clk ticks
//                                           ^ clk_divided is edge-aligned
//                                              to this clk edge
//
// The dividers here may not be 50% duty cycle
//
// Author : Christopher Torng, Yanghui Ou
// Date   : August 3, 2018
//

//------------------------------------------------------------------------
// ClockDivider
//------------------------------------------------------------------------

module ClockDivider
#(
  parameter p_divideby = 3
)(
  input  logic clk,
  input  logic clk_reset,
  output logic clk_divided
);

  logic [31:0] counter;

  generate

    //--------------------------------------------------------------------
    // Divide by 1
    //--------------------------------------------------------------------

    if ( p_divideby == 1 ) begin

      assign clk_divided = clk;

    end

    //--------------------------------------------------------------------
    // Divide by 3 with 50% duty cycle
    //--------------------------------------------------------------------
    // See Fig 2: http://www.onsemi.com/pub_link/Collateral/AND8001-D.PDF

    else if ( p_divideby == 3 ) begin

      logic dff1;
      logic dff2;
      logic dff3;

      always @ ( posedge clk ) begin
        if ( clk_reset ) begin
          dff1 <= '1;
          dff2 <= '0;
        end
        else begin
          dff1 <= ~dff1 & ~dff2;
          dff2 <= dff1;
        end
      end

      always @ ( negedge clk ) begin
        if ( clk_reset ) begin
          dff3 <= 'd0;
        end
        else begin
          dff3 <= dff2;
        end
      end

      assign clk_divided = dff2 | dff3;

    end

    //--------------------------------------------------------------------
    // Divide by 9 with 50% duty cycle
    //--------------------------------------------------------------------
    // See Fig 4: http://www.onsemi.com/pub_link/Collateral/AND8001-D.PDF

    else if ( p_divideby == 9 ) begin

      logic dff1;
      logic dff2;
      logic dff3;
      logic dff4;
      logic dff5;

      always @ ( posedge clk ) begin
        if ( clk_reset ) begin
          dff1 <= '1;
          dff2 <= '1;
          dff3 <= '0;
          dff4 <= '0;
        end
        else begin
          dff1 <= ~dff1 & ~dff4;
          dff2 <= ( dff1 & ~dff2 ) | ( ~dff1 & dff2 );
          dff3 <= ( dff1 & dff2 & ~dff3 ) | ( ~dff2 & dff3 ) | ( ~dff1 & dff3 );
          dff4 <= dff1 & dff2 & dff3;
        end
      end

      always @ ( negedge clk ) begin
        if ( clk_reset ) begin
          dff5 <= '0;
        end
        else begin
          dff5 <= dff3;
        end
      end

      assign clk_divided = dff3 | dff5;

    end

    //--------------------------------------------------------------------
    // Divide by N -- counter-based with non-50% duty cycle
    //--------------------------------------------------------------------
    // This is a simple counter-based non-50% duty cycle clock divider.
    //
    // Giving this coding style to Synopsys DC with divide-by-3 and
    // divide-by-9 results in a dumb synthesized netlist with 32-bit
    // counters and 32-bit addition. Since the logic is clocked by "clk"
    // (the pll clock), and because the pll clock can be pretty fast, this
    // then turns into the critical path.
    //
    // Try not to use this for these divide ratios and maybe for others:
    //
    // - p_divideby = 3
    // - p_divideby = 9
    //
    // When possible, we should use the optimized 50% duty cycle choices
    // before falling back to this code.
    //

    else begin

      always @ ( posedge clk ) begin
        if ( clk_reset ) begin
          counter <= 'd0;
        end
        else begin
          if ( counter == p_divideby - 1'b1 ) begin
            counter <= 'd0;
          end
          else begin
            counter <= counter + 1'b1;
          end
        end
      end

      // Align all divided clocks to the first edge after reset

      assign clk_divided = ( counter == 32'd1 );

    end

  endgenerate

endmodule


