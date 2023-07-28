//========================================================================
// gray_encoder.v
//========================================================================
// A binary to gray code encoder.
//
// Author : Yanghui Ou
//   Date : July 28, 2019

module gray_encoder #(
  parameter p_width = 4 // we only support width that is power of 2!
)(
  input  logic [p_width-1:0] data_in,
  output logic [p_width-1:0] data_out
);

genvar i;
generate

  for ( i=0; i < p_width-1; i=i+1 ) begin
    assign  data_out[i] = data_in[i+1] ^ data_in[i];
  end
  assign data_out[p_width-1] = data_in[p_width-1];

endgenerate

endmodule