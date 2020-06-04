
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np


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


def target_scan_figure(table_dict, meta_dict):
    '''
    Make a 3-panel figure for target scans.
    '''

    # There should be 3 fields:
    exp_keys = ['amp_chan', 'amp_time', 'amp_uvdist']

    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    # fig = make_subplots(rows=3, cols=1)
    fig = make_subplots(rows=1, cols=3)


    hovertemplate = 'Scan: %{customdata[0]}<br>SPW: %{customdata[1]}<br>Chan: %{customdata[2]}<br>Freq: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}<br>Time: %{customdata[7]}'

    # Amp vs. chan
    ampchan_tab = table_dict['amp_chan']

    custom_data = np.vstack((ampchan_tab['scan'].tolist(),
                             ampchan_tab['spw'].tolist(),
                             ampchan_tab['chan'].tolist(),
                             ampchan_tab['freq'].tolist(),
                             ampchan_tab['corr'].tolist(),
                             ampchan_tab['ant1name'].tolist(),
                             ampchan_tab['ant2name'].tolist(),
                             ampchan_tab['time'].tolist())).T

    fig.append_trace(go.Scattergl(x=ampchan_tab['freq'],
                                  y=ampchan_tab['y'],
                                  mode='markers',
                                  marker=dict(size=16,
                                              cmax=ampchan_tab['spw'].max(),
                                              cmin=ampchan_tab['spw'].min(),
                                              color=ampchan_tab['spw'],
                                              colorscale=px.colors.qualitative.Safe),
                                  customdata=custom_data,
                                  hovertemplate=hovertemplate),
                     row=1, col=1)

    # Amp vs. time
    amptime_tab = table_dict['amp_time']

    custom_data = np.vstack((amptime_tab['scan'].tolist(),
                             amptime_tab['spw'].tolist(),
                             amptime_tab['chan'].tolist(),
                             amptime_tab['freq'].tolist(),
                             amptime_tab['corr'].tolist(),
                             amptime_tab['ant1name'].tolist(),
                             amptime_tab['ant2name'].tolist(),
                             amptime_tab['time'].tolist())).T

    fig.append_trace(go.Scattergl(x=amptime_tab['time'],
                                  y=amptime_tab['y'],
                                  mode='markers',
                                  marker=dict(size=16,
                                              cmax=amptime_tab['spw'].max(),
                                              cmin=amptime_tab['spw'].min(),
                                              color=amptime_tab['spw'],
                                              colorscale=px.colors.qualitative.Safe),
                                  customdata=custom_data,
                                  hovertemplate=hovertemplate),
                     # row=2, col=1)
                     row=1, col=2)

    # Amp vs. uvdist
    ampuvdist_tab = table_dict['amp_uvdist']

    custom_data = np.vstack((ampuvdist_tab['scan'].tolist(),
                             ampuvdist_tab['spw'].tolist(),
                             ampuvdist_tab['chan'].tolist(),
                             ampuvdist_tab['freq'].tolist(),
                             ampuvdist_tab['corr'].tolist(),
                             ampuvdist_tab['ant1name'].tolist(),
                             ampuvdist_tab['ant2name'].tolist(),
                             ampuvdist_tab['time'].tolist())).T

    fig.append_trace(go.Scattergl(x=ampuvdist_tab['x'],
                                  y=ampuvdist_tab['y'],
                                  mode='markers',
                                  marker=dict(size=16,
                                              cmax=ampuvdist_tab['spw'].max(),
                                              cmin=ampuvdist_tab['spw'].min(),
                                              color=ampuvdist_tab['spw'],
                                              colorscale=px.colors.qualitative.Safe),
                                  customdata=custom_data,
                                  hovertemplate=hovertemplate),
                     # row=3, col=1)
                     row=1, col=3)

    fig['layout']['xaxis']['title'] = 'Frequency (GHz)'
    fig['layout']['xaxis2']['title'] = 'Time-MJD (s)'
    fig['layout']['xaxis3']['title'] = 'uv-distance (m)'

    fig['layout']['yaxis']['title'] = 'Amplitude'
    fig['layout']['yaxis2']['title'] = 'Amplitude'
    fig['layout']['yaxis3']['title'] = 'Amplitude'

    meta = meta_dict['amp_time']

    fig.update_layout(
        title=f"Field: {meta['field']}<br>MS: {meta['vis']}",
        font=dict(
            family="Courier New, monospace",
            size=15,
            color="#7f7f7f")
    )

    fig.show()

    return fig
