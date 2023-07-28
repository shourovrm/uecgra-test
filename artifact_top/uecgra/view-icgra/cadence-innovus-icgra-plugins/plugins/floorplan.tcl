#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.
#
# Author : Christopher Torng
# Date   : March 26, 2018

set tile_num_w  [expr 8]
set tile_num_h  [expr 8]
set tile_width  [expr 66]
set tile_height [expr 66]
set inter_tile_margin_w [expr 1]
set inter_tile_margin_h [expr 1]

floorPlan -d [expr $core_margin_l+$core_margin_r+$tile_num_w*$tile_width+($tile_num_w-1)*$inter_tile_margin_w] \
             [expr $core_margin_b+$core_margin_t+$tile_num_h*$tile_height+($tile_num_h-1)*$inter_tile_margin_h] \
             $core_margin_l $core_margin_b $core_margin_r $core_margin_t

setFlipping s

# Use automatic floorplan synthesis to pack macros (e.g., SRAMs) together

planDesign

# Take all ports and split into halves

set all_ports       [dbGet top.terms.name -v *clk*]

set num_ports       [llength $all_ports]
set half_ports_idx  [expr $num_ports / 2]

set pins_left_half  [lrange $all_ports 0               [expr $half_ports_idx - 1]]
set pins_right_half [lrange $all_ports $half_ports_idx [expr $num_ports - 1]     ]

# Take all clock ports and place them center-left

set clock_ports     [dbGet top.terms.name *clk*]
set half_left_idx   [expr [llength $pins_left_half] / 2]

# Bottom

# cfg_0
set bottom_pins [dbGet top.terms.name cfg__0__*]

# imm_0
set imms [dbGet top.terms.name imm__0\[*]
for {set imm_i 0} {$imm_i < [llength $imms]} {incr imm_i} {
  set bottom_pins \
      [linsert $bottom_pins $num_ports [lindex $imms $imm_i]]
}

for {set i 1} {$i < 32} {incr i} {
  # cfg_N
  set cfgs [dbGet top.terms.name cfg__${i}__*]
  for {set cfg_i 0} {$cfg_i < [llength $cfgs]} {incr cfg_i} {
    set bottom_pins \
        [linsert $bottom_pins $num_ports [lindex $cfgs $cfg_i]]
  }
  # cfg_en
  set cfgs [dbGet top.terms.name cfg_en\[${i}*]
  for {set cfg_i 0} {$cfg_i < [llength $cfgs]} {incr cfg_i} {
    set bottom_pins \
        [linsert $bottom_pins $num_ports [lindex $cfgs $cfg_i]]
  }
  # imm_N
  set imms [dbGet top.terms.name imm__${i}\[*]
  for {set imm_i 0} {$imm_i < [llength $imms]} {incr imm_i} {
    set bottom_pins \
        [linsert $bottom_pins $num_ports [lindex $imms $imm_i]]
  }
}

# recv_s
set recvs [dbGet top.terms.name recv_s*]
for {set recv_i 0} {$recv_i < [llength $recvs]} {incr recv_i} {
  set bottom_pins \
      [linsert $bottom_pins $num_ports [lindex $recvs $recv_i]]
}

# send_s
set sends [dbGet top.terms.name send_s*]
for {set send_i 0} {$send_i < [llength $sends]} {incr send_i} {
  set bottom_pins \
      [linsert $bottom_pins $num_ports [lindex $sends $send_i]]
}

# Top

# cfg_32
set top_pins [dbGet top.terms.name cfg__32__*]

# imm_32
set imms [dbGet top.terms.name imm__32\[*]
for {set imm_i 0} {$imm_i < [llength $imms]} {incr imm_i} {
  set top_pins \
      [linsert $top_pins $num_ports [lindex $imms $imm_i]]
}

for {set i 33} {$i < 64} {incr i} {
  # cfg_N
  set cfgs [dbGet top.terms.name cfg__${i}__*]
  for {set cfg_i 0} {$cfg_i < [llength $cfgs]} {incr cfg_i} {
    set top_pins \
        [linsert $top_pins $num_ports [lindex $cfgs $cfg_i]]
  }

  # cfg_en
  set cfgs [dbGet top.terms.name cfg_en\[${i}*]
  for {set cfg_i 0} {$cfg_i < [llength $cfgs]} {incr cfg_i} {
    set top_pins \
        [linsert $top_pins $num_ports [lindex $cfgs $cfg_i]]
  }

  # imm_N
  set imms [dbGet top.terms.name imm__${i}\[*]
  for {set imm_i 0} {$imm_i < [llength $imms]} {incr imm_i} {
    set top_pins \
        [linsert $top_pins $num_ports [lindex $imms $imm_i]]
  }
}

# recv_n
set recvs [dbGet top.terms.name recv_n*]
for {set recv_i 0} {$recv_i < [llength $recvs]} {incr recv_i} {
  set top_pins \
      [linsert $top_pins $num_ports [lindex $recvs $recv_i]]
}

# send_n
set sends [dbGet top.terms.name send_n*]
for {set send_i 0} {$send_i < [llength $sends]} {incr send_i} {
  set top_pins \
      [linsert $top_pins $num_ports [lindex $sends $send_i]]
}

# Left

set left_pins [dbGet top.terms.name recv_w*]
set sends [dbGet top.terms.name send_w*]
for {set send_i 0} {$send_i < [llength $sends]} {incr send_i} {
  set left_pins \
      [linsert $left_pins $num_ports [lindex $sends $send_i]]
}

# Right

set right_pins [dbGet top.terms.name recv_e*]
set sends [dbGet top.terms.name send_e*]
for {set send_i 0} {$send_i < [llength $sends]} {incr send_i} {
  set right_pins \
      [linsert $right_pins $num_ports [lindex $sends $send_i]]
}

# suspend

# Spread the pins evenly across the four sides of the block

set ports_layer M4

editPin -layer $ports_layer -pin $left_pins   -side LEFT   -spreadType SIDE
editPin -layer $ports_layer -pin $right_pins  -side RIGHT  -spreadType SIDE
editPin -layer $ports_layer -pin $top_pins    -side TOP    -spreadType SIDE
editPin -layer $ports_layer -pin $bottom_pins -side BOTTOM -spreadType SIDE

# Tell innovus to honor the fences

setPlaceMode -hardFence  true
setCTSMode   -honorFence true
setOptMode   -honorFence true

for {set idx_y 0} {${idx_y} < ${tile_num_h}} {incr idx_y} {
  for {set idx_x 0} {${idx_x} < ${tile_num_w}} {incr idx_x} {
    set cur_idx [expr $idx_x + $tile_num_w*$idx_y]
    #                      LB            Tile  1 micron between tiles
    set cur_lx [expr $core_margin_l + ($tile_width +$inter_tile_margin_w)*$idx_x]
    set cur_ly [expr $core_margin_b + ($tile_height+$inter_tile_margin_h)*$idx_y]
    set cur_rx [expr $core_margin_l + ($tile_width +$inter_tile_margin_w)*$idx_x + $tile_width ]
    set cur_ry [expr $core_margin_b + ($tile_height+$inter_tile_margin_h)*$idx_y + $tile_height]
    createFence tiles__$cur_idx $cur_lx $cur_ly $cur_rx $cur_ry
  }
}
