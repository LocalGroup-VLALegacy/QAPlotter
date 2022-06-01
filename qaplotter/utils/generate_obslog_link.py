
from .time_conversion import datetime_from_msname


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
