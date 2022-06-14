
'''
Functions to extract information from the pipeline HTML weblog.
'''

from multiprocessing.sharedctypes import Value
from bs4 import BeautifulSoup
import pandas as pd
import re
from astropy.table import Table
import numpy as np
import os
import warnings


def extract_source_table(msname, weblog_name='weblog'):

    filename = f'{weblog_name}/html/sessionsession_1/{msname}/t2-2-1.html'

    with open(filename) as f:
        html_doc = f.read()

    soup = BeautifulSoup(html_doc, 'html.parser')

    html_table = soup.find('table')

    table = pd.read_html(html_table.decode())

    if isinstance(table, list):
        table = table[0]

    return table


def get_field_intents(fieldname, msname, weblog_name='weblog'):

    table = extract_source_table(msname, weblog_name=weblog_name)

    is_field = table['Source Name'] == fieldname

    this_intent = table['Intent'][is_field['Source Name']]['Intent']

    intent_string = this_intent[this_intent.index[0]].replace(" ", "")

    # Pop out sys config, unless it's the only one:
    intent_list = intent_string.split(',')

    if len(intent_list) > 1:
        if 'SYSTEM_CONFIGURATION' in intent_list:
            intent_list.remove('SYSTEM_CONFIGURATION')

        intent_string = ",".join(intent_list)

    return intent_string


def extract_manual_flagging_log(msname, weblog_name='weblog'):
    '''
    Extract the log for the manual flagging commands to check if
    any flags were not applied due to a typo or error.
    '''

    if 'speclines' in msname:
        stage_num = 2
    else:
        # +1 for Hanning smoothing.
        stage_num = 3

    log_filename = f'{weblog_name}/html/stage{stage_num}/casapy.log'
    flag_filename = f'{weblog_name}/html/stage{stage_num}/{msname}-agent_flagcmds.txt'

    if os.path.exists(log_filename):
        with open(log_filename) as f:
            log_lines = f.readlines()
    else:
        raise ValueError(f"Unable to find log {log_filename}")

    if os.path.exists(flag_filename):
        with open(flag_filename) as f:
            flag_lines = f.readlines()
    else:
        raise ValueError(f"Unable to find flag commands in {flag_filename}")

    begin_task_match = "Begin Task: flagdata"
    end_task_match = "Running the agentflagger tool"

    begin_task_count = 0
    end_task_count = 0

    start_slice = None
    end_slice = None

    ii = 0
    while True:

        if begin_task_match in log_lines[ii]:
            begin_task_count += 1

            if begin_task_count == 2:
                start_slice = ii

        if end_task_match in log_lines[ii]:
            end_task_count += 1

            if end_task_count == 2:
                end_slice = ii

        ii += 1

        if start_slice is not None and end_slice is not None:
            break

    if start_slice is None or end_slice is None:
        raise ValueError("Unable to identify manual flagdata call in log.")

    # Go through line-by-line where warning or errors in the log are found
    # Line, comment, command
    warning_command_list = []

    statuses = ["WARN", 'SEVERE']
    # for jj in range(start_slice, end_slice + 1):
    jj = start_slice

    while True:
        # Check if WARN or ERROR in the line. If so, extract which command its coming from

        if jj >= end_slice + 1:
            break

        if not any([status in log_lines[jj] for status in statuses]):
            jj += 1
            continue

        # Skip the state expressions that are enabled by default
        if "State Expression" in log_lines[jj]:
            jj += 2
            continue

        # We often will flag the upper end of a SPW with +1 channels
        # e.g. 2:60~64 for a 64 channel SPW. CASA consider the 0th channel
        # so technically it should be 60~63. CASA fixes this but raises a harmless
        # warning that we can skip:
        if "parser::MSSpwIndex::convertToChannelIndex" in log_lines[jj]:
            jj += 1
            continue

        source_string, warn_string = log_lines[jj].split("\t")[-2:]

        # We expect that the only int in the message corresponds to the flag in
        # the manual flagging file (flag_lines). e.g. Manual_2
        int_check = re.search(r'\d+', warn_string)
        if int_check is None:
            flag_cmd = "Unable to identify from log."
        else:
            idx_flag = int(int_check.group())
            flag_cmd = flag_lines[idx_flag]

        if f"{source_string}+" in log_lines[jj+1]:
            warn_comment = log_lines[jj+1].split("\t")[-1]
            jj += 2
        else:
            warn_comment = ""
            jj += 1

        warning_command_list.append([warn_string, warn_comment, flag_cmd])

    # No warnings/errors? Great!
    if len(warning_command_list) == 0:
        warning_command_list.append(["No issues found for manual flagging.", "Good job!", ""])

    warning_command_list = np.array(warning_command_list)

    # Export as an astropy table
    tab = Table(warning_command_list, names=['Log error', 'Log comment', "Flagging command"])

    return tab


def extract_msname(weblog_name='weblog'):
    '''
    Find the MS name in the weblog from the listing in
    'weblog/html/sessionsession_1/'.
    '''

    try:
        msnames = os.listdir(f"{weblog_name}/html/sessionsession_1")
    except Exception as exc:
        warnings.warn(f"Encountered exception {exc}")
        return None

    # NOTE: One weblog I pulled down had hidden files/folders. Check and remove these
    # if present:
    msnames = [val for val in msnames if not val.startswith(".") ]

    if len(msnames) > 1:
        raise ValueError(f"Found multiple names: {msnames}"
                         " Cannot handle pipeline runs with multiple MSs.")

    if len(msnames) == 0:
        raise ValueError(f"Unable to find any folders in {weblog_name}/html/sessionsession_1")

    return msnames[0]
