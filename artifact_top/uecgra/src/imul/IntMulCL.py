from pymtl import *
from pclib.ifcs   import guarded_ifc, GuardedCallerIfc

class IntMulCL( Component ):

  def construct( s, latency=1 ):
    s.latency = latency
    s.send    = GuardedCallerIfc()

    s.entry = None
    s.countdown = 0

    @s.update
    def up_mul_cl():
      if s.countdown == 0:
        if s.entry is not None and s.send.rdy():
          s.send( s.entry.a * s.entry.b )
          s.entry = None
      else:
        s.countdown -= 1

    s.add_constraints( M(s.recv) < U(up_mul_cl) )

  @guarded_ifc( lambda s: s.entry is None )
  def recv( s, v ):
    s.entry     = v
    s.countdown = s.latency

  def line_trace( s ):
    return ""
