
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

from .utils import vla_time_conversion


def basic_scatter(tab, xvar='x', yvar='y', hover='ants',
                  colorvar='ant1', meta=None):

    if hover == 'ants':
        # Note that the slicing here is OPPOSITE the numpy convention.
        # Hence the transpose on custom_data.
        hovertemplate = 'Ant1: %{customdata[0]} <br>Ant2 %{customdata[1]}'

        custom_data = np.vstack((tab['ant1'].tolist(),
                                 tab['ant2'].tolist())).T
    else:
        raise NotImplementedError("")

    fig = go.Figure(data=go.Scattergl(x=tab[xvar],
                                      y=tab[yvar],
                                      mode='markers',
                                      marker=dict(size=16,
                                                  cmax=tab[colorvar].max(),
                                                  cmin=tab[colorvar].min(),
                                                  color=tab[colorvar].tolist(),
                                                  colorscale=px.colors.qualitative.Safe),
                                      customdata=custom_data,
                                      hovertemplate=hovertemplate))
    if meta is not None:
        fig.update_layout(
            title=f"Field: {meta['field']}<br>SPW: {meta['spw']}<br>Scan: {meta['scan']}<br>MS: {meta['vis']}",
            # NEED TO PASS x, y names!!
            xaxis_title="uv-distance (m)",
            yaxis_title="Amplitude",
            font=dict(
                family="Courier New, monospace",
                size=15,
                color="#7f7f7f")
        )

    fig.show()


def target_scan_figure(table_dict, meta_dict, show=False,
                       time_format='iso'):
    '''
    Make a 3-panel figure for target scans.
    '''

    # There should be 3 fields:
    exp_keys = {'amp_chan': {'x': 'freq', 'y': 'y', 'row': 1, 'col': 1},
                'amp_time': {'x': 'time', 'y': 'y', 'row': 1, 'col': 2},
                'amp_uvdist': {'x': 'x', 'y': 'y', 'row': 1, 'col': 3}}

    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    fig = make_subplots(rows=1, cols=3)


    hovertemplate = 'Scan: %{customdata[0]}<br>SPW: %{customdata[1]}<br>Chan: %{customdata[2]}<br>Freq: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}<br>Time: %{customdata[7]}'

    spw_nums = np.unique(table_dict['amp_chan']['spw'].tolist())

    markers = ['circle', 'diamond', 'triangle-up', 'triangle-down']

    for nspw, spw in enumerate(spw_nums):

        for nn, key in enumerate(exp_keys):

            # Convert the time axis values to strings
            # Time is always the x-axis.
            if "time" in key:
                def format_xvals(x):
                    return vla_time_conversion(x)
            else:
                def format_xvals(x):
                    return x

            tab_data = table_dict[key]

            spw_mask = tab_data['spw'] == spw

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
                                         vla_time_conversion(tab_data['time'][spw_mask & corr_mask].tolist()))).T

                fig.append_trace(go.Scattergl(x=format_xvals(tab_data[exp_keys[key]['x']][spw_mask & corr_mask]),
                                              y=tab_data[exp_keys[key]['y']][spw_mask & corr_mask],
                                              mode='markers',
                                              marker=dict(symbol=marker,
                                                          size=14,
                                                          color=px.colors.qualitative.Safe[nspw % 11]),
                                              customdata=custom_data,
                                              hovertemplate=hovertemplate,
                                              name=f"SPW {spw}",
                                              legendgroup=str(spw),
                                              showlegend=True if (nn == 0 and nc == 0) else False),
                                 row=exp_keys[key]['row'], col=exp_keys[key]['col'],
                                 )

    fig['layout']['xaxis']['title'] = 'Frequency (GHz)'
    fig['layout']['xaxis2']['title'] = 'Time-MJD (s)'
    fig['layout']['xaxis3']['title'] = 'uv-distance (m)'

    fig['layout']['yaxis']['title'] = 'Amplitude'
    fig['layout']['yaxis2']['title'] = 'Amplitude'
    fig['layout']['yaxis3']['title'] = 'Amplitude'

    meta = meta_dict['amp_time']

    fig.update_layout(
        title=f"Field: {meta['field']}<br>MS: {meta['vis']}",
        font=dict(family="Courier New, monospace",
                  size=15,
                  color="#7f7f7f")
    )

    if show:
        fig.show()

    return fig


def calibrator_scan_figure(table_dict, meta_dict, show=False):
    '''
    Make a 7-panel figure for target scans.
    '''

    # There should be 7 fields:
    exp_keys = {'amp_chan': {'x': 'freq', 'y': 'y', 'row': 1, 'col': 1},
                'amp_time': {'x': 'time', 'y': 'y', 'row': 1, 'col': 2},
                'amp_uvdist': {'x': 'x', 'y': 'y', 'row': 1, 'col': 3},
                'amp_phase': {'x': 'y', 'y': 'x', 'row': 1, 'col': 4},
                'phase_chan': {'x': 'freq', 'y': 'y', 'row': 2, 'col': 1},
                'phase_time': {'x': 'time', 'y': 'y', 'row': 2, 'col': 2},
                'phase_uvdist': {'x': 'x', 'y': 'y', 'row': 2, 'col': 3}}

    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    fig = make_subplots(rows=2, cols=4)


    hovertemplate = 'Scan: %{customdata[0]}<br>SPW: %{customdata[1]}<br>Chan: %{customdata[2]}<br>Freq: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}<br>Time: %{customdata[7]}'

    spw_nums = np.unique(table_dict['amp_chan']['spw'].tolist())

    markers = ['circle', 'diamond', 'triangle-up', 'triangle-down']

    for nspw, spw in enumerate(spw_nums):

        for nn, key in enumerate(exp_keys):

            # Convert the time axis values to strings
            # Time is always the x-axis.
            if "time" in key:
                def format_xvals(x):
                    return vla_time_conversion(x)
            else:
                def format_xvals(x):
                    return x

            tab_data = table_dict[key]

            spw_mask = tab_data['spw'] == spw

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
                                         vla_time_conversion(tab_data['time'][spw_mask & corr_mask].tolist()))).T

                fig.append_trace(go.Scattergl(x=format_xvals(tab_data[exp_keys[key]['x']][spw_mask & corr_mask]),
                                              y=tab_data[exp_keys[key]['y']][spw_mask & corr_mask],
                                              mode='markers',
                                              marker=dict(symbol=marker,
                                                          size=14,
                                                          color=px.colors.qualitative.Safe[nspw % 11]),
                                              customdata=custom_data,
                                              hovertemplate=hovertemplate,
                                              name=f"SPW {spw}",
                                              legendgroup=str(spw),
                                              showlegend=True if (nn == 0 and nc == 0) else False),
                                 row=exp_keys[key]['row'], col=exp_keys[key]['col'],
                                 )

    fig['layout']['xaxis']['title'] = 'Frequency (GHz)'
    fig['layout']['xaxis2']['title'] = 'Time-MJD (s)'
    fig['layout']['xaxis3']['title'] = 'uv-distance (m)'
    fig['layout']['xaxis4']['title'] = 'Phase'
    fig['layout']['xaxis5']['title'] = 'Frequency (GHz)'
    fig['layout']['xaxis6']['title'] = 'Time-MJD (s)'
    fig['layout']['xaxis7']['title'] = 'uv-distance (m)'

    fig['layout']['yaxis']['title'] = 'Amplitude'
    fig['layout']['yaxis2']['title'] = 'Amplitude'
    fig['layout']['yaxis3']['title'] = 'Amplitude'
    fig['layout']['yaxis4']['title'] = 'Amplitude'
    fig['layout']['yaxis5']['title'] = 'Phase'
    fig['layout']['yaxis6']['title'] = 'Phase'
    fig['layout']['yaxis7']['title'] = 'Phase'

    meta = meta_dict['amp_time']

    fig.update_layout(
        title=f"Field: {meta['field']}<br>MS: {meta['vis']}",
        font=dict(
            family="Courier New, monospace",
            size=15,
            color="#7f7f7f")
    )

    if show:
        fig.show()

    return fig
