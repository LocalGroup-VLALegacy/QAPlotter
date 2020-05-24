
from astropy.table import Table


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
