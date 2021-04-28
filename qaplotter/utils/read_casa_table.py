
'''
Functions for reading in different CASA calibration tables.
Requires CASA 6 or above
'''

import numpy as np
from astropy.table import Table, Column
import astropy.units as u

from .time_conversion import vla_time_conversion


def read_delay_table(tablename):
    """
    Read a CASA delay calibration table and return an astropy table
    for plotting.
    """

    from casatools import table

    tb = table()

    tb.open(tablename)

    # TODO: generalize for full pol table.
    delays = tb.getcol('FPARAM').squeeze() * u.ns
    delays_ll = delays[0]
    delays_rr = delays[1]

    flags = tb.getcol('FLAG').squeeze()
    flags_ll = flags[0]
    flags_rr = flags[1]

    field_ids = tb.getcol('FIELD_ID').squeeze()
    scan_numbers = tb.getcol('SCAN_NUMBER').squeeze()

    spws = tb.getcol('SPECTRAL_WINDOW_ID').squeeze()
    # How many unique SPWs?
    nspw = np.unique(spws).size


    ant1 = tb.getcol('ANTENNA1').squeeze()
    ant2 = tb.getcol('ANTENNA2').squeeze()

    # Close when done
    tb.done()
    tb.close()

    tab = Table([Column(delays_rr, 'delay_rr'), Column(delays_ll, 'delay_ll'),
                 Column(flags_rr, 'flag_rr'), Column(flags_ll, 'flag_ll'),
                 Column(field_ids, 'field'),
                 Column(scan_numbers, 'scan_number'), Column(spws, 'spw'),
                 Column(ant1, 'antenna1'), Column(ant2, 'antenna2')])

    return tab


def read_ampgain_table(tablename):
    """
    Read a CASA amp-gain calibration table and return an astropy table
    for plotting.

    """




    ## ADD conversion call: vla_time_conversion

    pass


def read_phasegain_table(tablename):
    """
    Read a CASA phase-gain calibration table and return an astropy table
    """
    pass
