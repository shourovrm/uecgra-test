import random
from pymtl import *
from pclib.test import TestSrcCL, TestSinkCL
from pymtl.passes import SimpleCLSim

from IntMulCL import IntMulCL

class TestHarness( Component ):

  def construct( s, cls, src_msgs, sink_msgs ):

    s.src  = TestSrcCL( src_msgs )
    s.sink = TestSinkCL( sink_msgs )

    s.imul = cls(2)( recv = s.src.send, send = s.sink.recv )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.imul.line_trace()+" >>> "+s.sink.line_trace()

random.seed(0xdeadbeef)
src_msgs  = []
sink_msgs = []


class MulMsg(object):
  def __init__( s, a=0, b=0 ):
    s.a = a
    s.b = b
  def __str__( s ):
    return "{}*{}".format(s.a, s.b)

for i in xrange(20):
  x = random.randint(0, 2**3)
  y = random.randint(0, 2**3)
  src_msgs.append( MulMsg( Bits64(x), Bits64(y) ) )
  sink_msgs.append( Bits64( x*y ) )

def run_test( cls, num_msgs ):
  th = TestHarness( cls, src_msgs[-num_msgs:], sink_msgs[-num_msgs:] )
  th.apply( SimpleCLSim )
  T, maxT = 0, 5000

  print
  while not th.done():
    th.tick()
    print th.line_trace()
    T += 1
    assert T < maxT

import pytest

@pytest.mark.parametrize(
    "num_msgs", [
  (  2 ),
  (  20 ),
])
def test_imul( num_msgs ):
  run_test( IntMulCL, num_msgs )
