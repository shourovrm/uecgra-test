#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.
#
# Author : Christopher Torng
# Date   : March 26, 2018

#floorPlan -r $core_aspect_ratio $core_density_target        $core_margin_l $core_margin_b $core_margin_r $core_margin_t
floorPlan -d 650 650 $core_margin_l $core_margin_b $core_margin_r $core_margin_t

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

if { $clock_ports != 0 } {
  for {set i 0} {$i < [llength $clock_ports]} {incr i} {
    set pins_left_half \
      [linsert $pins_left_half $half_left_idx [lindex $clock_ports $i]]
  }
}

# Spread the pins evenly across the left and right sides of the block

set ports_layer M4

editPin -layer $ports_layer -pin $pins_left_half  -side LEFT  -spreadType SIDE
editPin -layer $ports_layer -pin $pins_right_half -side RIGHT -spreadType SIDE


setPlaceMode -hardFence  true
setCTSMode   -honorFence true
setOptMode   -honorFence true

for {set idx_y 0} {${idx_y} < 8} {incr idx_y} {
  for {set idx_x 0} {${idx_x} < 8} {incr idx_x} {
    set cur_idx [expr $idx_x + 8*$idx_y]
    set cur_lx [expr 45 + 70*$idx_x]
    set cur_ly [expr 45 + 70*$idx_y]
    set cur_rx [expr 45 + 70*$idx_x + 70]
    set cur_ry [expr 45 + 70*$idx_y + 70]
    createFence tiles__$cur_idx $cur_lx $cur_ly $cur_rx $cur_ry
  }
}
