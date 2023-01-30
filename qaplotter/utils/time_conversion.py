
from astropy.coordinates import EarthLocation
from astropy.time import Time
import astropy.units as u


def telescope_time_conversion(time_mjd,
                              telescope='vla',
                              return_casa_string=True):
    '''
    Convert MJD seconds outputted in CASA txt files into a human-readable
    format for flagging purposes.
    '''

    # EK - Checked VLA site + match up of scan times for
    # first 20A-346 track.

    # sma not in hardcoded sites in astropy v5.2
    # Use MJD from JCMT which should be absolutely fine for most things.
    if telescope == 'sma':
        telescope = 'jcmt'
    tele_loc = EarthLocation.of_site(telescope)

    time = Time(time_mjd * u.second, format='mjd', location=tele_loc)

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


def make_casa_timestring(x):

    datetime_vals = vla_time_conversion(x)

    return [dtime.strftime("%Y/%m/%d/%H:%M:%S.%f")[:-5]
            for dtime in datetime_vals]


def datetime_from_msname(msname):
    """
    The VLA SDM names contain the MJD in days. Use the name
    to get a datetime object in UTC.
    """

    # An MS that keeps the SDM name should have eb and sb
    # in the name. This isn't robust but should work for
    # cases where the ms is obviously named differently.
    assert 'eb' in msname
    assert 'sb' in msname

    # Check if we need to strip off .ms, .continuum, .speclines
    for end in ['.ms', '.continuum', '.speclines']:
        if msname.endswith(end):
            msname = msname[:-len(end)]

    mjd_date = float(".".join(msname.split(".")[-2:]))

    # This is in days and `vla_time_conversion` expects seconds.

    utc_datetime = vla_time_conversion((mjd_date * u.day).to(u.s).value)

    return utc_datetime
