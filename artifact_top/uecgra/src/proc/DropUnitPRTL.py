#=======================================================================
# DropUnit.py
#=======================================================================

from pymtl3      import *
from pymtl3.stdlib.ifcs import InValRdyIfc, OutValRdyIfc
from pymtl3.stdlib.rtl  import RegRst

# State Constants

SNOOP = Bits1(0)
WAIT  = Bits1(1)

#-------------------------------------------------------------------------
# DropUnit
#-------------------------------------------------------------------------
# Drop Unit drops a transaction between any two models connected by
# using the val-rdy handshake protocol. It receives a drop signal as an
# input and if the drop signal is high, it will drop the next message
# it sees.

class DropUnitPRTL( Component ):

  def construct( s, Type ):

    s.drop = InPort     ( Bits1 )
    s.in_  = InValRdyIfc ( Type )
    s.out  = OutValRdyIfc( Type )
    connect( s.in_.msg, s.out.msg )

    s.snoop_state = RegRst( Bits1, reset_value=0 )

    @s.update
    def state_transitions():
      curr_state = s.snoop_state.out

      s.snoop_state.in_ = curr_state

      if s.snoop_state.out == SNOOP:
        # we wait if we haven't received the response yet
        if s.drop & (~s.out.rdy | ~s.in_.val):
          s.snoop_state.in_ = WAIT

      elif s.snoop_state.out == WAIT:
        # we are done waiting if the response arrives
        if s.in_.val:
          s.snoop_state.in_ = SNOOP

    # Shunning: this doesn't work ... because the scheduler sees in_.val
    # depends on in_.rdy
    # @s.update
    # def state_outputs():

      # if   s.snoop_state.out == SNOOP:
        # s.out.val = s.in_.val & ~s.drop
        # s.in_.rdy = s.out.rdy

      # elif s.snoop_state.out == WAIT:
        # s.out.val = Bits1(0)
        # s.in_.rdy = Bits1(1)

    @s.update
    def state_output_val():
      if   s.snoop_state.out == SNOOP:
        s.out.val = s.in_.val & ~s.drop

      elif s.snoop_state.out == WAIT:
        s.out.val = Bits1(0)

    @s.update
    def state_output_rdy():
      if   s.snoop_state.out == SNOOP:
        s.in_.rdy = s.out.rdy

      elif s.snoop_state.out == WAIT:
        s.in_.rdy = Bits1(1)
