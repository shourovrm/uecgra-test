//------------------------------------------------------------------------
// Sink
//------------------------------------------------------------------------
// A test sink with a val/rdy interface
//
// Notes:
//
// - The sink memory can be loaded explicitly from the test harness or
//   from the initial block at the end of this module
//
// Author : Christopher Torng
// Date   : July 18, 2019
//

module Sink  #(
  parameter p_width       = 16,
  parameter p_nmsgs       = 4,
  // Do not set these from outside!
  parameter p_nmsgs_width = $clog2( p_nmsgs + 1 ) // plus 1 for done flag
)(
  input  wire               clk,
  input  wire               reset,
  input  wire               val,
  output wire               rdy,
  input  wire [p_width-1:0] msg,
  output wire               done
);

  reg verbose = 1'b1;

  // Memory

  reg [p_width-1:0] mem [p_nmsgs:0];

  //----------------------------------------------------------------------
  // Control
  //----------------------------------------------------------------------
  // The state is just the index of the memory. The state increments on
  // every handshake until we finish the last message. Notice that DONE is
  // one index beyond p_nmsgs. This is why p_nmsgs_width is the $clog2 of
  // p_nmsgs + 1. When the state is at DONE, the done output signal is
  // raised.

  reg [p_nmsgs_width-1:0] state;

  // State transitions

  localparam INIT = '0;
  localparam DONE = p_nmsgs;

  always @ ( posedge clk ) begin
    if ( reset ) begin
      state <= INIT;
    end
    else if ( state != DONE ) begin
      if ( val & rdy ) begin
        state <= state + 1'b1;
        if ( verbose ) begin
          if ( msg === mem[state] ) begin
            $display( "%d: [ passed ] Entry %d (actual 0x%h, expect 0x%h)",
                           $time, state, msg, mem[state] );
          end
          else begin
            $display( "%d: [ failed ] Entry %d (actual 0x%h, expect 0x%h)",
                           $time, state, msg, mem[state] );
          end
        end
      end
    end
  end

  // Done signal

  assign done = ( state == DONE );

  // Handshake -- Always ready if not done

  assign rdy = !done;

  //---------------------------------------------------------------------
  // Initialization -- comment out if unused
  //---------------------------------------------------------------------
  // Explicitly load data, if not loaded hierarchically from test harness

  // initial begin
  //   mem[0] = { 16'd5  };
  //   mem[1] = { 16'd2  };
  //   mem[2] = { 16'd18 };
  //   mem[3] = { 16'd3  };
  // end

endmodule


