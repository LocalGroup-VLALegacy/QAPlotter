
from astropy.coordinates import EarthLocation
from astropy.time import Time
import astropy.units as u


def vla_time_conversion(time_mjd, return_casa_string=True):
    '''
    Convert MJD seconds outputted in CASA txt files into a human-readable
    format for flagging purposes.
    '''

    # EK - Checked site + match up of scan times for
    # first 20A-346 track.

    vla_loc = EarthLocation.of_site("vla")

    time = Time(time_mjd * u.second, format='mjd', location=vla_loc)

    if return_casa_string:
        # Replace spaces and - with / to match CASA
        # If one element, returns a str
        # if isinstance(time.iso, str):
        #     return time.iso.replace(" ", "/").replace("-", "/")
        # # Else returns an array of strings
        # else:
        #     return [time_str.replace(" ", "/").replace("-", "/")
        #             for time_str in time.iso]

        # Change to passing datetime objects.
        return time.datetime

    # Otherwise return the Time object
    return time
