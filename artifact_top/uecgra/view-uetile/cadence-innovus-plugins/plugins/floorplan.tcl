#=========================================================================
## floorplan.tcl
##=========================================================================
## This script is called from the Innovus init flow step.
##
## Author : Christopher Torng
## Date   : March 26, 2018

floorPlan -r $core_aspect_ratio $core_density_target \
             $core_margin_l $core_margin_b $core_margin_r $core_margin_t

setFlipping s

# Use automatic floorplan synthesis to pack macros (e.g., SRAMs) together

planDesign

# Split the pins into groups

set top_pins    [dbGet top.terms.name -regexp recv__0__*|send__0__*|clk_out__0*|clk_rate_in__0*|clk_rate_out__0*]
set bottom_pins [dbGet top.terms.name -regexp recv__1__*|send__1__*|clk_out__1*|clk_rate_in__1*|clk_rate_out__1*]
set left_pins   [dbGet top.terms.name -regexp recv__2__*|send__2__*|clk_out__2*|clk_rate_in__2*|clk_rate_out__2*|cfg*|imm*]
set right_pins  [dbGet top.terms.name -regexp recv__3__*|send__3__*|clk_out__3*|clk_rate_in__3*|clk_rate_out__3*|clk_rgals*|reset*]

# Spread the pins evenly across the four sides of the block

set ports_layer M4

editPin -layer $ports_layer -pin $left_pins   -side LEFT   -spreadType CENTER
editPin -layer $ports_layer -pin $right_pins  -side RIGHT  -spreadType CENTER
editPin -layer $ports_layer -pin $top_pins    -side TOP    -spreadType CENTER
editPin -layer $ports_layer -pin $bottom_pins -side BOTTOM -spreadType CENTER
