#=========================================================================
# plot-explore
#=========================================================================
# Plot the exhaustive space of points (generated by the doit tasks in
# task_explore.py) in an energy efficiency (tasks/energy) vs performance
# (tasks/s) space, normalized to the entire design running at nominal
# voltage/frequency.
#
# Date   : August 15, 2019
# Author : Christopher Torng

import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import numpy as np
import sys
import os.path
import json

import matplotlib.patches as patches

#-------------------------------------------------------------------------
# Command line
#-------------------------------------------------------------------------

if len(sys.argv) == 1:
  level = 100
else:
  level = int(sys.argv[1])

#-------------------------------------------------------------------------
# Calculate figure size
#-------------------------------------------------------------------------
# We determine the fig_width_pt by using \showthe\columnwidth in LaTeX
# and copying the result into the script. Change the aspect ratio as
# necessary.

fig_width_pt  = 224.0
inches_per_pt = 1.0/72.27                     # convert pt to inch
aspect_ratio  = 0.9

fig_width     = fig_width_pt * inches_per_pt  # width in inches
fig_height    = fig_width * aspect_ratio      # height in inches
fig_size      = [ fig_width, fig_height ]

#-------------------------------------------------------------------------
# Configure matplotlib
#-------------------------------------------------------------------------

plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['font.size']          = 8
plt.rcParams['font.family']        = 'serif'
plt.rcParams['font.serif']         = ['Times']
plt.rcParams['figure.figsize']     = fig_size

#-----------------------------------------------------------------------
# plot
#-----------------------------------------------------------------------

dumpfile = 'explore-data/plot-explore-list.json'

def create_plot():

  # Load data

  with open( dumpfile, 'r' ) as fd:
    data = json.load(fd)

  perf = data['perf']
  ee   = data['ee'  ]

  plt.plot( perf, ee, color='green', linestyle='',  marker='.', markersize=2 )

  # Draw isopower line

  plt.plot( [0.0, 2.0], [0.0, 2.0], linewidth=0.5, linestyle='-',
      color='b', zorder=1 )

  # Draw lines through (1,1)

  plt.axvline( x=1.0, linewidth=0.5, linestyle='-', color='r', zorder=1 )
  plt.axhline( y=1.0, linewidth=0.5, linestyle='-', color='r', zorder=1 )

#  # Manually draw pareto optimal line
#
#  # Pareto optimal line with lambda_ = 0.10
#  pareto_x = [  0.8,   0.9,   0.95,   1.0, 1.05,   1.1, 1.125, 1.150, 1.175, 1.200, 1.25, 1.30 ]
#  pareto_y = [ 1.36, 1.300, 1.2715, 1.233, 1.19, 1.145, 1.110, 1.090, 1.065, 1.040, 1.00, 0.95 ]
#
#  # Pareto optimal line with lambda_ = 0.50
#  #pareto_x = [  0.8,   0.9,   0.95,   1.0, 1.05,   1.1,  1.125, 1.15,  1.175, 1.2000 ]
#  #pareto_y = [ 1.16, 1.157, 1.1515, 1.143, 1.13, 1.120,  1.110, 1.100, 1.090, 1.080 ]
#
#  plt.plot( pareto_x, pareto_y, color='black', linestyle='--', linewidth=0.7 )
#  plt.text( 0.98, 1.24, "Pareto Frontier", transform=plt.gca().transData,
#      color='black' )
#  plt.gca().add_patch( patches.Rectangle(
#                         (0.98, 1.240),
#                         0.44, 0.032,
#                         color='white',
#                         zorder=3 ) )

  # Draw goal point

#  plt.plot( 1.11, 1.11, color='black', marker='.', markersize=12,
#      markerfacecolor='white', markeredgewidth=1.0 )

  # Move gridlines behind plot

  plt.gca().set_axisbelow(True)

  #for label, ips, ee in zip( labels, IPS, EE ):
  #  plt.annotate( label, (ips, ee), fontsize=5 )

  plt.grid(True)
  plt.xlabel("Normalized Speedup (500 tokens)", fontsize=8 )
  plt.ylabel("Normalized Energy Efficiency", fontsize=8 )

#  plt.xticks(np.arange(0.6, 1.26, 0.1))
#  plt.yticks(np.arange(0.6, 1.26, 0.1))
#  plt.xlim(0.6,1.5)
#  plt.ylim(0.65,1.5)

  ax = plt.gca()

  ax.xaxis.set_major_locator( plticker.MaxNLocator() )
  ax.yaxis.set_major_locator( plticker.MaxNLocator() )

  # Turn off top and right border

  ax.spines['right'].set_visible(False)
  ax.spines['top'].set_visible(False)
  ax.xaxis.set_ticks_position('bottom')
  ax.yaxis.set_ticks_position('left')

  # Remove tick marks

  ax.tick_params( axis='both',
                  which='both',
                  left='off',
                  bottom='off' )

#-------------------------------------------------------------------------
# Generate plots
#-------------------------------------------------------------------------

plt.subplot(1,1,1)
create_plot()

#-------------------------------------------------------------------------
# Generate PDF
#-------------------------------------------------------------------------

input_basename = os.path.splitext( os.path.basename(sys.argv[0]) )[0]
if level == 100:
  output_filename = input_basename + '.py.pdf'
else:
  output_filename = input_basename + '_' + str(level) + '-split.py.pdf'

plt.savefig( output_filename, bbox_inches='tight' )
