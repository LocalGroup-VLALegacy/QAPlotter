
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np


def bp_amp_phase_figures(table_dict, meta_dict,
                         nspw_per_figure=4, scatter_plot=go.Scattergl):
    '''
    Create an amp and phase plot for each SPW. Will create several figures based
    on total # of SPW vs. # SPW per figure (default is 4).
    '''

    # There should be 2 fields:
    exp_keys = {'amp': {'x': 'freq', 'y': 'y'},
                'phase': {'x': 'freq', 'y': 'y'}}

    hovertemplate = 'Scan: %{customdata[0]}<br>SPW: %{customdata[1]}<br>Chan: %{customdata[2]}<br>Freq: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}'

    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    nspws = len(table_dict['amp'])
    spw_keys = sorted(list(table_dict['amp'].keys()))

    nfigures = nspws // nspw_per_figure
    if nspws % nspw_per_figure > 0:
        nfigures += 1
    # if nspws % nspw_per_figure != 0:
    #     nfigures += 1

    # Count as we add in SPW plots
    spw_nums = list(table_dict['amp'].keys())
    spw_nums.sort()

    print(f"Number of spw nums: {spw_nums}")
    print(f"Making {nfigures} bandpass plots")

    markers = ['circle', 'diamond', 'triangle-up', 'triangle-down']

    all_figs = []


    for nn in range(nfigures):

        # Grab the new few titles:
        subplot_titles = []

        ncols = nspw_per_figure
        for jj in range(4):
            if nspw_per_figure * nn + jj < len(spw_nums):
                subplot_titles.append(f"SPW {spw_keys[nspw_per_figure * nn + jj]}")
            else:
                ncols = jj
                break

        fig = make_subplots(rows=2, cols=ncols,
                            subplot_titles=subplot_titles)

        # Loop through for each SPW
        for ii in range(ncols):

            spw_num = spw_nums[nspw_per_figure * nn + ii]

            # Make an amp vs freq and phase vs freq plot for each

            for key in table_dict.keys():

                tab_data = table_dict[key][spw_num]

                corrs = np.unique(tab_data['corr'].tolist())

                for nc, (corr, marker) in enumerate(zip(corrs, markers)):

                    corr_mask = (tab_data['corr'] == corr).tolist()

                    custom_data = np.vstack((tab_data['scan'][corr_mask].tolist(),
                                             tab_data['spw'][corr_mask].tolist(),
                                             tab_data['chan'][corr_mask].tolist(),
                                             tab_data['freq'][corr_mask].tolist(),
                                             tab_data['corr'][corr_mask].tolist(),
                                             tab_data['ant1name'][corr_mask].tolist(),
                                             tab_data['ant2name'][corr_mask].tolist())).T

                    # Colour by Ant 1
                    ant_data = tab_data['ant1name'][corr_mask].tolist()

                    ant1_map_dict = {}
                    for n_uniq, ant in enumerate(np.unique(ant_data)):
                        ant1_map_dict[ant] = n_uniq

                    ant_colors = [px.colors.qualitative.Safe[ant1_map_dict[ant] % 11]
                                  for ant in ant_data]

                    fig.append_trace(scatter_plot(x=tab_data[exp_keys[key]['x']][corr_mask],
                                                  y=tab_data[exp_keys[key]['y']][corr_mask],
                                                  mode='markers',
                                                  marker=dict(symbol=marker,
                                                              size=3,
                                                              color=ant_colors),
                                                  customdata=custom_data,
                                                  hovertemplate=hovertemplate,
                                                  # title=f"SPW {spw_keys[spw_num]}",
                                                  # name=f"SPW {spw}",
                                                  # legendgroup=str(spw),
                                                  # showlegend=True if (nc == 0) else False),
                                                  showlegend=False),
                                     row=1 if key == 'amp' else 2, col=ii + 1,
                                     )

            spw_num += 1

        fig.update_xaxes(nticks=8)
        fig.update_yaxes(nticks=8)

        for i in range(nspw_per_figure * 2):

            try:
                if i == 0:
                    fig['layout']['xaxis']['title'] = 'Frequency (GHz)'
                else:
                    fig['layout'][f'xaxis{i+1}']['title'] = 'Frequency (GHz)'
            except KeyError:
                pass

        for i in range(nspw_per_figure):

            try:
                if i == 0:
                    fig['layout']['yaxis']['title'] = 'Amplitude'
                else:
                    fig['layout'][f'yaxis{i+1}']['title'] = 'Amplitude'
            except KeyError:
                pass

        for i in range(nspw_per_figure):

            try:
                fig['layout'][f'yaxis{i+1+nspw_per_figure}']['title'] = 'Phase'
            except KeyError:
                pass

        meta = meta_dict['amp'][spw_keys[0]]

        fig.update_layout(
            title=f"BP table: {meta['vis']}<br>Marker symbols show correlation (RR, LL).",
            font=dict(family="Courier New, monospace",
                      size=15,
                      color="#7f7f7f")
        )

        all_figs.append(fig)

    return all_figs
