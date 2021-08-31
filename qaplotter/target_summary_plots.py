
import enum
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import astropy.table as table


# from .utils import read_field_data_tables
from qaplotter.utils import read_field_data_tables

# from .utils import vla_time_conversion
from qaplotter.utils import vla_time_conversion

# Define a common set of markers to plot for different correlations
# e.g. RR, LL, RL, LR
markers = ['circle', 'cross', 'triangle-up', 'triangle-down']


def target_summary_amptime_figure(fields, folder, show=False,
                                  scatter_plot=go.Scattergl,
                                  corrs=['RR', 'LL']):
    '''
    Make a N SPW-panel figure over all targets.
    '''

    txt_files = glob(f"{folder}/*.txt")

    # This summary only uses amp_time
    exp_keys = {'amp_time': {'x': 'time', 'y': 'y', 'row': 1, 'col': 2,
                             "title": "Amp vs. Time<br>Freq & Baseline avg"}}

    # Find all unique SPW nums over all target fields
    spw_nums = []
    for field in fields:
        table_dict = read_field_data_tables(field, folder)[0]

        for key in exp_keys:
            if key not in table_dict.keys():
                raise KeyError(f"Required dict key {key} not found.")

        spw_nums.extend(list(set(table_dict['amp_time']['spw'])))

        spw_nums = list(set(spw_nums))

    subplot_titles = [f"SPW {spw}" for spw in spw_nums]

    ncol = 3
    nrow = len(spw_nums) // 3
    if len(spw_nums) % 3 > 0:
        nrow += 1

    fig = make_subplots(rows=nrow, cols=ncol, subplot_titles=subplot_titles,
                        shared_xaxes=False, shared_yaxes=False)

    hovertemplate = 'Field name: %{customdata[0]}<br>Field number: %{customdata[1]}<br>Scan: %{customdata[2]}<br>SPW: %{customdata[3]}<br>Corr: %{customdata[4]}'

    def make_casa_timestring(x):

        datetime_vals = vla_time_conversion(x)

        return [dtime.strftime("%Y/%m/%d/%H:%M:%S.%f")[:-5]
                for dtime in datetime_vals]

    colors_dict = {"Field": [],
                   "Scan": [],
                   "Corr": []}

    # Convert the time axis values to strings
    # Time is always the x-axis.
    if "time" in key:
        def format_xvals(x):
            datetime_vals = vla_time_conversion(x)

            return datetime_vals
    else:
        def format_xvals(x):
            return x

    for nfield, field in enumerate(fields):
        print(f"On {field}")

        table_dict, meta_dict = read_field_data_tables(field, folder)

        tab_data = table_dict['amp_time']

        # Add a fieldname column
        tab_data.add_column(table.Column([field] * len(tab_data),
                                         name='fieldname'))


        field_mask = tab_data['fieldname'] == field

        for nspw, spw in enumerate(spw_nums):

            spw_mask = tab_data['spw'] == spw

            if corrs is None:
                corrs = np.unique(tab_data['corr'][spw_mask].tolist())

            for nc, (corr, marker) in enumerate(zip(corrs, markers)):

                corr_mask = (tab_data['corr'] == corr).tolist()

                all_mask = spw_mask & field_mask & corr_mask

                custom_data = np.vstack((tab_data['fieldname'][all_mask].tolist(),
                                        tab_data['field'][all_mask].tolist(),
                                        tab_data['scan'][all_mask].tolist(),
                                        tab_data['spw'][all_mask].tolist(),
                                        tab_data['corr'][all_mask].tolist())).T

                # We're also going to record colors based on Scan and field
                # SPW are unique and the colour palette has 11 colours.
                field_data = tab_data['fieldname'][all_mask].tolist()

                colors_dict['Field'].append([px.colors.qualitative.Safe[nfield % 11] for _ in range(len(field_data))])

                # Want to map to unique scan values, not the scan numbers themselves
                # (i.e., 50, 60, 70 -> 0, 1, 2)
                scan_data = tab_data['scan'][all_mask].tolist()

                scan_map_dict = {}
                for n_uniq, scan in enumerate(np.unique(scan_data)):
                    scan_map_dict[scan] = n_uniq

                colors_dict['Scan'].append([px.colors.qualitative.Safe[scan_map_dict[scan] % 11]
                                            for scan in scan_data])

                # And corr
                corr_data = tab_data['corr'][all_mask].tolist()

                colors_dict['Corr'].append([px.colors.qualitative.Safe[nc % 11]
                                            for _ in range(len(corr_data))])

                fig.append_trace(scatter_plot(x=format_xvals(tab_data['x'][all_mask]),
                                            y=tab_data['y'][all_mask],
                                            mode='markers',
                                            marker=dict(symbol=marker,
                                                        size=7,
                                                        color=colors_dict['Field'][-1]),
                                            customdata=custom_data,
                                            hovertemplate=hovertemplate,
                                            # name=f"SPW {spw}",
                                            name=field,
                                            legendgroup=str(field),
                                            showlegend=True if (nspw == 0 and nc == 0) else False),
                                row=(nspw // 3)+1, col=nspw % 3 + 1,
                                )

            if nspw == 0:
                label = ""
            else:
                label = f"{nspw+1}"

            fig['layout'][f'xaxis{label}']['title'] = 'Time (UTC)'
            fig['layout'][f'yaxis{label}']['title'] = 'Amplitude (Jy)'

    # Make custom time ticks in a nicer format.
    # Also scale with zoom to stop tick labels from overlapping in different subplots.
    for key in exp_keys:
        if "time" not in key:
            continue

        fig.update_xaxes(rangeslider_visible=False,
                        tickformatstops=[dict(dtickrange=[None, 1000e3], value="%H:%M:%S"),
                                        dict(dtickrange=[1000e3, None], value="%H:%M:%S"),
                                        ],
                        row=exp_keys[key]['row'],
                        col=exp_keys[key]['col'])

    fig.update_xaxes(nticks=8)
    fig.update_yaxes(nticks=8)

    fig.update_layout(
        title=exp_keys['amp_time']['title'],
        font=dict(family="Courier New, monospace",
                  size=15,
                  color="#7f7f7f")
    )

    updatemenus = go.layout.Updatemenu(type='buttons',
                                       direction='left',
                                       showactive=True,
                                       x=1.01,
                                       xanchor="right",
                                       y=1.15,
                                       yanchor="top",
                                       buttons=list([dict(label='Field',
                                                          method='update',
                                                          args=[{'marker.color': [col for col in colors_dict['Field']]}],
                                                          ),

                                                    dict(label='Scan',
                                                         method='update',
                                                         args=[{'marker.color': [col for col in colors_dict['Scan']]}],
                                                         ),

                                                    dict(label='Corr',
                                                         method='update',
                                                         args=[{'marker.color': [col for col in colors_dict['Corr']]}],
                                                         ),
                                                     ]))

    fig.update_layout(updatemenus=[updatemenus],
                      autosize=True,
                      height=300 * nrow,
                      margin=dict(t=100, pad=4),)

    if show:
        fig.show()

    return fig


def target_summary_ampfreq_figure(fields, folder, show=False,
                                  scatter_plot=go.Scattergl,
                                  corrs=['RR', 'LL']):
    '''
    Make a N SPW-panel figure over all targets.
    '''

    txt_files = glob(f"{folder}/*.txt")

    # This summary only uses amp_time
    exp_keys = {'amp_chan': {'x': 'freq', 'y': 'y', 'row': 1, 'col': 1,
                             "title": "Amp vs. Freq<br>Time & Baseline avg"}}

    # Find all unique SPW nums over all target fields
    spw_nums = []
    for field in fields:
        table_dict = read_field_data_tables(field, folder)[0]

        for key in exp_keys:
            if key not in table_dict.keys():
                raise KeyError(f"Required dict key {key} not found.")

        spw_nums.extend(list(set(table_dict['amp_time']['spw'])))

        spw_nums = list(set(spw_nums))


    subplot_titles = fields

    ncol = 3
    nrow = len(fields) // ncol
    if len(fields) % ncol > 0:
        nrow += 1

    fig = make_subplots(rows=nrow, cols=ncol, subplot_titles=subplot_titles,
                        shared_xaxes=False, shared_yaxes=False)

    hovertemplate = 'SPW: %{customdata[0]}<br>Field: %{customdata[1]}<br>Field number: %{customdata[2]}<br>Scan: %{customdata[3]}<br>Corr: %{customdata[4]}'

    colors_dict = {"SPW": [], "Scan": [],
                   "Corr": []}

    for nfield, field in enumerate(fields):
        print(f"On {field}")

        table_dict, meta_dict = read_field_data_tables(field, folder)

        tab_data = table_dict['amp_chan']

        # Add a fieldname column
        tab_data.add_column(table.Column([field] * len(tab_data),
                                         name='fieldname'))


        field_mask = tab_data['fieldname'] == field

        for nspw, spw in enumerate(spw_nums):

            spw_mask = tab_data['spw'] == spw

            if corrs is None:
                corrs = np.unique(tab_data['corr'][spw_mask].tolist())

            for nc, (corr, marker) in enumerate(zip(corrs, markers)):

                corr_mask = (tab_data['corr'] == corr).tolist()

                all_mask = spw_mask & field_mask & corr_mask

                custom_data = np.vstack((tab_data['spw'][all_mask].tolist(),
                                        tab_data['fieldname'][all_mask].tolist(),
                                        tab_data['field'][all_mask].tolist(),
                                        tab_data['scan'][all_mask].tolist(),
                                        tab_data['corr'][all_mask].tolist())).T

                # We're also going to record colors based on Scan and field
                # SPW are unique and the colour palette has 11 colours.
                spw_data = tab_data['spw'][all_mask].tolist()

                colors_dict['SPW'].append([px.colors.qualitative.Safe[nspw % 11] for _ in range(len(spw_data))])

                # Want to map to unique scan values, not the scan numbers themselves
                # (i.e., 50, 60, 70 -> 0, 1, 2)
                scan_data = tab_data['scan'][all_mask].tolist()

                scan_map_dict = {}
                for n_uniq, scan in enumerate(np.unique(scan_data)):
                    scan_map_dict[scan] = n_uniq

                colors_dict['Scan'].append([px.colors.qualitative.Safe[scan_map_dict[scan] % 11]
                                            for scan in scan_data])

                # And corr
                corr_data = tab_data['corr'][all_mask].tolist()

                colors_dict['Corr'].append([px.colors.qualitative.Safe[nc % 11]
                                            for _ in range(len(corr_data))])

                fig.append_trace(scatter_plot(x=tab_data['freq'][all_mask],
                                            y=tab_data['y'][all_mask],
                                            mode='markers',
                                            marker=dict(symbol=marker,
                                                        size=7,
                                                        color=colors_dict['SPW'][-1]),
                                            customdata=custom_data,
                                            hovertemplate=hovertemplate,
                                            name=f"SPW {spw}",
                                            legendgroup=str(nspw),
                                            showlegend=True if (nfield == 0 and nc == 0) else False),
                                row=(nfield // ncol)+1, col=nfield % ncol + 1,
                                )

        if nfield == 0:
            label = ""
        else:
            label = f"{nfield+1}"

        fig['layout'][f'xaxis{label}']['title'] = 'Frequency (GHz)'
        fig['layout'][f'yaxis{label}']['title'] = 'Amplitude (Jy)'

    # Here's what needs to be updated for the colors
    # fig['data'][0]['marker']['color']

    fig.update_xaxes(nticks=8)
    fig.update_yaxes(nticks=8)

    fig.update_layout(
        title=exp_keys['amp_chan']['title'],
        font=dict(family="Courier New, monospace",
                  size=15,
                  color="#7f7f7f")
    )

    updatemenus = go.layout.Updatemenu(type='buttons',
                                       direction='left',
                                       showactive=True,
                                       x=1.01,
                                       xanchor="right",
                                       y=1.15,
                                       yanchor="top",
                                       buttons=list([dict(label='SPW',
                                                          method='update',
                                                          args=[{'marker.color': [col for col in colors_dict['SPW']]}],
                                                          ),

                                                    dict(label='Scan',
                                                         method='update',
                                                         args=[{'marker.color': [col for col in colors_dict['Scan']]}],
                                                         ),

                                                    dict(label='Corr',
                                                         method='update',
                                                         args=[{'marker.color': [col for col in colors_dict['Corr']]}],
                                                         ),
                                                     ]))

    fig.update_layout(updatemenus=[updatemenus],
                      autosize=True,
                      height=300 * nrow,
                      margin=dict(t=100, pad=4),)

    if show:
        fig.show()

    return fig


# def target_summary_ampuvdist_figure(fields, folder, show=False,
#                                     scatter_plot=go.Scattergl,
#                                     corrs=['RR', 'LL']):
#     '''
#     Make a N SPW-panel figure over all targets.
#     '''

#     txt_files = glob(f"{folder}/*.txt")

#     # This summary only uses amp_time
#     exp_keys = {'amp_uvdist': {'x': 'x', 'y': 'y', 'row': 1, 'col': 1,
#                                "title": "Amp vs. uv-dist<br>Time & Freq avg"}}

#     # Find all unique SPW nums over all target fields
#     spw_nums = []
#     for field in fields:
#         table_dict = read_field_data_tables(field, folder)[0]

#         for key in exp_keys:
#             if key not in table_dict.keys():
#                 raise KeyError(f"Required dict key {key} not found.")

#         spw_nums.extend(list(set(table_dict['amp_uvdist']['spw'])))

#         spw_nums = list(set(spw_nums))


#     # subplot_titles = [f"SPW {spw}" for spw in spw_nums]
#     subplot_titles = fields

#     ncol = 3
#     nrow = len(fields) // ncol
#     if len(fields) % ncol > 0:
#         nrow += 1

#     fig = make_subplots(rows=nrow, cols=ncol, subplot_titles=subplot_titles,
#                         shared_xaxes=True, shared_yaxes=False)

#     hovertemplate = 'SPW: %{customdata[0]}<br>Field: %{customdata[1]}<br>Field number: %{customdata[2]}<br>Scan: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}'

#     colors_dict = {"SPW": [], "Scan": [],
#                    "Ant1": [],
#                    "Ant2": [],
#                    "Corr": []}

#     for nfield, field in enumerate(fields):
#         print(f"On {field}")

#         table_dict, meta_dict = read_field_data_tables(field, folder)

#         tab_data = table_dict['amp_uvdist']

#         # Add a fieldname column
#         tab_data.add_column(table.Column([field] * len(tab_data),
#                                          name='fieldname'))


#         field_mask = tab_data['fieldname'] == field

#         for nspw, spw in enumerate(spw_nums):

#             spw_mask = tab_data['spw'] == spw

#             if corrs is None:
#                 corrs = np.unique(tab_data['corr'][spw_mask].tolist())

#             for nc, (corr, marker) in enumerate(zip(corrs, markers)):

#                 corr_mask = (tab_data['corr'] == corr).tolist()

#                 all_mask = spw_mask & field_mask & corr_mask

#                 custom_data = np.vstack((tab_data['spw'][all_mask].tolist(),
#                                         tab_data['fieldname'][all_mask].tolist(),
#                                         tab_data['field'][all_mask].tolist(),
#                                         tab_data['scan'][all_mask].tolist(),
#                                         tab_data['corr'][all_mask].tolist(),
#                                         tab_data['ant1name'][all_mask].tolist(),
#                                         tab_data['ant2name'][all_mask].tolist())).T

#                 # We're also going to record colors based on Scan and field
#                 # SPW are unique and the colour palette has 11 colours.
#                 spw_data = tab_data['spw'][all_mask].tolist()

#                 colors_dict['SPW'].append([px.colors.qualitative.Safe[nspw % 11] for _ in range(len(spw_data))])

#                 # Want to map to unique scan values, not the scan numbers themselves
#                 # (i.e., 50, 60, 70 -> 0, 1, 2)
#                 scan_data = tab_data['scan'][all_mask].tolist()

#                 scan_map_dict = {}
#                 for n_uniq, scan in enumerate(np.unique(scan_data)):
#                     scan_map_dict[scan] = n_uniq

#                 colors_dict['Scan'].append([px.colors.qualitative.Safe[scan_map_dict[scan] % 11]
#                                             for scan in scan_data])

#                 # And antennas for colours. Same approach as scans
#                 ant_data = tab_data['ant1name'][all_mask].tolist()

#                 # ant1_map_dict = {}
#                 # for n_uniq, ant in enumerate(np.unique(ant_data)):
#                 #     ant1_map_dict[ant] = n_uniq

#                 # colors_dict['Ant1'].append([px.colors.qualitative.Safe[ant1_map_dict[ant] % 11]
#                 #                             for ant in ant_data])

#                 # ant_data = tab_data['ant2name'][all_mask].tolist()

#                 # ant2_map_dict = {}
#                 # for n_uniq, ant in enumerate(np.unique(ant_data)):
#                 #     ant2_map_dict[ant] = n_uniq

#                 # colors_dict['Ant2'].append([px.colors.qualitative.Safe[ant2_map_dict[ant] % 11]
#                 #                             for ant in ant_data])

#                 # And corr
#                 corr_data = tab_data['corr'][all_mask].tolist()

#                 colors_dict['Corr'].append([px.colors.qualitative.Safe[nc % 11]
#                                             for _ in range(len(corr_data))])

#                 fig.append_trace(scatter_plot(x=tab_data['x'][all_mask],
#                                             y=tab_data['y'][all_mask],
#                                             mode='markers',
#                                             marker=dict(symbol=marker,
#                                                         size=7,
#                                                         color=colors_dict['SPW'][-1]),
#                                             customdata=custom_data,
#                                             hovertemplate=hovertemplate,
#                                             name=f"SPW {spw}",
#                                             legendgroup=str(nspw),
#                                             showlegend=True if (nfield == 0 and nc == 0) else False),
#                                 row=(nfield // ncol)+1, col=nfield % ncol + 1,
#                                 )

#     # Here's what needs to be updated for the colors
#     # fig['data'][0]['marker']['color']

#     fig.update_xaxes(nticks=8)
#     fig.update_yaxes(nticks=8)

#     # fig['layout']['xaxis']['title'] = 'Frequency (GHz)'
#     # fig['layout']['xaxis2']['title'] = 'Time (UTC)'
#     # fig['layout']['xaxis3']['title'] = 'uv-distance (m)'

#     # fig['layout']['yaxis']['title'] = 'Amplitude (Jy)'
#     # fig['layout']['yaxis2']['title'] = 'Amplitude (Jy)'
#     # fig['layout']['yaxis3']['title'] = 'Amplitude (Jy)'

#     # meta = meta_dict['amp_time']

#     fig.update_layout(
#         title=exp_keys['amp_uvdist']['title'],
#         font=dict(family="Courier New, monospace",
#                   size=15,
#                   color="#7f7f7f")
#     )

#     updatemenus = go.layout.Updatemenu(type='buttons',
#                                        direction='left',
#                                        showactive=True,
#                                        x=1.01,
#                                        xanchor="right",
#                                        y=1.15,
#                                        yanchor="top",
#                                        buttons=list([dict(label='SPW',
#                                                           method='update',
#                                                           args=[{'marker.color': [col for col in colors_dict['SPW']]}],
#                                                           ),

#                                                     dict(label='Scan',
#                                                          method='update',
#                                                          args=[{'marker.color': [col for col in colors_dict['Scan']]}],
#                                                          ),

#                                                     dict(label='Ant1',
#                                                          method='update',
#                                                          args=[{'marker.color': [col for col in colors_dict['Ant1']]}],
#                                                          ),

#                                                     dict(label='Ant2',
#                                                          method='update',
#                                                          args=[{'marker.color': [col for col in colors_dict['Ant2']]}],
#                                                          ),

#                                                     dict(label='Corr',
#                                                          method='update',
#                                                          args=[{'marker.color': [col for col in colors_dict['Corr']]}],
#                                                          ),
#                                                      ]))

#     fig.update_layout(updatemenus=[updatemenus],
#                       margin=dict(t=150),
#                       autosize=True,
#                       height=300 * nrow,)
#                     #   width=1500,
#                     #   height=400 * len(spw_nums),)

#     if show:
#         fig.show()

#     return fig
