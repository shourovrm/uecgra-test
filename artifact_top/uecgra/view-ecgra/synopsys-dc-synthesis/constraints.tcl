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

set clock_net  clk
set clock_name ideal_clock

create_clock -name ${clock_name} \
             -period ${dc_clock_period} \
             [get_ports ${clock_net}]

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

# set_input_delay constraints for input ports
#
# - make this non-zero to avoid hold buffers on input-registered designs

# At CGRA level we are model SRAMs placed next to the tiles so we set 
# input delays to 0 ( that provides enough time for inputs to arrive )

set_input_delay -clock ${clock_name} [expr 0.0*${dc_clock_period}] [all_inputs]

# set_output_delay constraints for output ports

# Same applies for outputs

set_output_delay -clock ${clock_name} [expr 0.0*${dc_clock_period}] [all_outputs]

# Handle feedthrough

set_input_delay -clock ${clock_name} [expr 0.0*${dc_clock_period}] [get_ports send*rdy*]
set_output_delay -clock ${clock_name} 0 [get_ports send*en*]

# Make all signals limit their fanout

set_max_fanout 20 $dc_design_name

# Make all signals meet good slew

set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name

#set_input_transition 1 [all_inputs]
#set_max_transition 10 [all_outputs]

set_false_path -from cfg*
set_false_path -from reset*

# Set all paths from input and to output as false path
# This will not hurt tile-to-tile timing analysis
set_false_path -from [all_inputs]
set_false_path -to   [all_outputs]
