"""
==========================================================================
plot_stack.py
==========================================================================
Utility function to plot a stacked bar plot..

Author : Yanghui Ou
  Date : Aug 18, 2019

"""
import matplotlib.pyplot as plt
import numpy as np

#-------------------------------------------------------------------------
# plot_stack
#-------------------------------------------------------------------------
# Plot the bar

def plot_stack( plt_dict, color_dict, bar_names=None, ylabel='', outdir='power_breakdown.pdf' ):

  # Assume the list for each key has the same length.
  nbars       = len( list( plt_dict.values() )[0] )
  nstacks     = len( plt_dict )
  stack_names = list( plt_dict.keys() )
  if bar_names == None:
    bar_names = [ '' for _ in range(nbars) ]
  stack_lst   = []

  ind   = np.arange( nbars )
  width = 0.3

  fig = plt.figure()

  cur_bottom = np.array([ 0.0 for _ in range(nbars) ])
  for item_name, data in plt_dict.items():
    data = np.array( data )
    assert item_name in color_dict
    color = color_dict[ item_name ]
    stack_lst.append( plt.bar( ind, data, width, bottom=cur_bottom, color=color, edgecolor=color ) )
    cur_bottom += data

  plt.ylabel( ylabel )
  plt.xticks( ind, bar_names )
  rev_stack_lst = stack_lst[::-1]
  # Reverse the legend to match the stack plot
  plt.legend( [ bar[0] for bar in rev_stack_lst ], stack_names[::-1] )

  fig.savefig( outdir )
