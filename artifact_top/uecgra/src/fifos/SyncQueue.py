from pymtl3 import *
from pymtl3.stdlib.ifcs import EnqIfcRTL, DeqIfcRTL
from pymtl3.stdlib.rtl.queues import NormalQueueRTL

class SyncQueue( Component ):

  def construct( s, Type, num_entries=2 ):

    s.r_clk = InPort( Bits1 )
    s.w_clk = InPort( Bits1 )
    s.enq   = EnqIfcRTL( Type )
    s.deq   = DeqIfcRTL( Type )

    s.q = NormalQueueRTL( Type, num_entries )

    connect( s.enq, s.q.enq )
    connect( s.deq, s.q.deq )

  def line_trace( s ):
    return s.q.line_trace()
