
from glob import glob
import os
import warnings

from astropy.table import table
import numpy as np

from .utils import (read_field_data_tables,
                    read_bpcal_data_tables,
                    read_delay_data_tables,
                    read_BPinitialgain_data_tables,
                    read_phaseshortgaincal_data_tables,
                    read_ampgaincal_time_data_tables,
                    read_ampgaincal_freq_data_tables,
                    read_phasegaincal_data_tables,
                    load_spwdict)

from .parse_weblog import (get_field_intents,
                           extract_manual_flagging_log,
                           extract_msname)

from .field_plots import target_scan_figure, calibrator_scan_figure

from .target_summary_plots import target_summary_ampfreq_figure, target_summary_amptime_figure

from .quicklook_target_imaging import make_quicklook_figures

from .bp_plots import bp_amp_phase_figures

from .amp_phase_cal_plots import (phase_gain_figures, amp_gain_time_figures,
                                  delay_freq_figures, amp_gain_freq_figures)

from .html_linking import (make_all_html_links, make_html_homepage,
                           make_caltable_all_html_links,
                           make_quicklook_html_links)


def make_field_plots(msname, folder, output_folder, save_fieldnames=False,
                     flagging_sheet_link=None, corrs=['RR', 'LL'],
                     spw_dict=None, show_target_linesonly=True):
    '''
    Make all scan plots into an HTML for each target.
    '''

    # Grab all text files.
    txt_files = glob(f"{folder}/*.txt")

    # Make output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    def get_fieldname(filename):
        if "scan_" in filename:
            return "_".join(os.path.basename(filename).split("_")[1:-3])
        return "_".join(os.path.basename(filename).split("_")[1:-2])

    fieldnames = [get_fieldname(filename) for filename in txt_files
                  if os.path.getsize(filename) > 1000]

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

    field_intents = {}

    for i, field in enumerate(fieldnames):

        table_dict, meta_dict = read_field_data_tables(field, folder)

        try:
            field_intent = get_field_intents(field, msname)
        except Exception as exc:
            warnings.warn(f"Unable to find field intent. Raise exception: {exc}")
            field_intent = ''

        meta_dict['intent'] = field_intent

        field_intents[field] = field_intent

        # Target
        if len(table_dict.keys()) == 3:

            fig = target_scan_figure(table_dict, meta_dict, show=False, corrs=corrs,
                                     spw_dict=spw_dict,
                                     show_linesonly=show_target_linesonly)

        # 10 with amp/phase versus ant 1. 8 without.
        elif len(table_dict.keys()) == 10 or len(table_dict.keys()) == 8:

            fig = calibrator_scan_figure(table_dict, meta_dict, show=False, corrs=corrs,
                                         spw_dict=spw_dict)

        else:
            raise ValueError(f"Found {len(table_dict.keys())} tables for {field} instead of 3 or 10.")

        out_html_name = f"{field}_plotly_interactive.html"
        fig.write_html(f"{output_folder}/{out_html_name}")

    # Create summary tables using all target fields
    target_fields = []

    for i, field in enumerate(fieldnames):

        table_dict, meta_dict = read_field_data_tables(field, folder)

        try:
            field_intent = get_field_intents(field, msname)
        except Exception as exc:
            warnings.warn(f"Unable to find field intent. Raise exception: {exc}")
            field_intent = ''

        if "target" in field_intent.lower():
            target_fields.append(field)

    # Create target field summary plots
    # First check that there were target fields.

    if len(target_fields) > 0:

        try:
            fig_summ_time = target_summary_amptime_figure(target_fields, folder,
                                                        corrs=corrs,
                                                        spw_dict=spw_dict,
                                                        show_linesonly=show_target_linesonly)
            out_html_name = f"target_amptime_summary_plotly_interactive.html"
            fig_summ_time.write_html(f"{output_folder}/{out_html_name}")
        except Exception as exc:
            warnings.warn("Unable to make summary amp-time figure."
                          f" Raise exception {exc}")

        try:
            fig_summ_freq = target_summary_ampfreq_figure(target_fields, folder,
                                                        corrs=corrs,
                                                        spw_dict=spw_dict,
                                                        show_linesonly=show_target_linesonly)
            out_html_name = f"target_ampfreq_summary_plotly_interactive.html"
            fig_summ_freq.write_html(f"{output_folder}/{out_html_name}")
        except Exception as exc:
            warnings.warn("Unable to make summary amp-freq figure."
                          f" Raise exception {exc}")

    # Make the linking files into the same folder.
    make_all_html_links(flagging_sheet_link, output_folder, field_intents, meta_dict_0)


def make_all_cal_plots(flagging_sheet_link, folder, output_folder):

    fig_names = {}

    # Bandpass plots

    table_dict, meta_dict = read_bpcal_data_tables(folder)

    # Check if files exist. If not, skip.
    key0 = list(table_dict.keys())[0]
    if len(table_dict[key0]) > 0:

        meta_dict_0 = meta_dict['amp'][list(meta_dict['amp'].keys())[0]]

        figs = bp_amp_phase_figures(table_dict, meta_dict,
                                    nspw_per_figure=4)

        # Make output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        label = 'Bandpass'

        for i, fig in enumerate(figs):

            out_html_name = f"BP_amp_phase_plotly_interactive_{i}.html"
            fig.write_html(f"{output_folder}/{out_html_name}")

            fig_names[f"{label} {i+1}"] = out_html_name

    # Phase gain cal
    table_dict, meta_dict = read_phasegaincal_data_tables(folder)

    key0 = list(table_dict.keys())[0]
    if len(table_dict[key0]) > 0:

        label = 'Phase Gain Time'

        figs = phase_gain_figures(table_dict, meta_dict,
                                nant_per_figure=8,)

        for i, fig in enumerate(figs):

            out_html_name = f"phasegain_time_plotly_interactive_{i}.html"
            fig.write_html(f"{output_folder}/{out_html_name}")

            fig_names[f"{label} {i+1}"] = out_html_name

    # Amp gain cal time
    table_dict, meta_dict = read_ampgaincal_time_data_tables(folder)

    key0 = list(table_dict.keys())[0]
    if len(table_dict[key0]) > 0:

        label = 'Amp Gain Time'

        figs = amp_gain_time_figures(table_dict, meta_dict,
                                    nant_per_figure=8,)

        for i, fig in enumerate(figs):

            out_html_name = f"ampgain_time_plotly_interactive_{i}.html"
            fig.write_html(f"{output_folder}/{out_html_name}")

            fig_names[f"{label} {i+1}"] = out_html_name

    # Amp gain cal freq
    table_dict, meta_dict = read_ampgaincal_freq_data_tables(folder)

    key0 = list(table_dict.keys())[0]
    if len(table_dict[key0]) > 0:

        figs = amp_gain_freq_figures(table_dict, meta_dict,
                                    nant_per_figure=8,)
        label = 'Amp Gain Freq'

        for i, fig in enumerate(figs):

            out_html_name = f"ampgain_freq_plotly_interactive_{i}.html"
            fig.write_html(f"{output_folder}/{out_html_name}")

            fig_names[f"{label} {i+1}"] = out_html_name

    # Delay
    table_dict, meta_dict = read_delay_data_tables(folder)

    # Check if files exist. If not, skip.
    key0 = list(table_dict.keys())[0]
    if len(table_dict[key0]) > 0:

        figs = delay_freq_figures(table_dict, meta_dict,
                                nant_per_figure=8,)
        label = 'Delay'

        for i, fig in enumerate(figs):

            out_html_name = f"delay_plotly_interactive_{i}.html"
            fig.write_html(f"{output_folder}/{out_html_name}")

            fig_names[f"{label} {i+1}"] = out_html_name

    # phase short gain cal

    # Check if files exist. If not, skip.
    table_dict, meta_dict = read_phaseshortgaincal_data_tables(folder)

    key0 = list(table_dict.keys())[0]
    if len(table_dict[key0]) > 0:

        label = 'Phase (short) gain'

        figs = phase_gain_figures(table_dict, meta_dict,
                                nant_per_figure=8,)

        for i, fig in enumerate(figs):

            out_html_name = f"phaseshortgaincal_plotly_interactive_{i}.html"
            fig.write_html(f"{output_folder}/{out_html_name}")

            fig_names[f"{label} {i+1}"] = out_html_name

    # BP init phase
    table_dict, meta_dict = read_BPinitialgain_data_tables(folder)

    # Check if files exist. If not, skip.
    key0 = list(table_dict.keys())[0]
    if len(table_dict[key0]) > 0:

        figs = phase_gain_figures(table_dict, meta_dict,
                                nant_per_figure=8,)

        label = 'BP Initial Gain'

        for i, fig in enumerate(figs):

            out_html_name = f"BPinit_phase_plotly_interactive_{i}.html"
            fig.write_html(f"{output_folder}/{out_html_name}")

            fig_names[f"{label} {i+1}"] = out_html_name

    if len(fig_names) > 0:

        make_caltable_all_html_links(flagging_sheet_link, output_folder, fig_names, meta_dict_0)


def make_all_quicklook_plots(flagging_sheet_link, folder="quicklook_imaging",
                             output_folder="quicklook_imaging_figures"):

    # Generate the quicklook plots.
    target_dict, summary_filenames = make_quicklook_figures(folder, output_folder)

    # Identify if these are continuum or line plots
    # The line plots will tend to be larger, so we just want to
    # decrease the number of fields per page for the lines.
    filenames = glob(f"{output_folder}/*.html")
    if any(["continuum" in filename for filename in filenames]):
        fields_per_page = 5
    else:
        fields_per_page = 3

    make_quicklook_html_links(flagging_sheet_link, output_folder, target_dict,
                              summary_filenames,
                              fields_per_page=fields_per_page)


def make_all_plots(msname=None,
                   folder_fields="scan_plots_txt",
                   output_folder_fields="scan_plots_QAplots",
                   folder_BPs="finalBPcal_txt",
                   folder_cals="final_caltable_txt",
                   output_folder_cals="final_caltable_QAplots",
                   folder_qlimg="quicklook_imaging",
                   output_folder_qlimg="quicklook_imaging_figures",
                   save_fieldnames=True,
                   flagging_sheet_link=None,
                   corrs=['RR', 'LL'],
                   manualflag_tablename='manualflag_check.html',
                   spwdict_filename="spw_definitions.npy",
                   show_target_linesonly=True,
                   ):
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

    ms_info_dict = {}

    if msname is None:
        msname = extract_msname(weblog_name='weblog')

    # If it's STILL None, raise an exception.
    if msname is None:
        raise Exception("Unable to identify the MS or SDM name from the weblog."
                        " Please give the name using the 'msname' kwarg.")

        # except ValueError:
        #     # This only follows the convention we're using for product names in LGLBS
        #     # It is not general and when it does not match the expected format from the
        #     # SDM name, some features will be missing in the QA products.
        #     warnings.warn("Unable to extract MS name from the weblog. "
        #                   "Assuming parent directory name for MS.")
        #     msname = os.path.abspath(".").split("/")[-1]

    # Check if all product folders exist. If not, raise an exception.
    if not os.path.exists(folder_fields):
        raise Exception(f"Folder {folder_fields} does not exist.")

    if not os.path.exists(folder_cals):
        raise Exception(f"Folder {folder_cals} does not exist.")

    if not os.path.exists(folder_qlimg):
        raise Exception(f"Folder {folder_qlimg} does not exist.")

    ms_info_dict['vis'] = msname

    # Try parsing the hifv_flagdata log to check for issues in our
    # manual flagging commands.
    try:
        warn_tab = extract_manual_flagging_log(msname)
        warn_tab.write(manualflag_tablename, overwrite=True)
    except Exception as exc:
        warnings.warn(f"Encountered exception: {exc}")

    if os.path.exists(spwdict_filename):
        print(f"Found spw dictionary file.")
        spw_dict = load_spwdict(spwdict_filename)
    else:
        spw_dict = None
        print(f"NO spw dictionary file found.")

    make_html_homepage(".", ms_info_dict, flagging_sheet_link=flagging_sheet_link,
                       manualflag_tablename=manualflag_tablename)

    # Turn off show_target_linesonly for continuum-only cases
    if show_target_linesonly:
        is_continuum_spw = []
        if spw_dict is not None:
            for key in spw_dict:
                # Filter out the continuum SPWs
                is_continuum_spw.append("continuum" in spw_dict[key]['label'])

        if np.all(is_continuum_spw):
            show_target_linesonly = False
            print("Continuum-only SPWs detected. Disabling show_target_linesonly.")

    make_field_plots(ms_info_dict['vis'], folder_fields, output_folder_fields,
                     save_fieldnames=save_fieldnames,
                     corrs=corrs, spw_dict=spw_dict,
                     flagging_sheet_link=flagging_sheet_link,
                     show_target_linesonly=show_target_linesonly)

    # For older pipeline runs, only the BP txt files will be available.
    if not os.path.exists(folder_cals):

        if os.path.exists(folder_BPs):
            folder_cals = folder_BPs

        else:
            print("No cal plot txt files were found. Skipping.")
            return

    # Calibration plots
    make_all_cal_plots(flagging_sheet_link, folder_cals, output_folder_cals)

    if os.path.exists(folder_qlimg):
        # Quicklook target images
        make_all_quicklook_plots(flagging_sheet_link, folder_qlimg, output_folder_qlimg)

    else:
        print("No quicklook images were found. Skipping.")
