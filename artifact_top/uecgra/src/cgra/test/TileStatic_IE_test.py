"""
==========================================================================
TileStatic_IE_test.py
==========================================================================
Test cases for static inelastic CGRA tile.

Author : Yanghui Ou
  Date : August 9, 2019

"""
from pymtl3 import *
from pymtl3.passes.yosys import TranslationPass

from ..ConfigMsg import ConfigMsg
from ..TileStatic import TileStatic

#-------------------------------------------------------------------------
# Transaltion
#-------------------------------------------------------------------------

class TileStatic_IE_Tests:

  def test_translation( s ):
    dut = TileStatic( Bits32, ConfigMsg, 0, "inelastic" )
    dut.elaborate()
    dut.yosys_translate = True
    dut.apply( TranslationPass() )
