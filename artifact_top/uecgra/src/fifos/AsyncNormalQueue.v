//------------------------------------------------------------------------
// AsyncNormalQueue
//------------------------------------------------------------------------
// An asynchronous normal queue built to interface between two clock
// domains.
//
// Author : Yanghui Ou
//   Date : July 31, 2019
//

module AsyncNormalQueue #(
  parameter p_data_width  = 32,
  parameter p_num_entries = 2            // Only supports powers of 2
)(
  input  logic                    w_clk, // Writer clock
  input  logic                    r_clk, // Reader clock
  input  logic                    reset,
  input  logic                    enq_en,
  output logic                    enq_rdy,
  input  logic [p_data_width-1:0] enq_msg,
  input  logic                    deq_en,
  output logic                    deq_rdy,
  output logic [p_data_width-1:0] deq_msg
);

  localparam c_num_entries_bits = $clog2( p_num_entries );
  localparam c_sync_nstages     = 2;

  //----------------------------------------------------------------------
  // Control
  //----------------------------------------------------------------------

  // Enq and deq pointers and extra wrap bits.

  logic enq_wrapbit;
  logic deq_wrapbit;

  logic enq_wrapping;
  logic deq_wrapping;

  logic [c_num_entries_bits-1:0] enq_ptr;
  logic [c_num_entries_bits-1:0] deq_ptr;

  logic [c_num_entries_bits:0] enq_ptr_with_wrapbit;
  logic [c_num_entries_bits:0] deq_ptr_with_wrapbit;

  assign enq_wrapping = enq_ptr==p_num_entries[c_num_entries_bits-1:0]
  assign deq_wrapping = deq_ptr==p_num_entries[c_num_entries_bits-1:0]

  // Enq pointer update, clocked with writer clock

  always @ ( posedge w_clk ) begin
    if ( reset ) begin
      enq_wrapbit <= 'd0;
      enq_ptr     <= 'd0;
    end
    else if ( enq_en ) begin
      enq_wrapbit <= enq_wrapping ? ~enq_wrapbit : enq_wrapbit;
      enq_ptr     <= enq_wrapping ? 'd0          : enq_ptr + 'd1;
    end
  end

  // Deq pointer update, clocked with reader clock

  always @ ( posedge r_clk ) begin
    if ( reset ) begin
      deq_wrapbit <= 'd0;
      deq_ptr     <= 'd0;
    end
    else if ( deq_en ) begin
      deq_wrapbit <= deq_wrapping ? ~deq_wrapbit : deq_wrapbit;
      deq_ptr     <= deq_wrapping ? 'd0          : deq_ptr + 'd1;
    end
  end

  // Full and empty logic

  logic full;
  logic empty;

  logic sync_enq_wrapbit;
  logic sync_deq_wrapbit;

  logic [c_num_entries_bits-1:0] sync_enq_ptr;
  logic [c_num_entries_bits-1:0] sync_deq_ptr;

  assign full  = ( enq_ptr == sync_deq_ptr ) & ( enq_wrapbit != sync_deq_wrapbit );
  assign empty = ( sync_enq_ptr == deq_ptr ) & ( sync_enq_wrapbit == deq_wrapbit );

  //----------------------------------------------------------------------
  // Datapath
  //----------------------------------------------------------------------

  // Internal memory

  reg [p_data_width-1:0] mem [p_num_entries-1:0];

  // TODO: gray code encoder -> synchronizer -> decoder

  synchronizer #(
    .p_data_width( p_data_width   ),
    .p_nstages   ( c_sync_nstages )
  ) enq_ptr_sync (
    .clk      ( r_clk        ),
    .data_in  ( enq_ptr      ),
    .data_out ( sync_enq_ptr )
  );

  synchronizer #(
    .p_data_width( 1              ),
    .p_nstages   ( c_sync_nstages )
  ) enq_wrapbit_sync (
    .clk      ( r_clk            ),
    .data_in  ( enq_wrapbit      ),
    .data_out ( sync_enq_wrapbit )
  );

  // TODO: gray code encoder -> synchronizer -> decoder

  synchronizer #(
    .p_data_width( p_data_width   ),
    .p_nstages   ( c_sync_nstages )
  ) deq_ptr_sync (
    .clk      ( w_clk        ),
    .data_in  ( deq_ptr      ),
    .data_out ( sync_deq_ptr )
  );

  synchronizer #(
    .p_data_width( 1              ),
    .p_nstages   ( c_sync_nstages )
  ) deq_wrapbit_sync (
    .clk      ( waQQ_clk            ),
    .data_in  ( deq_wrapbit      ),
    .data_out ( sync_deq_wrapbit )
  );

  // Enq, clocked with the writer clock

  always @ ( posedge w_clk ) begin
    if ( enq_en ) begin
      mem[ enq_ptr ] <= enq_msg;
    end
  end

  // Deq are synchronous with the reader clock

  assign deq_msg = mem[ deq_ptr ];

endmodule