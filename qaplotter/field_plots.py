
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

from .utils import vla_time_conversion

# Define a common set of markers to plot for different correlations
# e.g. RR, LL, RL, LR
markers = ['circle', 'cross', 'triangle-up', 'triangle-down']


def target_scan_figure(table_dict, meta_dict, show=False,
                       scatter_plot=go.Scattergl,
                       corrs=['RR', 'LL']):
    '''
    Make a 3-panel figure for target scans.
    '''

    # There should be 3 fields:
    exp_keys = {'amp_chan': {'x': 'freq', 'y': 'y', 'row': 1, 'col': 1,
                             "title": "Amp vs. Freq<br>Time & Baseline avg"},
                'amp_time': {'x': 'time', 'y': 'y', 'row': 1, 'col': 2,
                             "title": "Amp vs. Time<br>Freq & Baseline avg"},
                'amp_uvdist': {'x': 'x', 'y': 'y', 'row': 1, 'col': 3,
                               "title": "Amp vs. uv-dist<br>Time & Freq avg"}}
    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    subplot_titles = [exp_keys['amp_chan']['title'],
                      exp_keys['amp_time']['title'],
                      exp_keys['amp_uvdist']['title']]

    fig = make_subplots(rows=1, cols=3, subplot_titles=subplot_titles)

    hovertemplate = 'Scan: %{customdata[0]}<br>SPW: %{customdata[1]}<br>Chan: %{customdata[2]}<br>Freq: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}<br>Time: %{customdata[7]}'

    spw_nums = np.unique(table_dict['amp_chan']['spw'].tolist())


    def make_casa_timestring(x):

        datetime_vals = vla_time_conversion(x)

        return [dtime.strftime("%Y/%m/%d/%H:%M:%S.%f")[:-5]
                for dtime in datetime_vals]

    colors_dict = {"SPW": [],
                   "Scan": [],
                   "Ant1": [],
                   "Ant2": [],
                   "Corr": []}

    for nn, key in enumerate(exp_keys):

        # Convert the time axis values to strings
        # Time is always the x-axis.
        if "time" in key:
            def format_xvals(x):
                datetime_vals = vla_time_conversion(x)

                return datetime_vals
        else:
            def format_xvals(x):
                return x

        tab_data = table_dict[key]

        for nspw, spw in enumerate(spw_nums):

            spw_mask = tab_data['spw'] == spw

            if corrs is None:
                corrs = np.unique(tab_data['corr'][spw_mask].tolist())

            for nc, (corr, marker) in enumerate(zip(corrs, markers)):

                corr_mask = (tab_data['corr'] == corr).tolist()

                custom_data = np.vstack((tab_data['scan'][spw_mask & corr_mask].tolist(),
                                         tab_data['spw'][spw_mask & corr_mask].tolist(),
                                         tab_data['chan'][spw_mask & corr_mask].tolist(),
                                         tab_data['freq'][spw_mask & corr_mask].tolist(),
                                         tab_data['corr'][spw_mask & corr_mask].tolist(),
                                         tab_data['ant1name'][spw_mask & corr_mask].tolist(),
                                         tab_data['ant2name'][spw_mask & corr_mask].tolist(),
                                         make_casa_timestring(tab_data['time'][spw_mask & corr_mask].tolist()))).T

                # We're also going to record colors based on Scan and SPW
                # SPW are unique and the colour palette has 11 colours.
                spw_data = tab_data['spw'][spw_mask & corr_mask].tolist()

                colors_dict['SPW'].append([px.colors.qualitative.Safe[nspw % 11] for _ in range(len(spw_data))])

                # Want to map to unique scan values, not the scan numbers themselves
                # (i.e., 50, 60, 70 -> 0, 1, 2)
                scan_data = tab_data['scan'][spw_mask & corr_mask].tolist()

                scan_map_dict = {}
                for n_uniq, scan in enumerate(np.unique(scan_data)):
                    scan_map_dict[scan] = n_uniq

                colors_dict['Scan'].append([px.colors.qualitative.Safe[scan_map_dict[scan] % 11]
                                            for scan in scan_data])

                # And antennas for colours. Same approach as scans
                ant_data = tab_data['ant1name'][spw_mask & corr_mask].tolist()

                ant1_map_dict = {}
                for n_uniq, ant in enumerate(np.unique(ant_data)):
                    ant1_map_dict[ant] = n_uniq

                colors_dict['Ant1'].append([px.colors.qualitative.Safe[ant1_map_dict[ant] % 11]
                                            for ant in ant_data])

                ant_data = tab_data['ant2name'][spw_mask & corr_mask].tolist()

                ant2_map_dict = {}
                for n_uniq, ant in enumerate(np.unique(ant_data)):
                    ant2_map_dict[ant] = n_uniq

                colors_dict['Ant2'].append([px.colors.qualitative.Safe[ant2_map_dict[ant] % 11]
                                            for ant in ant_data])

                # And corr
                colors_dict['Corr'].append([px.colors.qualitative.Safe[nc % 11]
                                            for _ in range(len(spw_data))])

                fig.append_trace(scatter_plot(x=format_xvals(tab_data[exp_keys[key]['x']][spw_mask & corr_mask]),
                                              y=tab_data[exp_keys[key]['y']][spw_mask & corr_mask],
                                              mode='markers',
                                              marker=dict(symbol=marker,
                                                          size=7,
                                                          color=colors_dict['SPW'][-1]),
                                              customdata=custom_data,
                                              hovertemplate=hovertemplate,
                                              name=f"SPW {spw}",
                                              legendgroup=str(spw),
                                              showlegend=True if (nn == 0 and nc == 0) else False),
                                 row=exp_keys[key]['row'], col=exp_keys[key]['col'],
                                 )

    # Here's what needs to be updated for the colors
    # fig['data'][0]['marker']['color']

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

    fig['layout']['xaxis']['title'] = 'Frequency (GHz)'
    fig['layout']['xaxis2']['title'] = 'Time (UTC)'
    fig['layout']['xaxis3']['title'] = 'uv-distance (m)'

    fig['layout']['yaxis']['title'] = 'Amplitude (Jy)'
    fig['layout']['yaxis2']['title'] = 'Amplitude (Jy)'
    fig['layout']['yaxis3']['title'] = 'Amplitude (Jy)'

    meta = meta_dict['amp_time']

    fig.update_layout(
        title=f"Field: {meta['field']}  Intent: {meta_dict['intent']}<br>MS: {meta['vis']}",
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

                                                    dict(label='Ant1',
                                                         method='update',
                                                         args=[{'marker.color': [col for col in colors_dict['Ant1']]}],
                                                         ),

                                                    dict(label='Ant2',
                                                         method='update',
                                                         args=[{'marker.color': [col for col in colors_dict['Ant2']]}],
                                                         ),

                                                    dict(label='Corr',
                                                         method='update',
                                                         args=[{'marker.color': [col for col in colors_dict['Corr']]}],
                                                         ),
                                                     ]))

    fig.update_layout(updatemenus=[updatemenus],
                      margin=dict(t=150))

    if show:
        fig.show()

    return fig


def calibrator_scan_figure(table_dict, meta_dict, show=False, scatter_plot=go.Scattergl,
                           corrs=['RR', 'LL']):
    '''
    Make a 12-panel (4x3) figure for calibrator scans.
    '''

    # There should be 10 fields:
    exp_keys = {'amp_chan': {'x': 'freq', 'y': 'y', 'row': 1, 'col': 1,
                             "title": "Amp vs. Freq<br>Time & Baseline avg"},
                'amp_time': {'x': 'time', 'y': 'y', 'row': 1, 'col': 2,
                             "title": "Amp vs. Time<br>Freq & Baseline avg"},
                'amp_uvdist': {'x': 'x', 'y': 'y', 'row': 1, 'col': 3,
                               "title": "Amp vs. uv-dist<br>Time & Freq avg"},
                'amp_phase': {'x': 'y', 'y': 'x', 'row': 1, 'col': 4,
                              "title": "Amp vs. Phase<br>Time & Freq avg"},
                'phase_chan': {'x': 'freq', 'y': 'y', 'row': 2, 'col': 1,
                               "title": "Phase vs. Freq<br>Time & Baseline avg"},
                'phase_time': {'x': 'time', 'y': 'y', 'row': 2, 'col': 2,
                               "title": "Phase vs. Time<br>Freq & Baseline avg"},
                'phase_uvdist': {'x': 'x', 'y': 'y', 'row': 2, 'col': 3,
                                 "title": "Phase vs. uv-dist<br>Time & Freq avg"},
                'ampresid_uvwave': {'x': 'x', 'y': 'y', 'row': 2, 'col': 4,
                                    "title": "Resid Amp vs. uv-wave<br>Time & Freq avg"},
                'amp_ant1': {'x': 'x', 'y': 'y', 'row': 3, 'col': 1,
                             "title": "Amp vs. Ant 1.<br>Time & Freq avg"},
                'phase_ant1': {'x': 'x', 'y': 'y', 'row': 3, 'col': 2,
                               "title": "Phase vs. Ant 1.<br>Time & Freq avg"}}

    # Make the antenna plots optional because they were added later.
    if not 'amp_ant1' in table_dict.keys():
        exp_keys['amp_ant1'].pop()
    if not 'phase_ant1' in table_dict.keys():
        exp_keys['phase_ant1'].pop()

    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    # It's easier to just do this by-hand. Or switch to an ordereddict
    subplot_titles = [exp_keys['amp_chan']['title'],
                      exp_keys['amp_time']['title'],
                      exp_keys['amp_uvdist']['title'],
                      exp_keys['amp_phase']['title'],
                      exp_keys['phase_chan']['title'],
                      exp_keys['phase_time']['title'],
                      exp_keys['phase_uvdist']['title'],
                      exp_keys['ampresid_uvwave']['title'],
                      exp_keys['amp_ant1']['title'],
                      exp_keys['phase_ant1']['title']]

    fig = make_subplots(rows=3, cols=4, subplot_titles=subplot_titles)

    hovertemplate = 'Scan: %{customdata[0]}<br>SPW: %{customdata[1]}<br>Chan: %{customdata[2]}<br>Freq: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}<br>Time: %{customdata[7]}'

    spw_nums = np.unique(table_dict['amp_chan']['spw'].tolist())

    def make_casa_timestring(x):

        datetime_vals = vla_time_conversion(x)

        return [dtime.strftime("%Y/%m/%d/%H:%M:%S.%f")[:-5]
                for dtime in datetime_vals]

    colors_dict = {"SPW": [],
                   "Scan": [],
                   "Ant1": [],
                   "Ant2": [],
                   "Corr": []}

    for nspw, spw in enumerate(spw_nums):

        for nn, key in enumerate(exp_keys):

            # Convert the time axis values to strings
            # Time is always the x-axis.
            if "time" in key:
                def format_xvals(x):
                    datetime_vals = vla_time_conversion(x)

                    return datetime_vals
            else:
                def format_xvals(x):
                    return x

            tab_data = table_dict[key]

            spw_mask = tab_data['spw'] == spw

            if corrs is None:
                corrs = np.unique(tab_data['corr'][spw_mask].tolist())

            for nc, (corr, marker) in enumerate(zip(corrs, markers)):

                corr_mask = (tab_data['corr'] == corr).tolist()

                custom_data = np.vstack((tab_data['scan'][spw_mask & corr_mask].tolist(),
                                         tab_data['spw'][spw_mask & corr_mask].tolist(),
                                         tab_data['chan'][spw_mask & corr_mask].tolist(),
                                         tab_data['freq'][spw_mask & corr_mask].tolist(),
                                         tab_data['corr'][spw_mask & corr_mask].tolist(),
                                         tab_data['ant1name'][spw_mask & corr_mask].tolist(),
                                         tab_data['ant2name'][spw_mask & corr_mask].tolist(),
                                         make_casa_timestring(tab_data['time'][spw_mask & corr_mask].tolist()))).T

                # We're also going to record colors based on Scan and SPW
                # SPW are unique and the colour palette has 11 colours.
                spw_data = tab_data['spw'][spw_mask & corr_mask].tolist()

                colors_dict['SPW'].append([px.colors.qualitative.Safe[nspw % 11] for _ in range(len(spw_data))])

                # Want to map to unique scan values, not the scan numbers themselves
                # (i.e., 50, 60, 70 -> 0, 1, 2)
                scan_data = tab_data['scan'][spw_mask & corr_mask].tolist()

                scan_map_dict = {}
                for n_uniq, scan in enumerate(np.unique(scan_data)):
                    scan_map_dict[scan] = n_uniq

                colors_dict['Scan'].append([px.colors.qualitative.Safe[scan_map_dict[scan] % 11]
                                            for scan in scan_data])

                # And antennas for colours. Same approach as scans
                ant_data = tab_data['ant1name'][spw_mask & corr_mask].tolist()

                ant1_map_dict = {}
                for n_uniq, ant in enumerate(np.unique(ant_data)):
                    ant1_map_dict[ant] = n_uniq

                colors_dict['Ant1'].append([px.colors.qualitative.Safe[ant1_map_dict[ant] % 11]
                                            for ant in ant_data])

                ant_data = tab_data['ant2name'][spw_mask & corr_mask].tolist()

                ant2_map_dict = {}
                for n_uniq, ant in enumerate(np.unique(ant_data)):
                    ant2_map_dict[ant] = n_uniq

                colors_dict['Ant2'].append([px.colors.qualitative.Safe[ant2_map_dict[ant] % 11]
                                            for ant in ant_data])

                # And corr
                colors_dict['Corr'].append([px.colors.qualitative.Safe[nc % 11]
                                            for _ in range(len(spw_data))])

                fig.append_trace(scatter_plot(x=format_xvals(tab_data[exp_keys[key]['x']][spw_mask & corr_mask]),
                                              y=tab_data[exp_keys[key]['y']][spw_mask & corr_mask],
                                              mode='markers',
                                              marker=dict(symbol=marker,
                                                          size=7,
                                                          color=px.colors.qualitative.Safe[nspw % 11]),
                                              customdata=custom_data,
                                              hovertemplate=hovertemplate,
                                              name=f"SPW {spw}",
                                              legendgroup=str(spw),
                                              showlegend=True if (nn == 0 and nc == 0) else False),
                                 row=exp_keys[key]['row'], col=exp_keys[key]['col'],
                                 )

    # Make custom time ticks in a nicer format.
    # Also scale with zoom to stop tick labels from overlapping in different subplots.
    for key in exp_keys:
        if "time" not in key:
            continue

        fig.update_xaxes(rangeslider_visible=False,
                         tickformatstops=[dict(dtickrange=[None, 1000], value="%H:%M:%S"),
                                          dict(dtickrange=[1000, None], value="%H:%M:%S"),
                                          ],
                         row=exp_keys[key]['row'],
                         col=exp_keys[key]['col'])

    fig.update_xaxes(nticks=8)
    fig.update_yaxes(nticks=8)

    fig['layout']['xaxis']['title'] = 'Frequency (GHz)'
    fig['layout']['xaxis2']['title'] = 'Time (UTC)'
    fig['layout']['xaxis3']['title'] = 'uv-distance (m)'
    fig['layout']['xaxis4']['title'] = 'Phase (deg)'
    fig['layout']['xaxis5']['title'] = 'Frequency (GHz)'
    fig['layout']['xaxis6']['title'] = 'Time (UTC)'
    fig['layout']['xaxis7']['title'] = 'uv-distance (m)'
    fig['layout']['xaxis8']['title'] = 'uv-wave'
    fig['layout']['xaxis9']['title'] = 'Antenna 1'
    fig['layout']['xaxis10']['title'] = 'Antenna 1'

    # Check these: is it actually Jy or Jy/deg, etc?
    fig['layout']['yaxis']['title'] = 'Amplitude (Jy)'
    fig['layout']['yaxis2']['title'] = 'Amplitude (Jy)'
    fig['layout']['yaxis3']['title'] = 'Amplitude (Jy)'
    fig['layout']['yaxis4']['title'] = 'Amplitude (Jy)'
    fig['layout']['yaxis5']['title'] = 'Phase (deg)'
    fig['layout']['yaxis6']['title'] = 'Phase (deg)'
    fig['layout']['yaxis7']['title'] = 'Phase (deg)'
    fig['layout']['yaxis8']['title'] = '(Amplitude - Model) Residual (Jy)'
    fig['layout']['yaxis9']['title'] = 'Amplitude (Jy)'
    fig['layout']['yaxis10']['title'] = 'Phase (deg)'

    meta = meta_dict['amp_time']

    if 'intent' not in meta_dict:
        intent_str = "NONE"
    else:
        intent_str = meta_dict['intent']

    fig.update_layout(
        title=f"Field: {meta['field']}  Intent: {intent_str}<br>MS: {meta['vis']}",
        font=dict(
            family="Courier New, monospace",
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

                                                    dict(label='Ant1',
                                                         method='update',
                                                         args=[{'marker.color': [col for col in colors_dict['Ant1']]}],
                                                         ),

                                                    dict(label='Ant2',
                                                         method='update',
                                                         args=[{'marker.color': [col for col in colors_dict['Ant2']]}],
                                                         ),

                                                    dict(label='Corr',
                                                         method='update',
                                                         args=[{'marker.color': [col for col in colors_dict['Corr']]}],
                                                         ),
                                                     ]))

    fig.update_layout(updatemenus=[updatemenus],
                      margin=dict(t=150))

    if show:
        fig.show()

    return fig
