#=========================================================================
# Design Constraints File
#=========================================================================

# This constraint sets the target clock period for the chip in
# nanoseconds. Note that the first parameter is the name of the clock
# signal in your verlog design. If you called it something different than
# clk you will need to change this. You should set this constraint
# carefully. If the period is unrealistically small then the tools will
# spend forever trying to meet timing and ultimately fail. If the period
# is too large the tools will have no trouble but you will get a very
# conservative implementation.

# Assuming the target clock period is for the nominal clock and
# 2:9:3 clock ratios, we can calculate the clock periods of the other
# two clocks (although in a single tile setup they are not used).

# Fast clock
create_clock -name ideal_clk1 \
             -period [ expr ${dc_clock_period} ] \
             [get_ports clk_rgals__clk1]

# Slow clock
create_clock -name ideal_clk2 \
             -period [ expr ${dc_clock_period} ] \
             [get_ports clk_rgals__clk2]

# Nominal clock
create_clock -name ideal_clk3 \
             -period [ expr ${dc_clock_period} ] \
             [get_ports clk_rgals__clk3]

# Generated clocks from clock switcher

# Using the target clock frequency as the frequency of clk_out will make
# STA work as we expect. Assuming DVFS will proportionally reduce the delay,
# we will be safe as long as the design meets timing at nominal.

#create_generated_clock -name ideal_switched_clk1 -divide_by 1 -combinational -add \
                       #[get_pins clk_switcher/clk_out] \
                       #-source [get_ports clk_rgals\$clk1] \
                       #-master_clock ideal_clk1

#create_generated_clock -name ideal_switched_clk2 -divide_by 1 -combinational -add \
                       #[get_pins clk_switcher/clk_out] \
                       #-source [get_ports clk_rgals\$clk2] \
                       #-master_clock ideal_clk2

create_generated_clock -name ideal_switched_clk3 -divide_by 1 -combinational -add \
                       [get_pins clk_switcher/clk_out] \
                       -source [get_ports clk_rgals__clk3] \
                       -master_clock ideal_clk3

#set_clock_groups -physically_exclusive -group ideal_switched_clk1 -group ideal_switched_clk2 -group ideal_switched_clk3

# This constraint sets the load capacitance in picofarads of the
# output pins of your design.

set_load -pin_load $ADK_TYPICAL_ON_CHIP_LOAD [all_outputs]

# This constraint sets the input drive strength of the input pins of
# your design. We specifiy a specific standard cell which models what
# would be driving the inputs. This should usually be a small inverter
# which is reasonable if another block of on-chip logic is driving
# your inputs.

set_driving_cell -no_design_rule \
  -lib_cell $ADK_DRIVING_CELL [all_inputs]

# Set false paths to handle config

set_false_path -from cfg*
set_false_path -from clk_rate_in*
set_false_path -from reset*
set_false_path -from clk_rgals__clk_reset*

# set_input_delay constraints for input ports
#
# - make this non-zero to avoid hold buffers on input-registered designs

set_input_delay -clock ideal_clk3 [expr 0.8*${dc_clock_period}] [all_inputs]

# set_output_delay constraints for output ports

set_output_delay -clock ideal_clk3 [expr 0.2*${dc_clock_period}] [all_outputs]

# Handle feedthrough

set_input_delay -clock ideal_clk3 [expr 0.1*${dc_clock_period}] [get_ports send*rdy*]
set_output_delay -clock ideal_clk3 0 [get_ports send*en*]

# Handle inputs from/outputs to other bisync queues
# These delays should be relative to the domain clk of the adjacent tiles. In
# the single-tile scenario I specified the reference clock as the one generated
# by the clock mux in the tile.

set_input_delay -clock ideal_switched_clk3 [expr 0.8*${dc_clock_period}] [get_ports recv__*__msg]
set_output_delay -clock ideal_switched_clk3 [expr 0.2*${dc_clock_period}] [get_ports send__*__msg]

# Make all signals limit their fanout

set_max_fanout 20 $dc_design_name

# Make all signals meet good slew

set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name

#set_input_transition 1 [all_inputs]
#set_max_transition 10 [all_outputs]

