#=========================================================================
# unsafe_gen.py
#=========================================================================
# Clock ratio-specific unsafe signal generators.
#
# Author : Peitian Pan
# Date   : Aug 22, 2019

from pymtl3 import *
from pymtl3.datatypes import concat

from clock.enums import *
from clock.clock_counter import ClockCounter
from crossing.enums import *

class FastNominalUnsafeGen( Component ):
  def construct( s ):
    # Assume fast : nominal = 2 : 3
    s.w_clk = InPort( Bits1 )
    s.r_clk = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.unsafe = OutPort( Bits1 )

    # s.w_cnt = Wire( Bits2 ) # count to 3
    # s.r_cnt = Wire( Bits1 ) # count to 2

    # s.w_counter = ClockCounter(count_to=3, nbits=2)(
      # clk = s.w_clk,
      # clk_reset = s.clk_reset,
      # clk_cnt = s.w_cnt,
    # )
    # s.r_counter = ClockCounter(count_to=2, nbits=1)(
      # clk = s.r_clk,
      # clk_reset = s.clk_reset,
      # clk_cnt = s.r_cnt,
    # )

    @s.update
    def upblk():
      s.unsafe = b1(1)
      # s.unsafe = ((s.w_cnt == b2(1)) and (s.r_cnt == b1(0))) or \
                 # ((s.w_cnt == b2(2)) and (s.r_cnt == b1(1)))

class FastSlowUnsafeGen( Component ):
  def construct( s ):
    # Assume fast : slow = 2 : 9
    s.w_clk = InPort( Bits1 )
    s.r_clk = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.unsafe = OutPort( Bits1 )

    # s.w_cnt = Wire( Bits4 ) # count to 9
    # s.r_cnt = Wire( Bits1 ) # count to 2

    # s.w_counter = ClockCounter(count_to=9, nbits=4)(
      # clk = s.w_clk,
      # clk_reset = s.clk_reset,
      # clk_cnt = s.w_cnt,
    # )
    # s.r_counter = ClockCounter(count_to=2, nbits=1)(
      # clk = s.r_clk,
      # clk_reset = s.clk_reset,
      # clk_cnt = s.r_cnt,
    # )

    @s.update
    def upblk():
      s.unsafe = b1(1)
      # s.unsafe = \
          # ((s.r_cnt == b1(0)) and \
              # ((s.w_cnt == b4(1)) or (s.w_cnt == b4(2)) or \
               # (s.w_cnt == b4(3)) or (s.w_cnt == b4(4)))) or \
          # ((s.r_cnt == b1(1)) and \
              # ((s.w_cnt == b4(5)) or (s.w_cnt == b4(6)) or \
               # (s.w_cnt == b4(7)) or (s.w_cnt == b4(8))))

class NominalFastUnsafeGen( Component ):
  def construct( s ):
    # Assume nominal : fast = 3 : 2
    s.w_clk = InPort( Bits1 )
    s.r_clk = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.unsafe = OutPort( Bits1 )

    # s.w_cnt = Wire( Bits1 ) # count to 2
    s.r_cnt = Wire( Bits2 ) # count to 3

    # s.w_counter = ClockCounter(count_to=2, nbits=1)(
      # clk = s.w_clk,
      # clk_reset = s.clk_reset,
      # clk_cnt = s.w_cnt,
    # )
    s.r_counter = ClockCounter(count_to=3, nbits=2)(
      clk = s.r_clk,
      clk_reset = s.clk_reset,
      clk_cnt = s.r_cnt,
    )

    @s.update
    def upblk():
      s.unsafe = (s.r_cnt == b2(1))
      # s.unsafe = (s.w_cnt == b1(1)) and (s.r_cnt == b2(1))

class NominalSlowUnsafeGen( Component ):
  def construct( s ):
    # Assume nominal : slow = 3 : 9
    s.w_clk = InPort( Bits1 )
    s.r_clk = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.unsafe = OutPort( Bits1 )

    # s.w_cnt = Wire( Bits2 ) # count to 3
    # s.r_cnt = Wire( Bits1 ) # count to 1, always 0

    # s.w_counter = ClockCounter(count_to=3, nbits=2)(
      # clk = s.w_clk,
      # clk_reset = s.clk_reset,
      # clk_cnt = s.w_cnt,
    # )

    @s.update
    def upblk():
      s.unsafe = b1(1)
      # s.unsafe = (s.w_cnt == b2(1)) or (s.w_cnt == b2(2))

class SlowFastUnsafeGen( Component ):
  def construct( s ):
    # Assume slow : fast = 9 : 2
    s.w_clk = InPort( Bits1 )
    s.r_clk = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.unsafe = OutPort( Bits1 )

    # s.w_cnt = Wire( Bits1 ) # count to 2
    s.r_cnt = Wire( Bits4 ) # count to 9

    # s.w_counter = ClockCounter(count_to=2, nbits=1)(
      # clk = s.w_clk,
      # clk_reset = s.clk_reset,
      # clk_cnt = s.w_cnt,
    # )
    s.r_counter = ClockCounter(count_to=9, nbits=4)(
      clk = s.r_clk,
      clk_reset = s.clk_reset,
      clk_cnt = s.r_cnt,
    )

    @s.update
    def upblk():
      s.unsafe = s.r_cnt == b4(4)
      # s.unsafe = (s.w_cnt == b1(1)) and (s.r_cnt == b4(4))

class UnsafeCrossingGen( Component ):
  def construct( s ):
    s.clk1 = InPort( Bits1 )
    s.clk2 = InPort( Bits1 )
    s.clk3 = InPort( Bits1 )
    s.clk_reset = InPort( Bits1 )
    s.unsafe_bus = OutPort( Bits9 )

    s.fast_slow = FastSlowUnsafeGen()(
      w_clk = s.clk1,
      r_clk = s.clk2,
      clk_reset = s.clk_reset,
    )
    s.fast_nomi = FastNominalUnsafeGen()(
      w_clk = s.clk1,
      r_clk = s.clk3,
      clk_reset = s.clk_reset,
    )
    s.slow_fast = SlowFastUnsafeGen()(
      w_clk = s.clk2,
      r_clk = s.clk1,
      clk_reset = s.clk_reset,
    )
    s.nomi_fast = NominalFastUnsafeGen()(
      w_clk = s.clk3,
      r_clk = s.clk1,
      clk_reset = s.clk_reset,
    )
    s.nomi_slow = NominalSlowUnsafeGen()(
      w_clk = s.clk3,
      r_clk = s.clk2,
      clk_reset = s.clk_reset,
    )

    @s.update
    def unsafe_bus_connect():
      s.unsafe_bus = concat(
        b1(0), s.nomi_slow.unsafe, s.nomi_fast.unsafe, b1(0), b1(0),
        s.slow_fast.unsafe, s.fast_nomi.unsafe, s.fast_slow.unsafe, b1(0),
      )
      # s.unsafe_bus[SEL_FAST_FAST]       = b1(0)
      # s.unsafe_bus[SEL_FAST_SLOW]       = s.fast_slow.unsafe
      # s.unsafe_bus[SEL_FAST_NOMINAL]    = s.fast_nomi.unsafe
      # s.unsafe_bus[SEL_SLOW_FAST]       = s.slow_fast.unsafe
      # s.unsafe_bus[SEL_SLOW_SLOW]       = b1(0)
      # s.unsafe_bus[SEL_SLOW_NOMINAL]    = b1(0)
      # s.unsafe_bus[SEL_NOMINAL_FAST]    = s.nomi_fast.unsafe
      # s.unsafe_bus[SEL_NOMINAL_SLOW]    = s.nomi_slow.unsafe
      # s.unsafe_bus[SEL_NOMINAL_NOMINAL] = b1(0)
