//------------------------------------------------------------------------
// BisynchronousNormalQueue
//------------------------------------------------------------------------
// A bisynchronous normal queue built to interface between two clock
// domains. This queue does not have brute-force synchronizers and gray
// code counters, so it is not an asynchronous fifo. It is meant to be
// used with the help of static timing analysis tools where the phase
// relationship between clocks is known.
//
// Note: This implementation only supports numbers of entries that are
// powers of 2.
//
// This queue uses read and write pointers that have an extra bit to
// differentiate full and empty conditions. The two pointers are initially
// reset so that they are equal (e.g., resetting both to 0 works), and
// this indicates an empty queue. Subsequent writes then bump the write
// pointer, while subsequent reads bump the read pointer and eventually
// "catch up" to the write pointer. The queue is full when the write
// pointer has incremented "full circle" such that the read and write
// pointers are now equal again, except for having different MSBs.
//
// Author : Christopher Torng
// Date   : August 3, 2018
//

module NormalQueue1
#(
  parameter p_data_width = 32
)(
  input wire clk,
  input wire reset,
  input wire w_val,
  output wire w_rdy,
  input wire [p_data_width-1:0] w_msg,
  output wire r_val,
  input wire r_rdy,
  output wire [p_data_width-1:0] r_msg
);

  reg [p_data_width-1:0] entry;
  reg full;

  wire w_go = w_val & w_rdy;
  wire r_go = r_val & r_rdy;

  always @ ( posedge clk ) begin
    if ( reset )
      full <= 0;
    else
      full <= (full & ~r_go) | (~full & w_go);
  end

  always @ ( posedge clk ) begin
    if ( reset )
      entry <= 0;
    else begin
      if ( w_go )
        entry <= w_msg;
    end
  end

  assign w_rdy = ~reset & ~full;
  assign r_val = ~reset & full;
  assign r_msg = entry;

endmodule

module DelayQueue
#(
  parameter p_data_width = 32,
  parameter p_fifo_latency = 1
)(
  input  wire clk,
  input  wire reset,
  input  wire w_val,
  output wire w_rdy,
  input  wire [p_data_width-1:0] w_msg,
  output wire r_val,
  input  wire r_rdy,
  output wire [p_data_width-1:0] r_msg
);

  wire [p_fifo_latency:0] q_w_val;
  wire [p_fifo_latency:0] q_w_rdy;
  wire [p_data_width-1:0] q_w_msg [p_fifo_latency:0];

  genvar i;
  generate
    for(i = 0; i < p_fifo_latency; i = i+1) begin : inst_normal_q
      NormalQueue1 #(
        .p_data_width( p_data_width )
      ) q (
        .clk( clk ),
        .reset( reset ),
        .w_val( q_w_val[i] ),
        .w_rdy( q_w_rdy[i] ),
        .w_msg( q_w_msg[i] ),
        .r_val( q_w_val[i+1] ),
        .r_rdy( q_w_rdy[i+1] ),
        .r_msg( q_w_msg[i+1] )
      );
    end
  endgenerate

  /* verilator lint_off UNOPTFLAT */
  assign q_w_val[0] = w_val & w_rdy;

  assign w_rdy = &q_w_rdy[p_fifo_latency-1:0];
  assign q_w_msg[0] = w_msg;

  assign r_val = q_w_val[p_fifo_latency];
  assign r_msg = q_w_msg[p_fifo_latency];
  assign q_w_rdy[p_fifo_latency] = r_rdy;

endmodule

module BisyncNormalQueue
#(
  parameter p_data_width  = 32,
  parameter p_num_entries = 8           // Only supports powers of 2!
)(
  input  wire                    w_clk, // Write clock
  input  wire                    r_clk, // Read clock
  input  wire                    reset,
  input  wire                    w_val,
  output wire                    w_rdy,
  input  wire [p_data_width-1:0] w_msg,
  output wire                    r_val,
  input  wire                    r_rdy,
  output wire [p_data_width-1:0] r_msg
);

  localparam p_num_entries_bits = $clog2( p_num_entries );

  //----------------------------------------------------------------------
  // Control
  //----------------------------------------------------------------------

  // Go signals

  wire w_go = w_val & w_rdy;
  wire r_go = r_val & r_rdy;

  // Read and write pointers, including the extra wrap bit

  reg  [p_num_entries_bits:0] w_ptr_with_wrapbit;
  reg  [p_num_entries_bits:0] r_ptr_with_wrapbit;

  // Convenience wires to separate the wrap bits from the actual pointers

  wire [p_num_entries_bits-1:0] w_ptr;
  wire                          w_ptr_wrapbit;

  wire [p_num_entries_bits-1:0] r_ptr;
  wire                          r_ptr_wrapbit;

  assign w_ptr         = w_ptr_with_wrapbit[p_num_entries_bits-1:0];
  assign w_ptr_wrapbit = w_ptr_with_wrapbit[p_num_entries_bits];

  assign r_ptr         = r_ptr_with_wrapbit[p_num_entries_bits-1:0];
  assign r_ptr_wrapbit = r_ptr_with_wrapbit[p_num_entries_bits];

  // Write pointer update, clocked with the write clock

  always @ ( posedge w_clk ) begin
    if ( reset ) begin
      w_ptr_with_wrapbit <= '0;
    end
    else if ( w_go ) begin
      w_ptr_with_wrapbit <= w_ptr_with_wrapbit + 1'b1;
    end
  end

  // Read pointer update, clocked with the read clock

  always @ ( posedge r_clk ) begin
    if ( reset ) begin
      r_ptr_with_wrapbit <= '0;
    end
    else if ( r_go ) begin
      r_ptr_with_wrapbit <= r_ptr_with_wrapbit + 1'b1;
    end
  end

  // full
  //
  // The queue is full when the read and write pointers are equal but have
  // different wrap bits (i.e., different MSBs). This indicates that we
  // have enqueued "num_entries" messages and cannot store any more.
  //
  // Note -- this queue implementation only works if "num_entries" is
  // a power of two, since we have assumed here that equal pointers
  // indicates a full queue,

  wire full = ( w_ptr == r_ptr ) && ( w_ptr_wrapbit != r_ptr_wrapbit );

  // empty
  //
  // The queue is empty when the full-length pointers (including wrap
  // bits) are equal.

  wire empty = ( w_ptr_with_wrapbit == r_ptr_with_wrapbit );

  // Set output control signals
  //
  // - w_rdy: We are ready to write if the queue has space, i.e., not full
  // - r_val: Data is valid for read if the queue is not empty

  assign w_rdy = !full;
  assign r_val = !empty;

  //----------------------------------------------------------------------
  // Datapath
  //----------------------------------------------------------------------

  // Internal memory

  reg [p_data_width-1:0] mem [p_num_entries-1:0];

  // Writes, clocked with the write clock

  always @ ( posedge w_clk ) begin
    if ( w_go ) begin
      mem[ w_ptr ] <= w_msg;
    end
  end

  // Reads are synchronous with the read clock

  assign r_msg = mem[ r_ptr ];

endmodule

module BisynchronousNormalQueue
#(
  parameter p_data_width  = 32,
  parameter p_num_entries = 8,           // Only supports powers of 2!
  parameter p_fifo_latency = 0
)(
  input  wire                    w_clk, // Write clock
  input  wire                    r_clk, // Read clock
  input  wire                    reset,
  input  wire                    w_val,
  output wire                    w_rdy,
  input  wire [p_data_width-1:0] w_msg,
  output wire                    r_val,
  input  wire                    r_rdy,
  output wire [p_data_width-1:0] r_msg
);

  wire q_r_val, q_r_rdy;
  wire [p_data_width-1:0] q_r_msg;

  BisyncNormalQueue #(
    .p_data_width( p_data_width ),
    .p_num_entries( p_num_entries )
  ) q (
    .w_clk( w_clk ),
    .r_clk( r_clk ),
    .reset( reset ),
    .w_val( w_val ),
    .w_rdy( w_rdy ),
    .w_msg( w_msg ),
    .r_val( q_r_val ),
    .r_rdy( q_r_rdy ),
    .r_msg( q_r_msg )
  );

  generate
    if( p_fifo_latency == 0 ) begin
      assign r_val = q_r_val;
      assign q_r_rdy = r_rdy;
      assign r_msg = q_r_msg;
    end
    else begin
      DelayQueue #(
        .p_data_width( p_data_width ),
        .p_fifo_latency( p_fifo_latency )
      ) delay_q (
        .clk( r_clk ),
        .reset( reset ),
        .w_val( q_r_val ),
        .w_rdy( q_r_rdy ),
        .w_msg( q_r_msg ),
        .r_val( r_val ),
        .r_rdy( r_rdy ),
        .r_msg( r_msg )
      );
    end
  endgenerate

endmodule
