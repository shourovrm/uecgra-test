from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL
from pymtl3.passes.sverilog import TranslationPass

try:
  # Check if PYTHONPATH has been set up
  import mul_q
except:
  # Hack to add the src directory of rgals-src to PYTHONPATH
  import os, sys
  cur_dir = os.path.dirname(os.path.abspath(__file__))
  while cur_dir and not os.path.isfile(f"{cur_dir}/conftest.py"):
    cur_dir = os.path.dirname(cur_dir)
  sys.path.insert(0, cur_dir)

from mul_q.Mul import Mul
from acc_q.Acc import Acc

class MACSync( Component ):
  def construct( s, p_width = 8 ):
    s.clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.recv = RecvIfcRTL( mk_bits( p_width*2 ) )
    s.send = SendIfcRTL( mk_bits( p_width ) )

    s.mul = Mul( mk_bits(p_width), ncycles = 3 )
    s.acc = Acc( mk_bits(p_width), nmsgs = 4 )

    s.clk //= s.mul.clk
    s.reset //= s.mul.reset
    s.clk //= s.acc.clk
    s.reset //= s.acc.reset

    s.recv //= s.mul.recv
    s.mul.send //= s.acc.recv
    s.acc.send //= s.send

  def line_trace( s ):
    return f"{s.recv}(M:{s.mul.line_trace()})>(A:{s.acc.line_trace()}){s.send}"

if __name__ == "__main__":
  dut = MACSync()
  dut.elaborate()
  dut.sverilog_translate = True
  dut.apply( TranslationPass() )
