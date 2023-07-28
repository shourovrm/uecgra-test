from pymtl3 import *
from collections import deque
from pymtl3.stdlib.ifcs import InValRdyIfc, OutValRdyIfc
from pymtl3.stdlib.rtl.valrdy_queues  import PipeQueue1RTL

TYPE_READ       = 0
TYPE_WRITE      = 1
# write no-refill
TYPE_WRITE_INIT = 2
TYPE_AMO_ADD    = 3
TYPE_AMO_AND    = 4
TYPE_AMO_OR     = 5
TYPE_AMO_XCHG   = 6
TYPE_AMO_MIN    = 7

AMO_FUNS = { TYPE_AMO_ADD  : lambda m,a : m+a,
             TYPE_AMO_AND  : lambda m,a : m&a,
             TYPE_AMO_OR   : lambda m,a : m|a,
             TYPE_AMO_XCHG : lambda m,a : a,
             TYPE_AMO_MIN  : min,
           }

class TestMemory( object ):
  def __init__( s, mem_nbytes=1<<20 ):
    s.mem       = bytearray( mem_nbytes )

  def read( s, addr, nbytes ):
    nbytes = int(nbytes)
    ret, shamt = Bits( nbytes<<3, 0 ), Bits32(0)
    addr = int(addr)
    end  = addr + nbytes
    for j in range( addr, end ):
      ret += Bits32( s.mem[j] ) << shamt
      shamt += Bits32(8)
    return ret

  def write( s, addr, nbytes, data ):
    tmp  = int(data)
    addr = int(addr)
    end  = addr + int(nbytes)
    for j in range( addr, end ):
      s.mem[j] = tmp & 255
      tmp >>= 8

  def amo( s, amo, addr, nbytes, data ):
    ret = s.read( addr, nbytes )
    s.write( addr, nbytes, AMO_FUNS[ int(amo) ]( ret, data ) )
    return ret

  def read_mem( s, addr, size ):
    assert len(s.mem) > (addr + size)
    return s.mem[ addr : addr + size ]

  def write_mem( s, addr, data ):
    assert len(s.mem) > (addr + len(data))
    s.mem[ addr : addr + len(data) ] = data

  def __getitem__( s, idx ):
    return s.mem[ idx ]

  def __setitem__( s, idx, data ):
    s.mem[ idx ] = data

class TestMemoryRTL( Component ):

  def construct( s, nports = 1, req_types = [ Bits77 ], \
                               resp_types = [ Bits47 ],
                               mem_nbytes=1<<20 ):
    s.mem = TestMemory( mem_nbytes )

    s.reqs  = [ InValRdyIfc( req_types[i] ) for i in range(nports) ]
    s.resps = [ OutValRdyIfc( resp_types[i] ) for i in range(nports) ]
    s.resp_qs = [ PipeQueue1RTL( resp_types[i] ) for i in range(nports) ]

    for i in range(nports):
      connect( s.resps[i], s.resp_qs[i].deq )

    s.req_types  = req_types
    s.resp_types = resp_types

    s.nports = nports

    @s.update
    def up_set_rdy():
      for i in range(nports):
        s.reqs[i].rdy = s.resp_qs[i].enq.rdy

    @s.update
    def up_process_memreq():

      for i in range(nports):
        s.resp_qs[i].enq.val = Bits1( 0 )

        if s.reqs[i].val & s.resp_qs[i].enq.rdy:
          req = s.reqs[i].msg
          typ = req[0:3]
          len = int(req[43:45])
          if not len: len = 4

          resp = Bits47(0)

          if   typ == TYPE_READ:
            resp[0:3]   = Bits3( TYPE_READ )
            resp[3:11]  = req[3:11]
            resp[13:15] = req[43:45]
            resp[15:47] = s.mem.read( req[11:43], len )

          elif typ == TYPE_WRITE:
            s.mem.write( req[11:43], len, req[45:77] )
            resp[0:3]   = Bits3( TYPE_WRITE )
            resp[3:11]  = req[3:11]
            resp[13:15] = req[43:45]

          else: # AMOS
            resp[0:3]   = req[0:3]
            resp[3:11]  = req[3:11]
            resp[13:15] = req[43:45]
            resp[15:47] = s.mem.amo( req[0:3], req[11:43], len, req[45:77] )

          s.resp_qs[i].enq.val = Bits1( 1 )
          s.resp_qs[i].enq.msg = resp

  def read_mem( s, addr, size ):
    return s.mem.read_mem( addr, size )

  def write_mem( s, addr, data ):
    return s.mem.write_mem( addr, data )

  def line_trace( s ):
    return "|".join( [ "{}>{}".format( s.reqs[i].line_trace(), s.resps[i].line_trace() ) \
                                for i in range(s.nports) ] )
