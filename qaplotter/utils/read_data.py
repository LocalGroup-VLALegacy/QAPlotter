
from astropy.table import Table
import os
from glob import glob

osjoin = os.path.join


def read_casa_txt(filename):

    # Grab the meta-data from the header
    meta_lines = skim_header_metadata(filename)

    meta_dict = make_meta_dict(meta_lines)

    # After the plot 0 line
    header_start = len(meta_lines) + 1
    # One for column names, another for units.
    data_start = len(meta_lines) + 3

    tab = Table.read(filename,
                     format='ascii.commented_header',
                     header_start=header_start,
                     data_start=data_start)

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

        name, value = line.split(":")

        name = name.strip(" ")
        value = value.strip(" ")
        value = value.strip("\n")

        data_dict[name] = value

    return data_dict


def read_field_data_tables(fieldname, inp_path):
    '''
    Read in a set of tables for a given `fieldname`. Note that this depends on the function:
    https://github.com/e-koch/ReductionPipeline/blob/master/lband_pipeline/qa_plotting/qa_plot_tools.py#L311.
    Because of this, the read-in is not generalized and may need to be updated.
    '''

    table_dict = dict()
    meta_dict = dict()

    # Table types:
    tab_types = ["amp_chan", "amp_phase", "amp_time", "amp_uvdist", "phase_chan",
                 "phase_time", "phase_uvdist", "ampresid_uvwave"]
    # Target fields will not have the phase tables.
    # Cal fields should have all

    for tab_type in tab_types:
        tabname = osjoin(inp_path, f"field_{fieldname}_{tab_type}.txt")
        if os.path.exists(tabname):
            out = read_casa_txt(tabname)

            table_dict[tab_type] = out[0]
            meta_dict[tab_type] = out[1]

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
