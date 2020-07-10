
from glob import glob
import os

from .utils import read_field_data_tables, read_bpcal_data_tables
from .field_plots import target_scan_figure, calibrator_scan_figure
from .bp_plots import bp_amp_phase_figures
from .html_linking import make_all_html_links


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
    fieldnames = sorted(list(set(fieldnames)))

    meta_dict_0 = read_field_data_tables(fieldnames[0], folder)[1]['amp_time']

    for i, field in enumerate(fieldnames):

        table_dict, meta_dict = read_field_data_tables(field, folder)

        # Target
        if len(table_dict.keys()) == 3:

            fig = target_scan_figure(table_dict, meta_dict, show=False)

        elif len(table_dict.keys()) == 8:

            fig = calibrator_scan_figure(table_dict, meta_dict, show=False)

        else:
            raise ValueError(f"Found {len(table_dict.keys())} tables for {field} instead of 3 or 7.")

        out_html_name = f"{field}_plotly_interactive.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

    # Make the linking files into the same folder.
    make_all_html_links(output_folder, fieldnames, meta_dict_0)


def make_BP_plots(folder, output_folder):

    table_dict, meta_dict = read_bpcal_data_tables(folder)

    figs = bp_amp_phase_figures(table_dict, meta_dict,
                                nspw_per_figure=4)

    # Make output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    for i, fig in enumerate(figs):

        out_html_name = f"BP_amp_phase_plotly_interactive_{i}.html"
        fig.write_html(f"{output_folder}/{out_html_name}")
