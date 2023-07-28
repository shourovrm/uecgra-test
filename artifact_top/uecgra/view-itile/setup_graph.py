#! /usr/bin/env python
#=========================================================================
# setup_graph.py
#=========================================================================
# Demo with 16-bit GcdUnit
#
# Author : Christopher Torng, Yanghui Ou
# Date   : June 2, 2019
#

import os
import sys

if __name__ == '__main__':
  sys.path.append( '../..' )

from mflow.components import Graph, Step

#-------------------------------------------------------------------------
# setup_graph
#-------------------------------------------------------------------------

def setup_graph():

  g = Graph()

  #-----------------------------------------------------------------------
  # Parameters
  #-----------------------------------------------------------------------

  adk_name = 'tsmc-28nm-cln28hpc'
  adk_view = 'view-frontend'

  parameters = {
    'design_name'  : 'TileStatic__1e6a4842d439bc99',
    'clock_period' : 1.33,
    'adk'          : adk_name,
    'adk_view'     : adk_view,
  }

  #-----------------------------------------------------------------------
  # ADK
  #-----------------------------------------------------------------------

  g.set_adk( adk_name )

  #-----------------------------------------------------------------------
  # Import steps
  #-----------------------------------------------------------------------

  # ADK as a step

  adk = g.get_adk_step()

  # Custom steps
  #
  # - rtl
  #

  this_dir = os.path.dirname( os.path.abspath( __file__ ) )

  rtl = Step( this_dir + '/pymtl-rtl' )

  # Default steps
  #
  # - info
  # - synthesis
  # - place and route
  #

  info       = Step( 'info',                        default=True )
  dc         = Step( this_dir + '/synopsys-dc-synthesis'         )
  iflow      = Step( 'cadence-innovus-flowgen',     default=True )
  iplugins   = Step( this_dir + '/cadence-innovus-plugins'       )
  placeroute = Step( this_dir + '/cadence-innovus-place-route'   )
  area       = Step( this_dir + '/area-breakdown'                )

  #-----------------------------------------------------------------------
  # Parameterize
  #-----------------------------------------------------------------------

  adk.update_params( parameters )
  info.update_params( parameters )
  dc.update_params( parameters )
  iflow.update_params( parameters )

  #-----------------------------------------------------------------------
  # Graph -- Add nodes
  #-----------------------------------------------------------------------

  g.add_step( info       )
  g.add_step( rtl        )
  g.add_step( dc         )
  g.add_step( iflow      )
  g.add_step( iplugins   )
  g.add_step( placeroute )
  g.add_step( area       )

  #-----------------------------------------------------------------------
  # Graph -- Add edges
  #-----------------------------------------------------------------------

  # Connect by name

  g.connect_by_name( rtl,      dc )
  g.connect_by_name( adk,      dc )

  g.connect_by_name( adk,      iflow )
  g.connect_by_name( dc,       iflow )
  g.connect_by_name( iplugins, iflow )

  g.connect_by_name( adk,      placeroute )
  g.connect_by_name( dc,       placeroute )
  g.connect_by_name( iflow,    placeroute )
  g.connect_by_name( iplugins, placeroute )

  g.connect_by_name( placeroute, area )

  return g

if __name__ == '__main__':
  g = setup_graph()
#  g.plot()
