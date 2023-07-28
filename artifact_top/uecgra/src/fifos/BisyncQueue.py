#=========================================================================
# BisyncQueue.py
#=========================================================================
# A bisynchronous normal queue that wraps its Verilog implementation.
#
# Author : Peitian Pan
# Date   : Aug 13, 2019

from pymtl3 import *
from pymtl3.dsl import Placeholder
from pymtl3.stdlib.rtl import RegRst
from pymtl3.stdlib.rtl.queues import NormalQueueRTL
from pymtl3.stdlib.ifcs import EnqIfcRTL, DeqIfcRTL
from pymtl3.passes.sverilog import TranslationConfigs
from misc.adapters import EnRdy2ValRdy

class BisynchronousNormalQueue( Placeholder, Component ):
  # taken as a blackbox during translation
  def construct( s, p_data_width = 32, p_num_entries = 8, p_fifo_latency = 0 ):
    DataType = mk_bits( p_data_width )
    s.w_clk = InPort( Bits1 )
    s.r_clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.w_val = InPort( Bits1 )
    s.w_rdy = OutPort( Bits1 )
    s.w_msg = InPort( DataType )
    s.r_val = OutPort( Bits1 )
    s.r_rdy = InPort( Bits1 )
    s.r_msg = OutPort( DataType )
    s.sverilog_translate = TranslationConfigs(
      v_src = "$RGALS_TOP/src/fifos/BisynchronousNormalQueue.v",
    )
    s.yosys_translate = TranslationConfigs(
      v_src = "$RGALS_TOP/src/fifos/BisynchronousNormalQueue.v",
    )

class BisyncQueue( Component ):

  def construct( s, Type, num_entries = 2, fifo_latency = 0 ):

    s.w_clk = InPort( Bits1 )
    s.r_clk = InPort( Bits1 )
    s.reset = InPort( Bits1 )
    s.enq = EnqIfcRTL( Type )
    s.deq = DeqIfcRTL( Type )

    # Is the queue emtpy?
    s.is_empty = OutPort( Bits1 )

    # Does the queue have exactly 1 element and deq is about to go?
    s.is_empty_next = OutPort( Bits1 )

    # Wire

    # NOTE: since we are only using 2-entry queues it is possible to infer
    # the number of elements in the queue without adding more ports.
    # If q.r_val then q has 1 or 2 elements. If q.w_rdy then q has 1 or 0 elements.
    # If q.r_val & q.w_rdy then q has 1 element.
    s.is_one_element = Wire( Bits1 )

    @s.update
    def one_element():
      s.is_one_element = s.deq.rdy and s.enq.rdy

    @s.update
    def empty():
      s.is_empty = not s.deq.rdy

    @s.update
    def empty_next():
      s.is_empty_next = s.is_one_element and s.deq.en

    s.q = BisynchronousNormalQueue( Type.nbits, num_entries, fifo_latency )

    s.q.w_clk //= s.w_clk
    s.q.r_clk //= s.r_clk
    s.q.reset //= s.reset

    s.q_adapter_in = EnRdy2ValRdy( Type )
    s.enq //= s.q_adapter_in.in_
    s.q.w_val //= s.q_adapter_in.out.val
    s.q.w_rdy //= s.q_adapter_in.out.rdy
    s.q.w_msg //= s.q_adapter_in.out.msg

    s.deq.en  //= s.q.r_rdy
    s.deq.rdy //= s.q.r_val
    s.deq.msg //= s.q.r_msg
