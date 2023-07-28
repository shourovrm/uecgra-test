//========================================================================
// gray_decoder.v
//========================================================================
// A gray code to binary decoder.
//
// Author : Yanghui Ou
//   Date : July 28, 2019
//

module gray_decoder # (
  parameter p_width = 4 // we only support width that is power of 2!
)(
  input  logic [p_width-1:0] data_in,
  output logic [p_width-1:0] data_out
);

genvar i;
generate

  for ( i=0; i < p_width; i=i+1 ) begin
    assign  data_out[i] = ^data_in[p_width-1:i];
  end

endgenerate

endmodule