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

create_generated_clock -name clk1 -divide_by 3 \
                       [get_pins clk_div_1/clk_divided] \
                       -source [get_ports ${clock_net}]

create_generated_clock -name clk2 -divide_by 5 \
                       [get_pins clk_div_2/clk_divided] \
                       -source [get_ports ${clock_net}]

# Mul clock switcher

create_generated_clock -name mul_clk1 -divide_by 1 -combinational -add \
                       [get_pins mul1/clkswitcher/clk_out] \
                       -source [get_pins clk_div_1/clk_divided] \
                       -master_clock clk1

create_generated_clock -name mul_clk2 -divide_by 1 -combinational -add \
                       [get_pins mul1/clkswitcher/clk_out] \
                       -source [get_pins clk_div_2/clk_divided] \
                       -master_clock clk2

set_clock_groups -physically_exclusive -group mul_clk1 -group mul_clk2

# Accum clock switcher

create_generated_clock -name accum_clk1 -divide_by 1 -combinational -add \
                       [get_pins accum1/clkswitcher/clk_out] \
                       -source [get_pins clk_div_1/clk_divided] \
                       -master_clock clk1

create_generated_clock -name accum_clk2 -divide_by 1 -combinational -add \
                       [get_pins accum1/clkswitcher/clk_out] \
                       -source [get_pins clk_div_2/clk_divided] \
                       -master_clock clk2

set_clock_groups -physically_exclusive -group accum_clk1 -group accum_clk2

#create_generated_clock -name mul_clk1 -divide_by 3 \
#                       [get_pins mul1/clkswitcher/clk_out] \
#                       -source [get_ports ${clock_net}]

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

set_input_delay -clock ${clock_name} [expr ${dc_clock_period}/2.0] [all_inputs]

# set_output_delay constraints for output ports

set_output_delay -clock ${clock_name} 0 [all_outputs]

# Make all signals limit their fanout

set_max_fanout 20 $dc_design_name

# Make all signals meet good slew

set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name

#set_input_transition 1 [all_inputs]
#set_max_transition 10 [all_outputs]

