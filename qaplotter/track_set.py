
from glob import glob
import os

from .utils import read_field_data_tables
from .basic_plots import target_scan_figure, calibrator_scan_figure


def make_field_plots(folder, output_folder):
    '''
    Make all scan plots into an HTML for each target.
    '''

    # Grab all text files.
    txt_files = glob(f"{folder}/*.txt")

    # Make output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    def get_fieldname(filename):
        return "_".join(os.path.basename(filename).split("_")[1:-2])

    fieldnames = [get_fieldname(filename) for filename in txt_files]

    # Get unique names only
    fieldnames = list(set(fieldnames))

    for field in fieldnames:

        table_dict, meta_dict = read_field_data_tables(field, folder)

        # Target
        if len(table_dict.keys()) == 3:

            fig = target_scan_figure(table_dict, meta_dict, show=False)

        elif len(table_dict.keys()) == 7:

            fig = calibrator_scan_figure(table_dict, meta_dict, show=False)

        else:
            raise ValueError(f"Found {len(table_dict.keys())} tables for {field} instead of 3 or 7.")

        out_html_name = f"{field}_plotly_interactive.html"
        fig.write_html(f"{output_folder}/{out_html_name}")
