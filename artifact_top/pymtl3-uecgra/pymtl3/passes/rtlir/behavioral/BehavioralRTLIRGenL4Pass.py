#=========================================================================
# BehavioralRTLIRGenL4Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 20, 2018
"""Provide L4 behavioral RTLIR generation pass."""

from pymtl3.passes.BasePass import BasePass, PassMetadata

from .BehavioralRTLIRGenL3Pass import BehavioralRTLIRGeneratorL3


class BehavioralRTLIRGenL4Pass( BasePass ):

  def __call__( s, m ):
    """ generate RTLIR for all upblks of m """
    if not hasattr( m, '_pass_behavioral_rtlir_gen' ):
      m._pass_behavioral_rtlir_gen = PassMetadata()
    m._pass_behavioral_rtlir_gen.rtlir_upblks = {}
    visitor = BehavioralRTLIRGeneratorL4( m )
    upblks = {
      'CombUpblk' : list(m.get_update_blocks() - m.get_update_on_edge()),
      'SeqUpblk'  : list(m.get_update_on_edge())
    }
    # Sort the upblks by their name
    upblks['CombUpblk'].sort( key = lambda x: x.__name__ )
    upblks['SeqUpblk'].sort( key = lambda x: x.__name__ )

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:
        visitor._upblk_type = upblk_type
        m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] = \
          visitor.enter( blk, m.get_update_block_ast( blk ) )

class BehavioralRTLIRGeneratorL4( BehavioralRTLIRGeneratorL3 ):
  """Behavioral RTLIR generator level 4.

  Do nothing here because attributes have been handled in previous
  levels.
  """
  def __init__( s, component ):
    super().__init__( component )
