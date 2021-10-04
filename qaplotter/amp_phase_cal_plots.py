

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np


from .utils.time_conversion import make_casa_timestring, vla_time_conversion


def phase_gain_figures(table_dict, meta_dict,
                        nant_per_figure=8,
                        scatter_plot=go.Scattergl,
                        ):
    '''
    Create an plot for each Antenna. Will create several figures based
    on total # of ants vs. # ants per figure (default is 4).

    Use for:
    1. phasegaincal
    2. phaseshortgaincal
    3. BPinitialgain
    '''

    exp_keys = {'phase': {'x': 'time', 'y': 'y'}}
    xlabel='Time'
    ylabel='Phase'

    keyname = list(exp_keys.keys())[0]

    # There should be 1 field:
    # exp_keys = {'amp': {'x': 'freq', 'y': 'y'}}

    hovertemplate = 'Scan: %{customdata[0]}<br>SPW: %{customdata[1]}<br>Chan: %{customdata[2]}<br>Freq: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}<br>Time: %{customdata[7]}'

    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    nants = len(table_dict[keyname])
    ant_keys = sorted(list(table_dict[keyname].keys()))

    nfigures = nants // nant_per_figure
    if nants % nant_per_figure > 0:
        nfigures += 1
    # if nants % nant_per_figure != 0:
    #     nfigures += 1

    # Count as we add in SPW plots
    ant_nums = list(table_dict[keyname].keys())
    ant_nums.sort()

    print(f"Number of ants: {ant_nums}")
    print(f"Making {nfigures} cal plots")

    markers = ['circle', 'diamond', 'triangle-up', 'triangle-down']

    all_figs = []


    for nn in range(nfigures):

        # Grab the new few titles:
        subplot_titles = []

        this_nant_per_figure = nant_per_figure

        ncols = this_nant_per_figure // 2
        # TODO: Should this be hard-coded? It's easier for now, IMO.
        nrows = 2
        for jj in range(this_nant_per_figure):
            ant_num = this_nant_per_figure * nn + jj
            if ant_num < len(ant_nums):
                # Extract the first ant1name from the data (if it exists):

                try:
                    ant1_vals = table_dict[list(exp_keys.keys())[0]][ant_num]['ant1name']
                except KeyError:
                    subplot_titles.append(f"Ant (Flagged)")
                    continue

                if len(ant1_vals) > 0:
                    subplot_titles.append(f"Ant {ant1_vals[0]}")
                else:
                    subplot_titles.append(f"Ant (Flagged)")
                # subplot_titles.append(f"Ant {ant_keys[this_nant_per_figure * nn + jj]}")
            else:
                this_nant_per_figure = jj

                break

        fig = make_subplots(rows=2, cols=ncols,
                            subplot_titles=subplot_titles,
                            shared_xaxes=False, shared_yaxes=False)

        # Loop through for each antenna
        for ii in range(this_nant_per_figure):

            ant_num = ant_nums[nant_per_figure * nn + ii]

            # Make an amp vs freq and phase vs freq plot for each

            for key in table_dict.keys():

                tab_data = table_dict[key][ant_num]

                corrs = np.unique(tab_data['corr'].tolist())

                for nc, (corr, marker) in enumerate(zip(corrs, markers)):

                    corr_mask = (tab_data['corr'] == corr).tolist()

                    # Colour by SPW
                    spw_data = tab_data['spw'][corr_mask].tolist()

                    spw_map_dict = {}
                    for n_uniq, spw in enumerate(np.unique(spw_data)):
                        spw_map_dict[spw] = n_uniq

                    spw_colors = [px.colors.qualitative.Safe[ij % 11]
                                  for ij, spw in enumerate(spw_data)]

                    # print(ii, ii // ncols, ii // nrows)

                    for kk, spw in enumerate(np.unique(spw_data)):

                        spw_mask = (tab_data['spw'] == spw).tolist()

                        combined_mask = np.logical_and(np.array(corr_mask), np.array(spw_mask))

                        custom_data = np.vstack((tab_data['scan'][combined_mask].tolist(),
                                                tab_data['spw'][combined_mask].tolist(),
                                                tab_data['chan'][combined_mask].tolist(),
                                                tab_data['freq'][combined_mask].tolist(),
                                                tab_data['corr'][combined_mask].tolist(),
                                                tab_data['ant1name'][combined_mask].tolist(),
                                                tab_data['ant2name'][combined_mask].tolist(),
                                                make_casa_timestring(tab_data['time'][combined_mask].tolist()))).T

                        fig.append_trace(scatter_plot(x=vla_time_conversion(tab_data['time'][combined_mask].tolist()),
                                                    y=tab_data[exp_keys[key]['y']][combined_mask],
                                                    mode='lines+markers',
                                                    marker=dict(symbol=marker,
                                                                size=8,
                                                                color=spw_colors[kk]),
                                                    customdata=custom_data,
                                                    hovertemplate=hovertemplate,
                                                    showlegend=False),
                                        row=ii // ncols + 1,
                                        col=ii % ncols + 1,
                                        )

                        fig.update_xaxes(rangeslider_visible=False,
                                        tickformatstops=[dict(dtickrange=[None, 1000], value="%H:%M:%S"),
                                                        dict(dtickrange=[1000, None], value="%H:%M:%S"),
                                                        ],
                                        row=ii // ncols + 1,
                                        col=ii % ncols + 1)

            ant_num += 1

        fig.update_xaxes(nticks=8)
        fig.update_yaxes(nticks=8)

        fig.update_yaxes(range=[-180, 180])


        for i in range(nant_per_figure * 2):

            try:
                if i == 0:
                    fig['layout']['xaxis']['title'] = xlabel
                else:
                    fig['layout'][f'xaxis{i+1}']['title'] = xlabel
            except KeyError:
                pass

        for i in range(nant_per_figure):

            try:
                if i == 0:
                    fig['layout']['yaxis']['title'] = ylabel
                else:
                    fig['layout'][f'yaxis{i+1}']['title'] = ylabel
            except KeyError:
                pass

        meta = meta_dict[keyname][ant_keys[0]]

        fig.update_layout(
            title=f"Cal table: {meta['vis']}<br>Marker symbols show correlation (RR, LL).",
            font=dict(family="Courier New, monospace",
                      size=15,
                      color="#7f7f7f"),
        )

        all_figs.append(fig)

    return all_figs


def amp_gain_time_figures(table_dict, meta_dict,
                          nant_per_figure=8,
                          scatter_plot=go.Scattergl,
                          ):
    '''
    Create a plot for each Antenna. Will create several figures based
    on total # of ants vs. # ants per figure (default is 4).
    '''

    exp_keys = {'amp': {'x': 'time', 'y': 'y'}}
    xlabel='Time'
    ylabel='Amplitude'

    keyname = list(exp_keys.keys())[0]

    # There should be 1 field:
    # exp_keys = {'amp': {'x': 'freq', 'y': 'y'}}

    hovertemplate = 'Scan: %{customdata[0]}<br>SPW: %{customdata[1]}<br>Chan: %{customdata[2]}<br>Freq: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}<br>Time: %{customdata[7]}'

    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    nants = len(table_dict[keyname])
    ant_keys = sorted(list(table_dict[keyname].keys()))

    nfigures = nants // nant_per_figure
    if nants % nant_per_figure > 0:
        nfigures += 1
    # if nants % nant_per_figure != 0:
    #     nfigures += 1

    # Count as we add in SPW plots
    ant_nums = list(table_dict[keyname].keys())
    ant_nums.sort()

    print(f"Number of ants: {ant_nums}")
    print(f"Making {nfigures} cal plots")

    markers = ['circle', 'diamond', 'triangle-up', 'triangle-down']

    # Find the max amp value:
    min_value = 0.
    max_value = 0.
    for ant_num in ant_nums:
        tab_data = table_dict[list(exp_keys.keys())[0]][ant_num]

        if len(tab_data['y']) == 0:
            continue

        this_max_value = np.nanmax(tab_data['y'])
        if max_value < this_max_value:
            max_value = this_max_value

    all_figs = []

    for nn in range(nfigures):

        # Grab the new few titles:
        subplot_titles = []

        this_nant_per_figure = nant_per_figure

        ncols = this_nant_per_figure // 2
        # TODO: Should this be hard-coded? It's easier for now, IMO.
        nrows = 2
        for jj in range(this_nant_per_figure):
            ant_num = this_nant_per_figure * nn + jj
            if ant_num < len(ant_nums):
                # Extract the first ant1name from the data (if it exists):

                try:
                    ant1_vals = table_dict[list(exp_keys.keys())[0]][ant_num]['ant1name']
                except KeyError:
                    subplot_titles.append(f"Ant (Flagged)")
                    continue

                if len(ant1_vals) > 0:
                    subplot_titles.append(f"Ant {ant1_vals[0]}")
                else:
                    subplot_titles.append(f"Ant (Flagged)")
                # subplot_titles.append(f"Ant {ant_keys[this_nant_per_figure * nn + jj]}")
            else:
                this_nant_per_figure = jj

                break

        fig = make_subplots(rows=2, cols=ncols,
                            subplot_titles=subplot_titles,
                            shared_xaxes=False, shared_yaxes=False)

        # Loop through for each antenna
        for ii in range(this_nant_per_figure):

            ant_num = ant_nums[nant_per_figure * nn + ii]

            # Make an amp vs freq and phase vs freq plot for each

            for key in table_dict.keys():

                tab_data = table_dict[key][ant_num]

                corrs = np.unique(tab_data['corr'].tolist())

                for nc, (corr, marker) in enumerate(zip(corrs, markers)):

                    corr_mask = (tab_data['corr'] == corr).tolist()

                    # Colour by Ant 1
                    spw_data = tab_data['spw'][corr_mask].tolist()

                    spw_map_dict = {}
                    for n_uniq, spw in enumerate(np.unique(spw_data)):
                        spw_map_dict[spw] = n_uniq

                    spw_colors = [px.colors.qualitative.Safe[spw_map_dict[spw] % 11]
                                  for spw in spw_data]

                    # print(ii, ii // ncols, ii // nrows)

                    for kk, spw in enumerate(np.unique(spw_data)):

                        spw_mask = (tab_data['spw'] == spw).tolist()

                        combined_mask = np.logical_and(np.array(corr_mask), np.array(spw_mask))

                        custom_data = np.vstack((tab_data['scan'][combined_mask].tolist(),
                                                tab_data['spw'][combined_mask].tolist(),
                                                tab_data['chan'][combined_mask].tolist(),
                                                tab_data['freq'][combined_mask].tolist(),
                                                tab_data['corr'][combined_mask].tolist(),
                                                tab_data['ant1name'][combined_mask].tolist(),
                                                tab_data['ant2name'][combined_mask].tolist(),
                                                make_casa_timestring(tab_data['time'][combined_mask].tolist()))).T

                        fig.append_trace(scatter_plot(x=vla_time_conversion(tab_data['time'][combined_mask].tolist()),
                                                    y=tab_data[exp_keys[key]['y']][combined_mask],
                                                    mode='lines+markers',
                                                    marker=dict(symbol=marker,
                                                                size=8,
                                                                color=spw_colors[kk]),
                                                    customdata=custom_data,
                                                    hovertemplate=hovertemplate,
                                                    showlegend=False),
                                        row=ii // ncols + 1,
                                        col=ii % ncols + 1,
                                        )

                        fig.update_xaxes(rangeslider_visible=False,
                                        tickformatstops=[dict(dtickrange=[None, 1000], value="%H:%M:%S"),
                                                        dict(dtickrange=[1000, None], value="%H:%M:%S"),
                                                        ],
                                        row=ii // ncols + 1,
                                        col=ii % ncols + 1)

            ant_num += 1

        fig.update_xaxes(nticks=8)
        fig.update_yaxes(nticks=8)

        fig.update_yaxes(range=[0, 1.1 * max_value])

        for i in range(nant_per_figure * 2):

            try:
                if i == 0:
                    fig['layout']['xaxis']['title'] = xlabel
                else:
                    fig['layout'][f'xaxis{i+1}']['title'] = xlabel
            except KeyError:
                pass

        for i in range(nant_per_figure):

            try:
                if i == 0:
                    fig['layout']['yaxis']['title'] = ylabel
                else:
                    fig['layout'][f'yaxis{i+1}']['title'] = ylabel
            except KeyError:
                pass

        meta = meta_dict[keyname][ant_keys[0]]

        fig.update_layout(
            title=f"Cal table: {meta['vis']}<br>Marker symbols show correlation (RR, LL).",
            font=dict(family="Courier New, monospace",
                      size=15,
                      color="#7f7f7f"),
        )

        all_figs.append(fig)

    return all_figs


def delay_freq_figures(table_dict, meta_dict,
                       nant_per_figure=8,
                       scatter_plot=go.Scattergl,
                       ):
    '''
    Create a plot for each Antenna. Will create several figures based
    on total # of ants vs. # ants per figure (default is 4).
    '''

    exp_keys = {'delay': {'x': 'freq', 'y': 'y'}}
    xlabel='Frequency (GHz)'
    ylabel='Delay (ns)'

    keyname = list(exp_keys.keys())[0]

    # There should be 1 field:
    # exp_keys = {'amp': {'x': 'freq', 'y': 'y'}}

    hovertemplate = 'Scan: %{customdata[0]}<br>SPW: %{customdata[1]}<br>Chan: %{customdata[2]}<br>Freq: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}<br>Time: %{customdata[7]}'

    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    nants = len(table_dict[keyname])
    ant_keys = sorted(list(table_dict[keyname].keys()))

    nfigures = nants // nant_per_figure
    if nants % nant_per_figure > 0:
        nfigures += 1
    # if nants % nant_per_figure != 0:
    #     nfigures += 1

    # Count as we add in SPW plots
    ant_nums = list(table_dict[keyname].keys())
    ant_nums.sort()

    print(f"Number of ants: {ant_nums}")
    print(f"Making {nfigures} cal plots")

    markers = ['circle', 'diamond', 'triangle-up', 'triangle-down']

    # Find the max amp value:
    min_value = 0.
    max_value = 0.
    for ant_num in ant_nums:
        tab_data = table_dict[list(exp_keys.keys())[0]][ant_num]

        if len(tab_data['y']) == 0:
            continue

        this_max_value = np.nanmax(tab_data['y'])
        if max_value < this_max_value:
            max_value = this_max_value

        this_min_value = np.nanmin(tab_data['y'])
        if min_value > this_min_value:
            min_value = this_min_value

    all_figs = []

    for nn in range(nfigures):

        # Grab the new few titles:
        subplot_titles = []

        this_nant_per_figure = nant_per_figure

        ncols = this_nant_per_figure // 2
        # TODO: Should this be hard-coded? It's easier for now, IMO.
        nrows = 2
        for jj in range(this_nant_per_figure):
            ant_num = this_nant_per_figure * nn + jj
            if ant_num < len(ant_nums):
                # Extract the first ant1name from the data (if it exists):

                try:
                    ant1_vals = table_dict[list(exp_keys.keys())[0]][ant_num]['ant1name']
                except KeyError:
                    subplot_titles.append(f"Ant (Flagged)")
                    continue

                if len(ant1_vals) > 0:
                    subplot_titles.append(f"Ant {ant1_vals[0]}")
                else:
                    subplot_titles.append(f"Ant (Flagged)")
                # subplot_titles.append(f"Ant {ant_keys[this_nant_per_figure * nn + jj]}")
            else:
                this_nant_per_figure = jj

                break

        fig = make_subplots(rows=2, cols=ncols,
                            subplot_titles=subplot_titles,
                            shared_xaxes=False, shared_yaxes=False)

        # Loop through for each antenna
        for ii in range(this_nant_per_figure):

            ant_num = ant_nums[nant_per_figure * nn + ii]

            # Make an amp vs freq and phase vs freq plot for each

            for key in table_dict.keys():

                tab_data = table_dict[key][ant_num]

                corrs = np.unique(tab_data['corr'].tolist())

                for nc, (corr, marker) in enumerate(zip(corrs, markers)):

                    corr_mask = (tab_data['corr'] == corr).tolist()

                    # Colour by Ant 1
                    spw_data = tab_data['spw'][corr_mask].tolist()

                    spw_map_dict = {}
                    for n_uniq, spw in enumerate(np.unique(spw_data)):
                        spw_map_dict[spw] = n_uniq

                    spw_colors = [px.colors.qualitative.Safe[spw_map_dict[spw] % 11]
                                  for spw in spw_data]

                    # print(ii, ii // ncols, ii // nrows)

                    for kk, spw in enumerate(np.unique(spw_data)):

                        spw_mask = (tab_data['spw'] == spw).tolist()

                        combined_mask = np.logical_and(np.array(corr_mask), np.array(spw_mask))

                        custom_data = np.vstack((tab_data['scan'][combined_mask].tolist(),
                                                tab_data['spw'][combined_mask].tolist(),
                                                tab_data['chan'][combined_mask].tolist(),
                                                tab_data['freq'][combined_mask].tolist(),
                                                tab_data['corr'][combined_mask].tolist(),
                                                tab_data['ant1name'][combined_mask].tolist(),
                                                tab_data['ant2name'][combined_mask].tolist(),
                                                tab_data['time'][combined_mask].tolist())).T

                        fig.append_trace(scatter_plot(x=tab_data['freq'][combined_mask],
                                                    y=tab_data[exp_keys[key]['y']][combined_mask],
                                                    mode='lines+markers',
                                                    marker=dict(symbol=marker,
                                                                size=8,
                                                                color=spw_colors[kk]),
                                                    customdata=custom_data,
                                                    hovertemplate=hovertemplate,
                                                    showlegend=False),
                                        row=ii // ncols + 1,
                                        col=ii % ncols + 1,
                                        )

            ant_num += 1

        fig.update_xaxes(nticks=8)
        fig.update_yaxes(nticks=8)

        fig.update_yaxes(range=[0.75 * min_value, 1.25 * max_value])

        for i in range(nant_per_figure * 2):

            try:
                if i == 0:
                    fig['layout']['xaxis']['title'] = xlabel
                else:
                    fig['layout'][f'xaxis{i+1}']['title'] = xlabel
            except KeyError:
                pass

        for i in range(nant_per_figure):

            try:
                if i == 0:
                    fig['layout']['yaxis']['title'] = ylabel
                else:
                    fig['layout'][f'yaxis{i+1}']['title'] = ylabel
            except KeyError:
                pass

        meta = meta_dict[keyname][ant_keys[0]]

        fig.update_layout(
            title=f"Cal table: {meta['vis']}<br>Marker symbols show correlation (RR, LL).",
            font=dict(family="Courier New, monospace",
                      size=15,
                      color="#7f7f7f"),
        )

        all_figs.append(fig)

    return all_figs


def amp_gain_freq_figures(table_dict, meta_dict,
                          nant_per_figure=8,
                          scatter_plot=go.Scattergl,
                          ):
    '''
    Create a plot for each Antenna. Will create several figures based
    on total # of ants vs. # ants per figure (default is 4).
    '''

    exp_keys = {'amp': {'x': 'freq', 'y': 'y'}}
    xlabel='Frequency (GHz)'
    ylabel='Amplitude'

    keyname = list(exp_keys.keys())[0]

    # There should be 1 field:
    # exp_keys = {'amp': {'x': 'freq', 'y': 'y'}}

    hovertemplate = 'Scan: %{customdata[0]}<br>SPW: %{customdata[1]}<br>Chan: %{customdata[2]}<br>Freq: %{customdata[3]}<br>Corr: %{customdata[4]}<br>Ant1: %{customdata[5]}<br>Ant2: %{customdata[6]}<br>Time: %{customdata[7]}'

    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    nants = len(table_dict[keyname])
    ant_keys = sorted(list(table_dict[keyname].keys()))

    nfigures = nants // nant_per_figure
    if nants % nant_per_figure > 0:
        nfigures += 1
    # if nants % nant_per_figure != 0:
    #     nfigures += 1

    # Count as we add in SPW plots
    ant_nums = list(table_dict[keyname].keys())
    ant_nums.sort()

    print(f"Number of ants: {ant_nums}")
    print(f"Making {nfigures} cal plots")

    markers = ['circle', 'diamond', 'triangle-up', 'triangle-down']

    # Find the max amp value:
    min_value = 0.
    max_value = 0.
    for ant_num in ant_nums:
        tab_data = table_dict[list(exp_keys.keys())[0]][ant_num]

        if len(tab_data['y']) == 0:
            continue

        this_max_value = np.nanmax(tab_data['y'])
        if max_value < this_max_value:
            max_value = this_max_value

    all_figs = []

    for nn in range(nfigures):

        # Grab the new few titles:
        subplot_titles = []

        this_nant_per_figure = nant_per_figure

        ncols = this_nant_per_figure // 2
        # TODO: Should this be hard-coded? It's easier for now, IMO.
        nrows = 2
        for jj in range(this_nant_per_figure):
            ant_num = this_nant_per_figure * nn + jj
            if ant_num < len(ant_nums):
                # Extract the first ant1name from the data (if it exists):

                try:
                    ant1_vals = table_dict[list(exp_keys.keys())[0]][ant_num]['ant1name']
                except KeyError:
                    subplot_titles.append(f"Ant (Flagged)")
                    continue

                if len(ant1_vals) > 0:
                    subplot_titles.append(f"Ant {ant1_vals[0]}")
                else:
                    subplot_titles.append(f"Ant (Flagged)")
                # subplot_titles.append(f"Ant {ant_keys[this_nant_per_figure * nn + jj]}")
            else:
                this_nant_per_figure = jj

                break

        fig = make_subplots(rows=2, cols=ncols,
                            subplot_titles=subplot_titles,
                            shared_xaxes=False, shared_yaxes=False)

        # Loop through for each antenna
        for ii in range(this_nant_per_figure):

            ant_num = ant_nums[nant_per_figure * nn + ii]

            # Make an amp vs freq and phase vs freq plot for each

            for key in table_dict.keys():

                tab_data = table_dict[key][ant_num]

                corrs = np.unique(tab_data['corr'].tolist())

                for nc, (corr, marker) in enumerate(zip(corrs, markers)):

                    corr_mask = (tab_data['corr'] == corr).tolist()

                    # Colour by Ant 1
                    spw_data = tab_data['spw'][corr_mask].tolist()

                    spw_map_dict = {}
                    for n_uniq, spw in enumerate(np.unique(spw_data)):
                        spw_map_dict[spw] = n_uniq

                    spw_colors = [px.colors.qualitative.Safe[spw_map_dict[spw] % 11]
                                  for spw in spw_data]

                    # print(ii, ii // ncols, ii // nrows)

                    for kk, spw in enumerate(np.unique(spw_data)):

                        spw_mask = (tab_data['spw'] == spw).tolist()

                        combined_mask = np.logical_and(np.array(corr_mask), np.array(spw_mask))

                        custom_data = np.vstack((tab_data['scan'][combined_mask].tolist(),
                                                tab_data['spw'][combined_mask].tolist(),
                                                tab_data['chan'][combined_mask].tolist(),
                                                tab_data['freq'][combined_mask].tolist(),
                                                tab_data['corr'][combined_mask].tolist(),
                                                tab_data['ant1name'][combined_mask].tolist(),
                                                tab_data['ant2name'][combined_mask].tolist(),
                                                tab_data['time'][combined_mask].tolist())).T

                        fig.append_trace(scatter_plot(x=tab_data['freq'][combined_mask],
                                                    y=tab_data[exp_keys[key]['y']][combined_mask],
                                                    mode='lines+markers',
                                                    marker=dict(symbol=marker,
                                                                size=8,
                                                                color=spw_colors[kk]),
                                                    customdata=custom_data,
                                                    hovertemplate=hovertemplate,
                                                    showlegend=False),
                                        row=ii // ncols + 1,
                                        col=ii % ncols + 1,
                                        )

            ant_num += 1

        fig.update_xaxes(nticks=8)
        fig.update_yaxes(nticks=8)

        fig.update_yaxes(range=[min_value, 1.1 * max_value])

        for i in range(nant_per_figure * 2):

            try:
                if i == 0:
                    fig['layout']['xaxis']['title'] = xlabel
                else:
                    fig['layout'][f'xaxis{i+1}']['title'] = xlabel
            except KeyError:
                pass

        for i in range(nant_per_figure):

            try:
                if i == 0:
                    fig['layout']['yaxis']['title'] = ylabel
                else:
                    fig['layout'][f'yaxis{i+1}']['title'] = ylabel
            except KeyError:
                pass

        meta = meta_dict[keyname][ant_keys[0]]

        fig.update_layout(
            title=f"Cal table: {meta['vis']}<br>Marker symbols show correlation (RR, LL).",
            font=dict(family="Courier New, monospace",
                      size=15,
                      color="#7f7f7f"),
        )

        all_figs.append(fig)

    return all_figs
