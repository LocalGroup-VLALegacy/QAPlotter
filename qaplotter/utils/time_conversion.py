
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


def projectcode_from_sdmname(sdmname):

    # An MS that keeps the SDM name should have eb and sb
    # in the name. This isn't robust but should work for
    # cases where the ms is obviously named differently.
    assert 'eb' in sdmname
    assert 'sb' in sdmname

    return sdmname.split(".")[0]


def generate_obslog_link(sdmname):
    '''
    Create a link to the observing log on www.vla.nrao.edu/operators/logs/

    Expected format is:
    http://www.vla.nrao.edu/operators/logs/2014/12/2014-12-11_2203_14B-088.pdf

    YY/MM/YYYY-MM-DD_HHMM_PROJCODE.pdf

    Note there is no leading 0 for months before October.

    '''

    projcode = projectcode_from_sdmname(sdmname)

    this_date = datetime_from_msname(sdmname)

    year_string = this_date.strftime("%Y")
    # The str -> int -> is to strip the leading 0 off
    month_string = str(int(this_date.strftime("%m")))


    file_datestring = this_date.strftime("%Y-%m-%d_%H%M")

    return f"http://www.vla.nrao.edu/operators/logs/{year_string}/{month_string}/{file_datestring}_{projcode}.pdf"
