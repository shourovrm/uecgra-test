
JSON format specifics:
```
Available src  : "N", "S", "W", "E", "self"
Available dst  : "N", "S", "W", "E", "self", "none"
Available op   : "cp0", "cp1", "add", "sub", "sll", "srl", "and", "or'", "xor", 
                   "eq'", "ne'", "gt'", "geq", "lt'", "leq", "mul", "phi", "nop", "br"
Available dvfs : "slow", "nominal", "fast"
Note that the above options are all case insensitive
[
  {
    "x"           : 0,            // int: coordiate X
    "y"           : 5,            // int: coordiate Y
    "op"          : "none",       // string (op): "none", "add", etc
    "src_a"       : "self",       // string (src of opd a): "self", "N", "E", etc
    "src_b"       : "self",       // string (src of opd b): "self", "N", "E", etc
    "dst"         : [ "S", "E" ], // list of string (outports for compute)
    "bps_src"     : "N",          // string (bypass src), if this field is missing. then it will be set to "self"
    "bps_dst"     : [ "W" ],      // list of string (bypass dst), if this field is missing. then it will be set to [ "none" ]
    "bps_alt_src" : "E",          // string (alternative bypass src), if this field is missing. then it will be set to "self"
    "bps_alt_dst" : [ "N" ],      // list of string (alternative bypass dst), if this field is missing. then it will be set to [ "none" ]
    "dvfs"        : "nominal"
  },
]
```
-------------------------
Note that the items or subitems no need to appear if they are not used.
For example, in above example, "op", "src_a", and "src_b" can be eliminated.

One exception is the JSON format for the 'br' node. Note that branch does not support broadcast for compute dst, therefore the compute dst is not a list.
```
[
  {
    "x"           : 1,
    "y"           : 2,
    "op"          : "br",
    "src_data"    : "S",     // string (data): the "data" incoming port
    "src_bool"    : "E",     // string (bool): the "bool" outgoing port
    "dst_true"    : "N",     // string (dst true): the "data" outgoing port if "bool" is true
    "dst_false"   : "none",  // string (dst false): the "data" outgoing port if "bool" is false
    "bps_src"     : "N",     // string (bypass src), if this field is missing. then it will be set to "self"
    "bps_dst"     : [ "S" ], // list of string (bypass dst), if this field is missing. then it will be set to [ "none" ]
    "bps_alt_src" : "E",     // string (alternative bypass src), if this field is missing. then it will be set to "self"
    "bps_alt_dst" : [ "N" ], // list of string (alternative bypass dst), if this field is missing. then it will be set to [ "none" ]
    "dvfs"        : "nominal"
  },
]
```
