#=========================================================================
# ImportPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 14, 2019
"""Provide a pass that imports arbitrary SystemVerilog modules."""


from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import get_component_ifc_rtlir
from pymtl3.passes.sverilog import ImportConfigs
from pymtl3.passes.sverilog import ImportPass as SVerilogImportPass
from pymtl3.passes.sverilog.errors import SVerilogImportError
from pymtl3.passes.sverilog.util.utility import get_component_unique_name, make_indent


class ImportPass( SVerilogImportPass ):

  #-----------------------------------------------------------------------
  # Backend-specific methods
  #-----------------------------------------------------------------------

  def get_backend_name( s ):
    return "yosys"

  def get_config( s, m ):
    return m.yosys_import

  def get_translation_namespace( s, m ):
    return m._pass_yosys_translation

  #-------------------------------------------------------------------------
  # Name mangling functions
  #-------------------------------------------------------------------------

  def mangle_vector( s, d, id_, dtype ):
    return [ ( id_, rt.Port( d, dtype ) ) ]

  def mangle_struct( s, d, id_, dtype ):
    ret = []
    all_properties = dtype.get_all_properties()
    for name, field in all_properties:
      ret += s.mangle_dtype( d, id_+"__"+name, field )
    return ret

  def mangle_packed_array( s, d, id_, dtype ):

    def _mangle_packed_array( d, id_, dtype, n_dim ):
      if not n_dim:
        return s.mangle_dtype( d, id_, dtype )
      else:
        ret = []
        for i in range( n_dim[0] ):
          ret += _mangle_packed_array( d, id_+"__"+str(i), dtype, n_dim[1:] )
        return ret

    n_dim, sub_dtype = dtype.get_dim_sizes(), dtype.get_sub_dtype()
    return _mangle_packed_array( d, id_, sub_dtype, n_dim )

  def mangle_dtype( s, d, id_, dtype ):
    if isinstance( dtype, rdt.Vector ):
      return s.mangle_vector( d, id_, dtype )
    elif isinstance( dtype, rdt.Struct ):
      return s.mangle_struct( d, id_, dtype )
    elif isinstance( dtype, rdt.PackedArray ):
      return s.mangle_packed_array( d, id_, dtype )
    else:
      assert False, "unrecognized data type {}!".format( dtype )

  def mangle_port( s, id_, port, n_dim ):
    if not n_dim:
      return s.mangle_dtype( port.get_direction(), id_, port.get_dtype() )
    else:
      ret = []
      for i in range( n_dim[0] ):
        ret += s.mangle_port( id_+"__"+str(i), port, n_dim[1:] )
      return ret

  #-------------------------------------------------------------------------
  # Python signal connections generation functions
  #-------------------------------------------------------------------------

  def gen_vector_conns( s, d, lhs, rhs, dtype, pos ):
    nbits = dtype.get_length()
    _lhs, _rhs = s._verilator_name(lhs), s._verilator_name(rhs)
    ret = ["connect( s.{_lhs}, s.mangled__{_rhs} )".format(**locals())]
    return ret, pos + nbits

  def gen_struct_conns( s, d, lhs, rhs, dtype, pos ):
    dtype_name = dtype.get_class().__name__
    upblk_name = lhs.replace('.', '_DOT_').replace('[', '_LBR_').replace(']', '_RBR_')
    ret = [
      "@s.update",
      "def " + upblk_name + "():",
    ]
    if d == "output":
      ret.append( "  s.{lhs} = {dtype_name}()".format( **locals() ) )
    body = []
    all_properties = reversed(dtype.get_all_properties())
    for name, field in all_properties:
      # Use upblk to generate assignment to a struct port
      _ret, pos = s._gen_dtype_conns( d, lhs+"."+name, rhs+"__"+name, field, pos )
      body += _ret
    return ret + body, pos

  def _gen_vector_conns( s, d, lhs, rhs, dtype, pos ):
    nbits = dtype.get_length()
    l, r = pos, pos+nbits
    _lhs, _rhs = s._verilator_name( lhs ), s._verilator_name( rhs )
    if d == "input":
      ret = ["  s.mangled__{_rhs} = s.{_lhs}".format( **locals() )]
    else:
      ret = ["  s.{_lhs} = s.mangled__{_rhs}".format( **locals() )]
    return ret, r

  def _gen_struct_conns( s, d, lhs, rhs, dtype, pos ):
    ret = []
    all_properties = reversed(dtype.get_all_properties())
    for name, field in all_properties:
      _ret, pos = s._gen_dtype_conns(d, lhs+"."+name, rhs+"__"+name, field, pos)
      ret += _ret
    return ret, pos

  def _gen_packed_array_conns( s, d, lhs, rhs, dtype, n_dim, pos ):
    if not n_dim:
      return s._gen_dtype_conns( d, lhs, rhs, dtype, pos )
    else:
      ret = []
      for idx in range(n_dim[0]):
        _lhs = lhs + "[{idx}]".format( **locals() )
        _rhs = rhs + "__{idx}".format( **locals() )
        _ret, pos = \
          s._gen_packed_array_conns( d, _lhs, _rhs, dtype, n_dim[1:], pos )
        ret += _ret
      return ret, pos

  def gen_port_conns( s, id_py, id_v, port, n_dim ):
    if not n_dim:
      d = port.get_direction()
      dtype = port.get_dtype()
      nbits = dtype.get_length()
      ret, pos = s.gen_dtype_conns( d, id_py, id_v, dtype, 0 )
      assert pos == nbits, \
        "internal error: {} wire length mismatch!".format( id_py )
      return ret
    else:
      ret = []
      for idx in range(n_dim[0]):
        _id_py = id_py + "[{idx}]".format( **locals() )
        _id_v = id_v + "__{idx}".format( **locals() )
        ret += s.gen_port_conns( _id_py, _id_v, port, n_dim[1:] )
      return ret

  #-------------------------------------------------------------------------
  # PyMTL combinational input and output generation functions
  #-------------------------------------------------------------------------

  def gen_dtype_comb( s, lhs, rhs, dtype, is_input ):

    def _gen_packed_comb( lhs, rhs, dtype, n_dim, is_input ):
      if not n_dim:
        return s.gen_dtype_comb( lhs, rhs, dtype, is_input )
      else:
        ret = []
        for i in range( n_dim[0] ):
          if is_input:
            _lhs = lhs + "__" + str(i)
            _rhs = rhs + "[{i}]".format( **locals() )
          else:
            _lhs = lhs + "[{i}]".format( **loacls() )
            _rhs = rhs + "__" + str(i)
          ret += _gen_packed_comb( _lhs, _rhs, dtype, n_dim[1:] )
        return ret

    if isinstance( dtype, rdt.Vector ):
      nbits = dtype.get_length()
      if is_input:
        return s._gen_ref_write( lhs, rhs, nbits )
      else:
        return s._gen_ref_read( lhs, rhs, nbits )
    elif isinstance( dtype, rdt.Struct ):
      ret = []
      all_properties = dtype.get_all_properties()
      for name, field in all_properties:
        if is_input:
          _lhs = lhs + "__" + name
          _rhs = rhs + "." + name
        else:
          _lhs = lhs + "." + name
          _rhs = rhs + "__" + name
        ret += s.gen_dtype_comb( _lhs, _rhs, field )
      return ret
    elif isinstance( dtype, rdt.PackedArray ):
      n_dim = dtype.get_dim_sizes()
      sub_dtype = dtype.get_sub_dtype()
      return _gen_packed_comb( lhs, rhs, sub_dtype, n_dim, is_input )
    else:
      assert False, "unrecognized data type {}!".format( dtype )

  def gen_port_array_input( s, lhs, rhs, dtype, n_dim ):
    if not n_dim:
      return s.gen_dtype_comb( lhs, rhs, dtype, is_input = True )
    else:
      ret = []
      for i in range( n_dim[0] ):
        _lhs = lhs + "__{i}".format( **locals() )
        _rhs = rhs + "[{i}]".format( **locals() )
        ret += s.gen_port_array_input( _lhs, _rhs, dtype, n_dim[1:] )
      return ret

  def gen_port_array_output( s, lhs, rhs, dtype, n_dim ):
    if not n_dim:
      return s.gen_dtype_comb( lhs, rhs, dtype, is_input = False )
    else:
      ret = []
      for i in range( n_dim[0] ):
        _lhs = lhs + "[{i}]".format( **locals() )
        _rhs = rhs + "__{i}".format( **locals() )
        ret += s.gen_port_array_output( _lhs, _rhs, dtype, n_dim[1:] )
      return ret

  #-------------------------------------------------------------------------
  # PyMTL wrapper constraint generation function
  #-------------------------------------------------------------------------

  def _gen_constraints( s, name, n_dim, rtype ):
    if not n_dim:
      return ["U( seq_upblk ) < RD( {} ),".format("s.mangled__"+name)]
    else:
      ret = []
      for i in range( n_dim[0] ):
        ret += s._gen_constraints( name+"__"+str(i), n_dim[1:], rtype )
      return ret
