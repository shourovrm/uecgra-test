from pymtl3 import *
from pymtl3.dsl import Placeholder
from pymtl3.datatypes import concat
from pymtl3.passes.sverilog.util.utility import get_dir
from pymtl3.passes.sverilog import ImportConfigs, ImportPass

class MACRgals( Placeholder, Component ):
  def construct( s, p_width = 8 ):
    DataType = mk_bits( 2*p_width )
    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.mul_clksel_val = InPort( Bits1 )
    s.mul_clksel_rdy = OutPort( Bits1 )
    s.mul_clksel_msg = InPort( Bits1 )
    s.accum_clksel_val = InPort( Bits1 )
    s.accum_clksel_rdy = OutPort( Bits1 )
    s.accum_clksel_msg = InPort( Bits1 )
    s.req_val = InPort( Bits1 )
    s.req_rdy = OutPort( Bits1 )
    s.req_msg = InPort( DataType )
    s.resp_val = OutPort( Bits1 )
    s.resp_rdy = InPort( Bits1 )
    s.resp_msg = OutPort( DataType )
    s.sverilog_import = ImportConfigs(
      verbose = True,
      top_module = "mac_rgals",
      vl_trace = True,
      vl_src = f"{get_dir(__file__)}/mac-rgals.v",
      vl_flist = f"{get_dir(__file__)}/flist.vl",
      vl_Wno_list = ['WIDTH'],
    )

if __name__ == "__main__":
  dut = MACRgals()
  dut.elaborate()
  dut = ImportPass()( dut )
  dut.elaborate()
  dut.apply( SimulationPass )
  dut.reset = b1(1)
  dut.clk_reset = b1(1)
  dut.tick()
  print("-----")
  dut.tick()
  print("-----")

  dut.clk_reset = b1(0)
  dut.mul_clksel_val = b1(1)
  dut.mul_clksel_msg = b1(0)
  dut.accum_clksel_val = b1(1)
  dut.accum_clksel_msg = b1(1)

  for i in range(10):
    dut.tick()
    print("-----")

  dut.mul_clksel_val = b1(0)
  dut.accum_clksel_val = b1(0)
  dut.tick()
  print("-----")

  dut.reset =b1(0)
  dut.tick()
  print("-----")

  dut.resp_rdy = b1(1)
  dut.req_val = b1(0)
  if dut.req_rdy == b1(1):
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
  while dut.req_rdy != b1(1):
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
  dut.req_val = b1(1)
  dut.req_msg = concat( b8(1), b8(2) )
  print(dut.internal_line_trace())
  dut.tick()
  print("-----")

  dut.req_val = b1(0)
  if dut.req_rdy == b1(1):
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")

  while dut.req_rdy != b1(1):
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
  dut.req_val = b1(1)
  dut.req_msg = concat( b8(3), b8(4) )
  print(dut.internal_line_trace())
  dut.tick()
  print("-----")
  dut.req_val = b1(0)

  dut.req_val = b1(0)
  if dut.req_rdy == b1(1):
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
  while dut.req_rdy != b1(1):
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
  dut.req_val = b1(1)
  dut.req_msg = concat( b8(5), b8(6) )
  print(dut.internal_line_trace())
  dut.tick()
  print("-----")

  dut.req_val = b1(0)
  if dut.req_rdy == b1(1):
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
  while dut.req_rdy != b1(1):
    print(dut.internal_line_trace())
    dut.tick()
    print("-----")
  dut.req_val = b1(1)
  dut.req_msg = concat( b8(7), b8(8) )
  print(dut.internal_line_trace())

  for i in range(50):
    dut.tick()
    print("-----")
    dut.req_val = b1(0)
    print(dut.internal_line_trace())
