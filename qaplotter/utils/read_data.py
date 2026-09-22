
from astropy.table import Table, vstack
import os
from glob import glob
import numpy as np

osjoin = os.path.join


def read_casa_txt(filename):
    '''
    Read a QA data table, dispatching on file extension:

    - ".ecsv": tables written by the casatools-based `make_qa_tables`
      (ReductionPipeline >= the plotms removal). Self-describing astropy
      ECSV; the header/units-row parsing below does not apply.
    - anything else (".txt"): the original plotms native text export.

    Both older (plotms) and newer (casatools/ecsv) pipeline outputs can
    be present side by side (e.g. re-running QA on older products), so
    this dispatch is by the concrete file rather than a global setting.
    '''

    if filename.endswith('.ecsv'):
        return _read_casa_txt_ecsv(filename)

    return _read_casa_txt_plotms(filename)


def _read_casa_txt_ecsv(filename):

    try:
        tab = Table.read(filename, format='ascii.ecsv')
    except Exception as e:
        print(f"Failed reading {filename} with exception {e}.")
        return Table(), {}

    # table.meta is already a plain dict of the run/table info
    # (field, scan, vis, ydatacolumn) written by make_qa_tables.
    meta_dict = dict(tab.meta)

    return tab, meta_dict


# plotms's native export always uses generic 'x'/'y' columns for
# whatever the plot's xaxis/yaxis was (plus a few tab-type-specific ones
# like 'chan'/'freq'/'time'/'ant1'/'ant2' that happen to be redundant
# with 'x' or 'y' for some tab_types). field_plots.py now expects the
# same descriptive column names the casatools/ecsv writer uses
# (amp/phase/uvdist/uvwave/resid), so alias 'x'/'y' to those based on
# the tab_type encoded in the filename -- only for whichever of 'x'/'y'
# doesn't already have a same-valued named column (e.g. 'time' for the
# *_time tables, 'chan'/'freq' for the *_chan tables, 'ant1'/'ant2' for
# the *_ant1 tables are already present under their real names).
_LEGACY_VALUE_ALIASES = {
    'amp_chan': {'y': 'amp'},
    'amp_time': {'y': 'amp'},
    'amp_uvdist': {'x': 'uvdist', 'y': 'amp'},
    'amp_phase': {'x': 'amp', 'y': 'phase'},
    'phase_chan': {'y': 'phase'},
    'phase_time': {'y': 'phase'},
    'phase_uvdist': {'x': 'uvdist', 'y': 'phase'},
    'ampresid_uvwave': {'x': 'uvwave', 'y': 'resid'},
    'amp_ant1': {'y': 'amp'},
    'phase_ant1': {'y': 'phase'},
}


def _alias_legacy_columns(tab, filename):
    '''
    No-op for anything that isn't one of the known MS-QA table types
    (e.g. calibration-table exports, which field_plots.py doesn't touch
    and keep their own plotms-native column names).
    '''

    basename = os.path.basename(filename)
    tab_type = next((t for t in sorted(_LEGACY_VALUE_ALIASES, key=len, reverse=True)
                     if t in basename), None)
    if tab_type is None:
        return tab

    for generic_col, real_name in _LEGACY_VALUE_ALIASES[tab_type].items():
        if generic_col in tab.colnames and real_name not in tab.colnames:
            tab[real_name] = tab[generic_col]

    return tab


def _read_casa_txt_plotms(filename):

    # Grab the meta-data from the header
    meta_lines = skim_header_metadata(filename)

    meta_dict = make_meta_dict(meta_lines)

    # After the plot 0 line
    header_start = len(meta_lines) + 1
    # One for column names, another for units.
    data_start = len(meta_lines) + 3

    try:
        tab = Table.read(filename,
                        format='ascii.commented_header',
                        header_start=header_start,
                        data_start=data_start)
        tab = _alias_legacy_columns(tab, filename)
    except Exception as e:
        print(f"Failed reading {filename} with exception {e}.")
        tab = Table()

    return tab, meta_dict


def skim_header_metadata(filename):
    '''
    Search for "From plot 0"
    '''
    search_str = "# From plot 0"

    # Should be close to ~10 or below, I think
    # This just stops reading too far if something
    # goes wrong.
    max_line = 50

    meta_lines = []

    with open(filename, 'r') as f:

        for i, line in enumerate(f):
            if search_str in line:
                break

            meta_lines.append(line)

            if i > max_line:
                raise ValueError(f"Could not find header in {filename}")

    return meta_lines


def make_meta_dict(meta_lines):
    '''
    Convert the meta lines into something nice.
    '''

    data_dict = {}

    for line in meta_lines:

        # Skip "# "
        line = line[2:]

        # Some plotms output will have multiple name:value pairs
        num_names = len(line.split(": ")) // 2

        for ii in range(num_names):

            name, value = line.split(": ")[2*ii:2*(ii)+2]

            name = name.strip(" ")
            value = value.strip(" ")
            value = value.strip("\n")

            data_dict[name] = value

    # CASA 6.6 uses 'file' instead of 'vis'.
    if 'file' in data_dict:
        data_dict['vis'] = data_dict['file']
        del data_dict['file']

    return data_dict


def read_field_data_tables(fieldname, inp_path, try_per_scan=True):
    '''
    Read in a set of tables for a given `fieldname`. Note that this depends on the function:
    https://github.com/e-koch/ReductionPipeline/blob/master/lband_pipeline/qa_plotting/qa_plot_tools.py#L311.
    Because of this, the read-in is not generalized and may need to be updated.
    '''

    table_dict = dict()
    meta_dict = dict()

    # Table types:
    tab_types = ["amp_chan", "amp_phase", "amp_time", "amp_uvdist", "phase_chan",
                 "phase_time", "phase_uvdist", "ampresid_uvwave", "amp_ant1",
                 "phase_ant1"]
    # Target fields will not have the phase tables.
    # Cal fields should have all

    print(f" On field {fieldname}.")

    # Both the legacy plotms ".txt" export and the newer casatools-based
    # ".ecsv" export may be present (e.g. re-running QA on older
    # products); read_casa_txt itself dispatches on the extension, so
    # just try both here and use whichever is found. An empty ".ecsv"
    # file is never written (make_qa_tables skips it outright when there
    # is no valid data), but it always carries a non-trivial YAML header,
    # so a size floor tuned for plotms's flakiness (near-empty ".txt"
    # exports) would wrongly reject small-but-valid ecsv tables.
    exts = ['txt', 'ecsv']
    min_size = {'txt': 1000, 'ecsv': 200}

    for tab_type in tab_types:
        tabname = None
        for ext in exts:
            candidate = osjoin(inp_path, f"field_{fieldname}_{tab_type}.{ext}")
            if os.path.exists(candidate):
                tabname = candidate
                break

        if tabname is not None:
            out = read_casa_txt(tabname)

            table_dict[tab_type] = out[0]
            meta_dict[tab_type] = out[1]

        else:
            # Recent change to output txt tables per scan to reduce the memory footprint
            # when calling plotms
            if try_per_scan:
                tabnames = []
                for ext in exts:
                    tabnames.extend(glob(osjoin(inp_path, f"field_{fieldname}_{tab_type}.scan_*.{ext}")))

                if len(tabnames) == 0:
                    print(f"Could not find {tab_type} tables for {fieldname} per scans. Skipping.")
                    continue

                # Loop through and stack the tables
                scan_tables = []
                for tabname in tabnames:
                    # Skip empty tables
                    ext = tabname.rsplit('.', 1)[-1]
                    if os.path.getsize(tabname) < min_size.get(ext, 1000):
                        continue

                    out = read_casa_txt(tabname)

                    scan_tables.append(out[0])

                if len(scan_tables) == 0:
                    print(f"Could not find {tab_type} tables for {fieldname} per scans. Skipping.")
                    continue

                # Each scan's table.meta['scan'] necessarily differs; the
                # combined table's own 'scan' column (added by the
                # casatools-based writer) is what matters row-to-row, so
                # don't warn about the meta-level conflict.
                comb_table = vstack(scan_tables, metadata_conflicts='silent')

                # CASA v6.6 is outputting a "poln" column name; previous versions used 'corr'
                if 'poln' in comb_table.colnames:
                    comb_table.rename_column('poln', 'corr')

                table_dict[tab_type] = comb_table

                # Grab the last meta-data dict. These shouldn't change across scans
                # for the values we use for the plots.
                meta_dict[tab_type] = out[1]

            else:
                if not try_per_scan:
                    print(f"Could not find {tab_type} table for {fieldname}. Skipping.")

    return table_dict, meta_dict


def read_bpcal_data_tables(inp_path):
    '''
    Read in the BP txt files for amp and phase.
    '''

    table_dict = dict()
    meta_dict = dict()

    # Table types:
    tab_types = ["amp", "phase"]

    for tab_type in tab_types:
        table_dict[tab_type] = {}
        meta_dict[tab_type] = {}

    amp_tab_names = glob(f"{inp_path}/*finalBPcal_freq_amp*.txt")
    phase_tab_names = glob(f"{inp_path}/*finalBPcal_freq_phase*.txt")

    # If either of these return 0, try the old naming scheme:
    if len(amp_tab_names) == 0 or len(phase_tab_names) == 0:
        amp_tab_names = glob(f"{inp_path}/*finalBPcal_amp*.txt")
        phase_tab_names = glob(f"{inp_path}/*finalBPcal_phase*.txt")

    if len(amp_tab_names) != len(phase_tab_names):
        raise ValueError("Number of BP amp tables does not match BP phase tables.: "
                         f"Num amp tables: {len(amp_tab_names)}. Num phase tables: {len(phase_tab_names)}")

    # Sort by SPW and create a text

    spw_nums = [int(tab.rstrip(".txt").split("spw")[1]) for tab in amp_tab_names]

    for spw in spw_nums:

        # There aren't many to loop through.
        for amp_name in amp_tab_names:

            if f"_spw{spw}.txt" in amp_name:
                break

        for phase_name in phase_tab_names:

            if f"_spw{spw}.txt" in phase_name:
                break

        amp_out = read_casa_txt(amp_name)
        phase_out = read_casa_txt(phase_name)

        table_dict['amp'][spw] = amp_out[0]
        table_dict['phase'][spw] = phase_out[0]

        meta_dict['amp'][spw] = amp_out[1]
        meta_dict['phase'][spw] = phase_out[1]

    return table_dict, meta_dict


def read_delay_data_tables(inp_path):
    '''
    Read in the BP txt files for amp and phase.
    '''

    table_dict = dict()
    meta_dict = dict()

    # Table types:
    tab_types = ["delay"]

    for tab_type in tab_types:
        table_dict[tab_type] = {}
        meta_dict[tab_type] = {}

    delay_tab_names = glob(f"{inp_path}/*finaldelay_freq_delay*.txt")

    # Sort by SPW and create a text
    ant_nums = [int(tab.rstrip(".txt").split("ant")[1]) for tab in delay_tab_names]

    for ant in ant_nums:

        # There aren't many to loop through.
        for ant_name in delay_tab_names:

            if f"_ant{ant}.txt" in ant_name:
                break

        delay_out = read_casa_txt(ant_name)

        table_dict['delay'][ant] = delay_out[0]

        meta_dict['delay'][ant] = delay_out[1]

    return table_dict, meta_dict


def read_BPinitialgain_data_tables(inp_path):
    '''
    Read in the BP txt files for amp and phase.
    '''

    table_dict = dict()
    meta_dict = dict()

    # Table types:
    tab_types = ["phase"]

    for tab_type in tab_types:
        table_dict[tab_type] = {}
        meta_dict[tab_type] = {}

    bpinitial_tab_names = glob(f"{inp_path}/*finalBPinitialgain_time_phase*.txt")

    # Sort by SPW and create a text
    ant_nums = [int(tab.rstrip(".txt").split("ant")[1]) for tab in bpinitial_tab_names]

    for ant in ant_nums:

        # There aren't many to loop through.
        for ant_name in bpinitial_tab_names:

            if f"_ant{ant}.txt" in ant_name:
                break

        phase_out = read_casa_txt(ant_name)

        table_dict['phase'][ant] = phase_out[0]

        meta_dict['phase'][ant] = phase_out[1]

    return table_dict, meta_dict


def read_phaseshortgaincal_data_tables(inp_path):
    '''
    Read in the BP txt files for amp and phase.
    '''

    table_dict = dict()
    meta_dict = dict()

    # Table types:
    tab_types = ["phase"]

    for tab_type in tab_types:
        table_dict[tab_type] = {}
        meta_dict[tab_type] = {}

    phaseshort_tab_names = glob(f"{inp_path}/*phaseshortgaincal_time_phase*.txt")

    # Sort by SPW and create a text
    ant_nums = [int(tab.rstrip(".txt").split("ant")[1]) for tab in phaseshort_tab_names]

    for ant in ant_nums:

        # There aren't many to loop through.
        for ant_name in phaseshort_tab_names:

            if f"_ant{ant}.txt" in ant_name:
                break

        phase_out = read_casa_txt(ant_name)

        table_dict['phase'][ant] = phase_out[0]

        meta_dict['phase'][ant] = phase_out[1]

    return table_dict, meta_dict


def read_ampgaincal_time_data_tables(inp_path):
    '''
    Read in the BP txt files for amp and phase.
    '''

    table_dict = dict()
    meta_dict = dict()

    # Table types:
    tab_types = ["amp"]

    for tab_type in tab_types:
        table_dict[tab_type] = {}
        meta_dict[tab_type] = {}

    ampgaincal_tab_names = glob(f"{inp_path}/*finalampgaincal_time_amp*.txt")

    # Sort by SPW and create a text
    ant_nums = [int(tab.rstrip(".txt").split("ant")[1]) for tab in ampgaincal_tab_names]

    for ant in ant_nums:

        # There aren't many to loop through.
        for ant_name in ampgaincal_tab_names:

            if f"_ant{ant}.txt" in ant_name:
                break

        amp_out = read_casa_txt(ant_name)

        table_dict['amp'][ant] = amp_out[0]

        meta_dict['amp'][ant] = amp_out[1]

    return table_dict, meta_dict


def read_ampgaincal_freq_data_tables(inp_path):
    '''
    Read in the BP txt files for amp and phase.
    '''

    table_dict = dict()
    meta_dict = dict()

    # Table types:
    tab_types = ["amp"]

    for tab_type in tab_types:
        table_dict[tab_type] = {}
        meta_dict[tab_type] = {}

    ampgaincal_tab_names = glob(f"{inp_path}/*finalampgaincal_freq_amp*.txt")

    # Sort by SPW and create a text
    ant_nums = [int(tab.rstrip(".txt").split("ant")[1]) for tab in ampgaincal_tab_names]

    for ant in ant_nums:

        # There aren't many to loop through.
        for ant_name in ampgaincal_tab_names:

            if f"_ant{ant}.txt" in ant_name:
                break

        amp_out = read_casa_txt(ant_name)

        table_dict['amp'][ant] = amp_out[0]

        meta_dict['amp'][ant] = amp_out[1]

    return table_dict, meta_dict


def read_phasegaincal_data_tables(inp_path):
    '''
    Read in the BP txt files for amp and phase.
    '''

    table_dict = dict()
    meta_dict = dict()

    # Table types:
    tab_types = ["phase"]

    for tab_type in tab_types:
        table_dict[tab_type] = {}
        meta_dict[tab_type] = {}

    phaseshort_tab_names = glob(f"{inp_path}/*finalphasegaincal_time_phase*.txt")

    # Sort by SPW and create a text
    ant_nums = [int(tab.rstrip(".txt").split("ant")[1]) for tab in phaseshort_tab_names]

    for ant in ant_nums:

        # There aren't many to loop through.
        for ant_name in phaseshort_tab_names:

            if f"_ant{ant}.txt" in ant_name:
                break

        phase_out = read_casa_txt(ant_name)

        table_dict['phase'][ant] = phase_out[0]

        meta_dict['phase'][ant] = phase_out[1]

    return table_dict, meta_dict


def read_flagfrac_freq_data_tables(inp_path):

    table_dict = dict()

    template_name = '_flagfrac_freq.txt'

    flagfrac_tab_names = glob(f"{inp_path}/*{template_name}")

    for tab_filename in flagfrac_tab_names:

        field_name = os.path.basename(tab_filename).split(template_name)[0].split('field_')[1]

        data = np.loadtxt(tab_filename)

        colnames = ['spw', 'channel', 'freq', 'frac']

        table_dict[field_name] = Table(data, names=colnames)

    return table_dict


def read_flagfrac_uvdist_data_tables(inp_path):

    table_dict = dict()

    template_name = '_flagfrac_uvdist.txt'

    flagfrac_tab_names = glob(f"{inp_path}/*{template_name}")

    for tab_filename in flagfrac_tab_names:

        field_name = os.path.basename(tab_filename).split(template_name)[0].split('field_')[1]

        colnames = ['field', 'spw', 'uvdist', 'frac']

        table_dict[field_name] = Table.read(tab_filename, names=colnames, format='ascii')

    return table_dict
