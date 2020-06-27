
from astropy.coordinates import EarthLocation
from astropy.time import Time
import astropy.units as u


def vla_time_conversion(time_mjd):
    '''
    Convert MJD seconds outputted in CASA txt files into a human-readable
    format for flagging purposes.
    '''

    # EK - Checked site + match up of scan times for
    # first 20A-346 track.

    vla_loc = EarthLocation.of_site("vla")

    time = Time(time_mjd * u.second, format='mjd', location=vla_loc)

    return time
