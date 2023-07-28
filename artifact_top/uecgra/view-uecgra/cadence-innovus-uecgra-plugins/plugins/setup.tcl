#=========================================================================
# setup.tcl
#=========================================================================
# This design-specific setup.tcl can overwrite any variable in the
# default innovus-flowsetup "setup.tcl" script
#
# Author : Christopher Torng
# Date   : March 26, 2018

# Reduced-effort flow that sacrifices timing to iterate more quickly

set vars(reduced_effort_flow) false

set vars(clk_tree_top_layer)    9
set vars(clk_tree_bottom_layer) 7
