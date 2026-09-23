
from astropy.table import Table


def load_velocity_table(filename):
    '''
    Load the per-target line velocity range table written by
    ReductionPipeline's `build_target_velocity_table` (columns: target,
    line, restfreq_GHz, vlow_kms, vhigh_kms). One row per identified line
    per protected velocity window (a line can have more than one disjoint
    window, and a single SPW can carry more than one identified line, e.g.
    the OH 1665/1667 satellite lines).
    '''

    return Table.read(filename, format='ascii.ecsv')


def velocity_rows_for_field(velocity_table, fieldname):
    '''
    Rows of `velocity_table` whose target name is a substring of
    `fieldname`, matching the same convention ReductionPipeline uses to
    identify science targets from MS field names (`identify_targets`).
    '''

    mask = [target in fieldname for target in velocity_table['target']]
    return velocity_table[mask]
