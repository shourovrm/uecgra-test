#=========================================================================
# errors.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Provide exception types for translation errors."""

import sys
import traceback


class RTLIRTranslationError( Exception ):
  """Exception type for errors happening during translation of RTLIR."""
  def __init__( self, obj, msg ):
    obj = str(obj)
    _, _, tb = sys.exc_info()
    traceback.print_tb(tb)
    tb_info = traceback.extract_tb(tb)
    fname, line, func, text = tb_info[-1]
    return super().__init__(
      "\nIn file {fname}, Line {line}, Method {func}:"
      "\nError trying to translate top component {obj}:\n- {msg}"
      "\n  {text}".format( **locals() ) )
