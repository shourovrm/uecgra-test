"""
==========================================================================
AluMsg.py
==========================================================================
Bit struct for two operands.

Author : Yanghui Ou
  Date : Aug 23, 2019

"""
from pymtl3 import *

def mk_alu_msg( Type ):
  cls_name = f'AluMsg_{Type.nbits}'
  return mk_bit_struct( cls_name, [
    ( 'opd_a', Type ),
    ( 'opd_b', Type ),
  ])