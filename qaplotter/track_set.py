
from glob import glob
import os

from .utils import read_field_data_tables, read_bpcal_data_tables
from .field_plots import target_scan_figure, calibrator_scan_figure
from .bp_plots import bp_amp_phase_figures
from .html_linking import make_all_html_links, make_bandpass_all_html_links


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

    meta_dict_0 = meta_dict['amp'][list(meta_dict['amp'].keys())[0]]

    figs = bp_amp_phase_figures(table_dict, meta_dict,
                                nspw_per_figure=4)

    # Make output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    fig_names = []

    for i, fig in enumerate(figs):

        out_html_name = f"BP_amp_phase_plotly_interactive_{i}.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

        fig_names.append(out_html_name)

    make_bandpass_all_html_links(output_folder, fig_names, meta_dict_0)


def make_all_plots(folder_fields="scan_plots_txt",
                   output_folder_fields="scan_plots_QAplots",
                   folder_BPs="finalBPcal_txt",
                   output_folder_BPs="finalBPcal_QAplots"):
    '''
    Make both the field and BP cal plots based on the standard pipeline folder names defined
    in the ReductionPipeline package (https://github.com/LocalGroup-VLALegacy/ReductionPipeline).

    Additional QA plot types will be added here to create a single call to produce all QA plots.

    Parameters
    ----------
    folder_fields : str, optional
        Folder where the txt files per field are located.
    output_folder_fields : str, optional
        Output folder to place the interactive HTML figures per field.
    folder_BPs : str, optional
        Folder where the txt files for bandpass solutions per SPW are located.
    output_folder_BPs : str, optional
        Output folder to place the interactive HTML figures per bandpass SPW solution.

    '''

    make_field_plots(folder_fields, output_folder_fields)

    make_BP_plots(folder_BPs, output_folder_BPs)
