"""
==========================================================================
ConfigMsg_RGALS.py
==========================================================================
Bit struct for RGALS CGRA configuration messages.

Author : Yanghui Ou, Peitian Pan
  Date : Aug 7, 2019

"""
from pymtl3 import *

#-------------------------------------------------------------------------
# ConfigMsg
#-------------------------------------------------------------------------
# Format:
# - Q type: for normal operation
#     operands only comes from input queues or the general purpose
#     register.
# - B type: for branch
#     src_opd_a is used for data input and src_opd_b is used for condition
#     input. func is used for destination when the condition is false and
#     dst_compute is used for configuring destination when condition is
#     true.
# - I type: for initialize the constant
#     all fields except opcode are concated to form the 24-bit immediate.

ConfigMsg_RGALS = mk_bit_struct( 'ConfigMsg_RGALS', [
  ('opcode',      Bits2 ),
  ('func',        Bits5 ),
  ('src_opd_a',   Bits3 ),
  ('src_opd_b',   Bits3 ),
  ('dst_compute', Bits5 ),
  ('src_bypass',  Bits3 ),
  ('dst_bypass',  Bits5 ),
  ('src_altbps',  Bits3 ),
  ('dst_altbps',  Bits5 ),
  ('clk_self',    Bits2 ),
])
