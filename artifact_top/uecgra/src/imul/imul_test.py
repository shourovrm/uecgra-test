import random
from pymtl import *
from pclib.rtl import TestSourceValRdy, TestSinkValRdy
from pclib.ifcs import InValRdyIfc, OutValRdyIfc
from IntMul import IntMul

class TestHarness( Component ):

  def construct( s, model, src_msgs, sink_msgs ):

    s.src  = TestSourceValRdy( Bits128, src_msgs )
    s.sink = TestSinkValRdy( Bits64, sink_msgs )

    s.imul = model( req = s.src.out, resp = s.sink.in_ )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.imul.line_trace()+" >>> "+s.sink.line_trace()

random.seed(0xdeadbeef)
src_msgs  = []
sink_msgs = []

for i in xrange(20):
  x = random.randint(0, 2**62)
  y = random.randint(0, 2**62)
  z = Bits128(0)
  z[0:64]  = x
  z[64:128] = y
  src_msgs.append( z )
  sink_msgs.append( Bits64( x * y ) )

# The additional message is to discriminate fixed/variable latency
src_msgs.append( Bits128(0x10101010101010101010101010101010) )
sink_msgs.append( Bits64(0x0706050403020100L) )

def run_test( model, num_msgs ):
  th = TestHarness( model, src_msgs[-num_msgs:], sink_msgs[-num_msgs:] )
  th.apply( SimpleSim )
  T, maxT = 0, 5000

  print
  while not th.done():
    th.tick()
    print th.line_trace()
    T += 1
    assert T < maxT

import pytest

@pytest.mark.parametrize(
    "mode,    num_msgs", [
  ( "varlat", 2 ),
  ( "normal", 2 ),
  ( "varlat", 20 ),
  ( "normal", 20 ),
])
def test_imul( mode, num_msgs ):
  run_test( IntMul(64, mode), num_msgs )
