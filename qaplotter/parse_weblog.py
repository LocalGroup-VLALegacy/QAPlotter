
'''
Functions to extract information from the pipeline HTML weblog.
'''

from bs4 import BeautifulSoup
import pandas as pd


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
