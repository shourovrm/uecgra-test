#=========================================================================
# color_scheme.py
#=========================================================================
# A color scheme generator.
#
# Author : Peitian Pan
# Date   : Sep 10, 2019

from matplotlib.cm import get_cmap

def scheme_gen( scheme_name, item_dict, extra_slot=0 ):
  assert item_dict
  cmap = get_cmap(scheme_name, lut=len(item_dict)+extra_slot)
  color_dict = {k:'' for k in item_dict.keys()}

  for idx, key in enumerate(item_dict.keys()):
    f_idx = idx / float(len(item_dict)+extra_slot)
    color_dict[key] = cmap(f_idx)

  return color_dict

def get_tile_breakdown_color_dict( scheme_name ):
  plt_dict = {
    'leak'         : '',
    'mul'          : '',
    'alu'          : '',
    'acc'          : '',
    'in_q_n'       : '',
    'in_q_s'       : '',
    'in_q_w'       : '',
    'in_q_e'       : '',
    'suppress'     : '',
    'unsafe_gen'   : '',
    'clk_switcher' : '',
    'muxes'        : '',
    'other'        : '',
  }
  color_dict = scheme_gen( scheme_name, plt_dict )

  return color_dict
