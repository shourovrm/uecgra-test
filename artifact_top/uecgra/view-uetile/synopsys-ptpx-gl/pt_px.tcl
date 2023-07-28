#=========================================================================
# pt_px.tcl
#=========================================================================
# We use Synopsys Prime-Time to get the power analysis of the PnR Netlist.
#
# This Prime-Time Power analysis step follows the Signoff step to estimate
# the average power of the gate-level netlist using RTL SAIF file.
#
# Author : Shady Agwa, Yanghui Ou
# Date   : May 7, 2019
#

set pt_search_path inputs/adk 
set pt_target_libraries stdcells.db
set pt_design_name  $::env(design_name)
set pt_reports reports
# Only extract activity for the RGALS tile (not including the wrapper)
set pt_uut tbench_TileStatic_RGALS__4860350d42859600/tile
set pt_clk_period $::env(clock_period)

set_app_var target_library "* ${pt_search_path}/${pt_target_libraries}"
set_app_var link_library "* ${pt_search_path}/${pt_target_libraries} "
set_app_var power_enable_analysis true 

read_verilog inputs/design.vcs.v

current_design ${pt_design_name}
file mkdir ${pt_reports}
link_design > ${pt_reports}/${pt_design_name}.link.rpt

# create_clock ${pt_clk} -name ideal_clock1 -period ${pt_clk_period}

# Fast clock
create_clock -name ideal_clk1 \
             -period [ expr ${pt_clk_period} ] \
             [get_ports clk_rgals__clk1]

# Slow clock
create_clock -name ideal_clk2 \
             -period [ expr ${pt_clk_period} ] \
             [get_ports clk_rgals__clk2]

# Nominal clock
create_clock -name ideal_clk3 \
             -period [ expr ${pt_clk_period} ] \
             [get_ports clk_rgals__clk3]

source inputs/design.namemap > ${pt_reports}/${pt_design_name}.map.rpt

report_activity_file_check inputs/run.saif -strip_path ${pt_uut} \
  > ${pt_reports}/${pt_design_name}.activity.pre.rtp

read_saif inputs/run.saif -strip_path ${pt_uut}
read_parasitics -format spef inputs/design.spef.gz
read_sdc inputs/design.pt.sdc > ${pt_reports}/${pt_design_name}.sdc.rpt

update_power > ${pt_reports}/${pt_design_name}.update.rpt
report_switching_activity > ${pt_reports}/${pt_design_name}.sw.rpt 
report_power -nosplit  -verbose > ${pt_reports}/signoff.pwr.rpt
report_power -nosplit -hierarchy -verbose > ${pt_reports}/${pt_design_name}.pwr.hier.rpt
exit
