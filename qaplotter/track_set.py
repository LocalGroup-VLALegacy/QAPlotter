
from glob import glob
import os

from .utils import (read_field_data_tables,
                    read_bpcal_data_tables,
                    read_delay_data_tables,
                    read_BPinitialgain_data_tables,
                    read_phaseshortgaincal_data_tables,
                    read_ampgaincal_time_data_tables,
                    read_ampgaincal_freq_data_tables,
                    read_phasegaincal_data_tables)

from .field_plots import target_scan_figure, calibrator_scan_figure
from .bp_plots import bp_amp_phase_figures

from .amp_phase_cal_plots import (phase_gain_figures, amp_gain_time_figures,
                                  delay_freq_figures, amp_gain_freq_figures)

from .html_linking import (make_all_html_links, make_html_homepage,
                           make_caltable_all_html_links)


def make_field_plots(track_folder, folder, output_folder, save_fieldnames=False,
                     flagging_sheet_link=None, corrs=['RR', 'LL']):
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

    if save_fieldnames:
        field_txtfilename = f"{output_folder}/fieldnames.txt"

        if os.path.exists(field_txtfilename):
            os.remove(field_txtfilename)

        with open(field_txtfilename, 'w') as f:

            for field in fieldnames:
                f.write(f"{field}\n")

    meta_dict_0 = read_field_data_tables(fieldnames[0], folder)[1]['amp_time']

    for i, field in enumerate(fieldnames):

        table_dict, meta_dict = read_field_data_tables(field, folder)

        # Target
        if len(table_dict.keys()) == 3:

            fig = target_scan_figure(table_dict, meta_dict, show=False, corrs=corrs)

        elif len(table_dict.keys()) == 8:

            fig = calibrator_scan_figure(table_dict, meta_dict, show=False, corrs=corrs)

        else:
            raise ValueError(f"Found {len(table_dict.keys())} tables for {field} instead of 3 or 7.")

        out_html_name = f"{field}_plotly_interactive.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

    # Make the linking files into the same folder.
    make_all_html_links(flagging_sheet_link, output_folder, fieldnames, meta_dict_0)


def make_all_cal_plots(track_folder, folder, output_folder,
                       flagging_sheet_link=None):

    # Bandpass plots

    table_dict, meta_dict = read_bpcal_data_tables(folder)

    meta_dict_0 = meta_dict['amp'][list(meta_dict['amp'].keys())[0]]

    figs = bp_amp_phase_figures(table_dict, meta_dict,
                                nspw_per_figure=4)

    # Make output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    fig_names = {}
    label = 'Bandpass'

    for i, fig in enumerate(figs):

        out_html_name = f"BP_amp_phase_plotly_interactive_{i}.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

        fig_names[f"{label} {i+1}"] = out_html_name

    # Delay
    table_dict, meta_dict = read_delay_data_tables(folder)

    figs = delay_freq_figures(table_dict, meta_dict,
                              nant_per_figure=8,)
    label = 'Delay'

    for i, fig in enumerate(figs):

        out_html_name = f"delay_plotly_interactive_{i}.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

        fig_names[f"{label} {i+1}"] = out_html_name

    # BP init phase
    table_dict, meta_dict = read_BPinitialgain_data_tables(folder)
    label = 'BP Initial Gain'

    figs = phase_gain_figures(table_dict, meta_dict,
                              nant_per_figure=8,)

    for i, fig in enumerate(figs):

        out_html_name = f"BPinit_phase_plotly_interactive_{i}.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

        fig_names[f"{label} {i+1}"] = out_html_name

    # phase short gain cal
    table_dict, meta_dict = read_phaseshortgaincal_data_tables(folder)
    label = 'Phase (short) gain'

    figs = phase_gain_figures(table_dict, meta_dict,
                              nant_per_figure=8,)

    for i, fig in enumerate(figs):

        out_html_name = f"phaseshortgaincal_plotly_interactive_{i}.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

        fig_names[f"{label} {i+1}"] = out_html_name

    # Amp gain cal time
    table_dict, meta_dict = read_ampgaincal_time_data_tables(folder)
    label = 'Amp Gain Time'

    figs = amp_gain_time_figures(table_dict, meta_dict,
                                 nant_per_figure=8,)

    for i, fig in enumerate(figs):

        out_html_name = f"ampgain_time_plotly_interactive_{i}.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

        fig_names[f"{label} {i+1}"] = out_html_name

    # Amp gain cal freq
    table_dict, meta_dict = read_ampgaincal_freq_data_tables(folder)

    figs = amp_gain_freq_figures(table_dict, meta_dict,
                                 nant_per_figure=8,)
    label = 'Amp Gain Freq'

    for i, fig in enumerate(figs):

        out_html_name = f"ampgain_freq_plotly_interactive_{i}.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

        fig_names[f"{label} {i+1}"] = out_html_name

    # Phase gain cal
    table_dict, meta_dict = read_phasegaincal_data_tables(folder)
    label = 'Phase Gain Time'

    figs = phase_gain_figures(table_dict, meta_dict,
                              nant_per_figure=8,)

    for i, fig in enumerate(figs):

        out_html_name = f"phasegain_time_plotly_interactive_{i}.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

        fig_names[f"{label} {i+1}"] = out_html_name

    make_caltable_all_html_links(flagging_sheet_link, output_folder, fig_names, meta_dict_0)


def make_all_plots(msname=None,
                   folder_fields="scan_plots_txt",
                   output_folder_fields="scan_plots_QAplots",
                #    folder_BPs="final_caltable_txt",
                #    output_folder_BPs="final_caltable_QAplots",
                   folder_cals="final_caltable_txt",
                   output_folder_cals="final_caltable_QAplots",
                   save_fieldnames=True,
                   flagging_sheet_link=None,
                   corrs=['RR', 'LL']):
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
    flagging_sheet_link : str, optional
        Link to the sheet where manual flags can be added.
    corrs : list, optional
        Give which correlations to show in the plots. Default is ['LL', 'RR']. To show
        the cross terms, give: ['LL', 'RR', 'LR', 'RL'].

    '''

    # TODO: add a metadata reader. Most likely include this as a save file from the pipeline to be read in.
    # This will eventually be used to contain more info about the track.
    # For now, it's just the name. We default to the parent folder's name when none is given.
    ms_info_dict = {}

    if msname is None:
        msname = os.path.abspath(".").split("/")[-1]

    ms_info_dict['vis'] = msname

    track_folder = msname

    make_html_homepage(".", ms_info_dict, flagging_sheet_link=flagging_sheet_link)

    make_field_plots(flagging_sheet_link, folder_fields, output_folder_fields,
                     save_fieldnames=save_fieldnames,
                     corrs=corrs)

    make_all_cal_plots(flagging_sheet_link, folder_cals, output_folder_cals)
