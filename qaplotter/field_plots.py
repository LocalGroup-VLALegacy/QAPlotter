
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

from .utils import telescope_time_conversion, velocity_rows_for_field

_C_KMS = 299792458.0 / 1000.

# Define a common set of markers to plot for different correlations
# e.g. RR, LL, RL, LR
markers = ['circle', 'cross', 'triangle-up', 'triangle-down']

# Per tab_type plot config: which table columns are the plot's x/y
# values, and which columns to show in the hover text. This is tied to
# the column names written by ReductionPipeline's casatools-based
# `make_qa_tables` (spw/scan/corr always present; chan/freq only for the
# *_chan tables; time only for *_time and amp_phase; ant1/ant2/ant1name/
# ant2name only for the baseline-resolved tables) -- unlike the old
# plotms native export, a column is only present where it's meaningful,
# so there's no generic "x"/"y" pair or universal hover set here.
PLOT_CONFIG = {
    'amp_chan': {'x': 'freq', 'y': 'amp',
                "title": "Amp vs. Freq<br>Time & Baseline avg",
                "hover": ['scan', 'spw', 'corr', 'chan', 'freq']},
    'amp_time': {'x': 'time', 'y': 'amp',
                "title": "Amp vs. Time<br>Freq & Baseline avg",
                "hover": ['scan', 'spw', 'corr', 'time']},
    'amp_uvdist': {'x': 'uvdist', 'y': 'amp',
                  "title": "Amp vs. uv-dist<br>Time & Freq avg",
                  "hover": ['scan', 'spw', 'corr', 'ant1name', 'ant2name', 'uvdist']},
    'amp_phase': {'x': 'phase', 'y': 'amp',
                 "title": "Amp vs. Phase<br>Time & Freq avg",
                 "hover": ['scan', 'spw', 'corr', 'ant1name', 'ant2name', 'time']},
    'phase_chan': {'x': 'freq', 'y': 'phase',
                  "title": "Phase vs. Freq<br>Time & Baseline avg",
                  "hover": ['scan', 'spw', 'corr', 'chan', 'freq']},
    'phase_time': {'x': 'time', 'y': 'phase',
                  "title": "Phase vs. Time<br>Freq & Baseline avg",
                  "hover": ['scan', 'spw', 'corr', 'time']},
    'phase_uvdist': {'x': 'uvdist', 'y': 'phase',
                     "title": "Phase vs. uv-dist<br>Time & Freq avg",
                     "hover": ['scan', 'spw', 'corr', 'ant1name', 'ant2name', 'uvdist']},
    'ampresid_uvwave': {'x': 'uvwave', 'y': 'resid',
                        "title": "Resid Amp vs. uv-wave<br>Time & Freq avg",
                        "hover": ['scan', 'spw', 'corr', 'ant1name', 'ant2name', 'uvdist', 'uvwave']},
    'amp_ant1': {'x': 'ant1', 'y': 'amp',
                "title": "Amp vs. Ant 1.<br>Time & Freq avg",
                "hover": ['scan', 'spw', 'corr', 'ant1name', 'ant2name']},
    'phase_ant1': {'x': 'ant1', 'y': 'phase',
                  "title": "Phase vs. Ant 1.<br>Time & Freq avg",
                  "hover": ['scan', 'spw', 'corr', 'ant1name', 'ant2name']},
}

HOVER_LABELS = {'scan': 'Scan', 'spw': 'SPW', 'corr': 'Corr', 'chan': 'Chan',
                'freq': 'Freq', 'time': 'Time', 'ant1name': 'Ant1',
                'ant2name': 'Ant2', 'uvdist': 'UVdist', 'uvwave': 'UVwave'}


def _casa_timestrings(x, telescope):
    datetime_vals = telescope_time_conversion(x, telescope=telescope)
    return [dtime.strftime("%Y/%m/%d/%H:%M:%S.%f")[:-5] for dtime in datetime_vals]


def _build_hover(tab_data, mask, fields, telescope):
    '''
    Build the customdata array and matching hovertemplate string for
    whichever of `fields` are actually present in `tab_data` (some, like
    'ant1name', only exist for the baseline-resolved tables).
    '''

    cols = []
    template_parts = []

    for field in fields:
        if field not in tab_data.colnames:
            continue

        if field == 'time':
            vals = _casa_timestrings(tab_data['time'][mask].tolist(), telescope)
        else:
            vals = tab_data[field][mask].tolist()

        template_parts.append(f"{HOVER_LABELS[field]}: %{{customdata[{len(cols)}]}}")
        cols.append(vals)

    customdata = np.vstack(cols).T if cols else None
    hovertemplate = '<br>'.join(template_parts)

    return customdata, hovertemplate


def _add_scan_traces(fig, exp_keys, table_dict, spw_nums, corrs, spw_labels,
                     row_col, telescope, first_trace_flag):
    '''
    Shared trace-adding loop used by both `target_scan_figure` and
    `calibrator_scan_figure`. Returns the colors_dict used to populate
    the SPW/Scan/Corr/Ant1/Ant2 colour-toggle buttons.
    '''

    colors_dict = {"SPW": [], "Scan": [], "Corr": [], "Ant1": [], "Ant2": []}

    # Neutral placeholder for panels with no baseline info at all (shapes
    # A/B: amp_time/amp_chan/phase_time/phase_chan average over baseline),
    # matching how the old plotms native export's placeholder ant1name='*'
    # value would have collapsed to a single colour group there too.
    placeholder_color = '#888888'

    for nn, key in enumerate(exp_keys):

        cfg = PLOT_CONFIG[key]

        if key == 'time' or 'time' in key:
            def format_xvals(x):
                return telescope_time_conversion(x, telescope=telescope)
        else:
            def format_xvals(x):
                return x

        tab_data = table_dict[key]

        if len(tab_data) == 0:
            print("Empty data table found. Skipping")
            continue

        for nspw, spw in enumerate(spw_nums):

            spw_mask = tab_data['spw'] == spw

            corr_name = 'corr' if 'corr' in tab_data.colnames else 'poln'

            these_corrs = corrs
            if these_corrs is None:
                these_corrs = np.unique(tab_data[corr_name][spw_mask].tolist())

            for nc, (corr, marker) in enumerate(zip(these_corrs, markers)):

                corr_mask = (tab_data[corr_name] == corr).tolist()
                full_mask = spw_mask & corr_mask

                customdata, hovertemplate = _build_hover(tab_data, full_mask,
                                                         cfg['hover'], telescope)

                n_points = int(np.count_nonzero(full_mask))

                colors_dict['SPW'].append([px.colors.qualitative.Safe[nspw % 11]
                                           for _ in range(n_points)])

                scan_data = tab_data['scan'][full_mask].tolist()
                scan_map_dict = {scan: n_uniq for n_uniq, scan in enumerate(np.unique(scan_data))}
                colors_dict['Scan'].append([px.colors.qualitative.Safe[scan_map_dict[scan] % 11]
                                            for scan in scan_data])

                colors_dict['Corr'].append([px.colors.qualitative.Safe[nc % 11]
                                            for _ in range(n_points)])

                for ant_label in ('ant1name', 'ant2name'):
                    color_key = 'Ant1' if ant_label == 'ant1name' else 'Ant2'
                    if ant_label in tab_data.colnames:
                        ant_data = tab_data[ant_label][full_mask].tolist()
                        ant_map_dict = {ant: n_uniq for n_uniq, ant in enumerate(np.unique(ant_data))}
                        colors_dict[color_key].append([px.colors.qualitative.Safe[ant_map_dict[ant] % 11]
                                                       for ant in ant_data])
                    else:
                        colors_dict[color_key].append([placeholder_color for _ in range(n_points)])

                spw_str = f"SPW {spw}"
                if spw in spw_labels:
                    spw_str += f"<br>({spw_labels[spw]})"

                row, col = row_col(key)

                fig.append_trace(go.Scattergl(x=format_xvals(tab_data[cfg['x']][full_mask]),
                                              y=tab_data[cfg['y']][full_mask],
                                              mode='markers',
                                              marker=dict(symbol=marker, size=7,
                                                          color=colors_dict['SPW'][-1]),
                                              customdata=customdata,
                                              hovertemplate=hovertemplate,
                                              name=spw_str,
                                              legendgroup=str(spw),
                                              showlegend=first_trace_flag(nn, nspw, nc)),
                                 row=row, col=col)

    return colors_dict


def _add_color_buttons(fig, colors_dict):

    buttons = [dict(label=label, method='update',
                    args=[{'marker.color': list(colors_dict[label])}])
              for label in ('SPW', 'Scan', 'Corr', 'Ant1', 'Ant2')]

    updatemenus = go.layout.Updatemenu(type='buttons', direction='left',
                                       showactive=True, x=1.01, xanchor="right",
                                       y=1.15, yanchor="top", buttons=buttons)

    fig.update_layout(updatemenus=[updatemenus], margin=dict(t=150))


def _add_line_velocity_shading(fig, row, col, tab_data, velocity_rows, line_to_spw):
    '''
    Shade the protected velocity range for each identified spectral line
    on a chan/freq-axis panel: a gray band between the low/high edges,
    plus a hoverable vertical line at each edge showing its frequency and
    Doppler velocity. A line with more than one disjoint velocity window,
    or an SPW with more than one identified line (e.g. the OH 1665/1667
    satellite lines both landing in the same window), gets one band per
    row of `velocity_rows` -- so those show up as two separate bands.

    `line_to_spw` (line name -> list of spw ids, from `spw_dict`) ties
    each band to the same `legendgroup` as its SPW's data traces, so
    toggling a SPW off in the legend hides its shading/lines too (and
    lets the x-axis autorange correctly to only the visible SPWs)
    instead of every identified line's markers always being shown
    regardless of which SPW is selected. A line with no SPW match (data
    inconsistency) falls back to an ungrouped, always-visible band.

    Frequencies are computed with the plain radio-convention Doppler
    formula against the SPECTRAL_WINDOW frame the 'freq' column is
    already in (TOPO, typically); this is the same LSRK-vs-TOPO
    approximation already accepted elsewhere in ReductionPipeline (at
    most ~30 km/s against SPW bandwidths of several MHz or more), and is
    unavoidable here since QAPlotter has no MS access to do better.

    Drawn as Scattergl traces (fill='toself' for the band, lines+markers
    for the hoverable edges), matching the data traces' rendering so
    z-order follows normal trace-insertion order. A protected velocity
    window is typically a few hundred kHz wide -- under a percent of the
    panel's full multi-SPW frequency range -- so the *fill* is often
    sub-pixel and effectively invisible at that zoomed-out view (this
    isn't a rendering bug, just geometry: confirmed by rendering the
    real figure with kaleido). The boundary lines are the reliable,
    always-visible marker regardless of zoom (bold, solid, high-contrast,
    and padded well past the data's y-range so they poke out above/below
    the point cloud); the shaded fill becomes clearly visible once a
    viewer zooms in on that specific line, which is normal, expected use
    of an interactive plot.
    '''

    if len(velocity_rows) == 0:
        return

    amp = np.asarray(tab_data['amp'])
    finite = amp[np.isfinite(amp)]
    if len(finite) == 0:
        return
    y_lo, y_hi = float(finite.min()), float(finite.max())
    pad = 0.15 * (y_hi - y_lo) if y_hi > y_lo else 1.0
    y_lo, y_hi = y_lo - pad, y_hi + pad
    y_line = np.linspace(y_lo, y_hi, 5)

    for vel_row in velocity_rows:

        restfreq = float(vel_row['restfreq_GHz'])
        # Higher velocity -> lower observed frequency (radio convention),
        # same formula as ReductionPipeline's lines_rest2obs.
        freq_at_vlow = restfreq * (1 - float(vel_row['vlow_kms']) / _C_KMS)
        freq_at_vhigh = restfreq * (1 - float(vel_row['vhigh_kms']) / _C_KMS)
        freq_lo, freq_hi = sorted((freq_at_vlow, freq_at_vhigh))

        # A line normally belongs to exactly one SPW; draw once per match
        # in the rare case it's identified in more than one (e.g.
        # overlapping SPW edges).
        matching_spws = line_to_spw.get(vel_row['line'], [None])

        for spw in matching_spws:

            legendgroup = str(spw) if spw is not None else None

            fig.append_trace(go.Scattergl(
                x=[freq_lo, freq_hi, freq_hi, freq_lo, freq_lo],
                y=[y_lo, y_lo, y_hi, y_hi, y_lo],
                mode='lines', fill='toself',
                fillcolor='rgba(105,105,105,0.35)',
                line=dict(width=0),
                hoverinfo='skip', showlegend=False,
                legendgroup=legendgroup,
            ), row=row, col=col)

            for freq, vel in ((freq_at_vlow, vel_row['vlow_kms']), (freq_at_vhigh, vel_row['vhigh_kms'])):
                fig.append_trace(go.Scattergl(
                    x=[freq] * len(y_line), y=y_line,
                    mode='lines',
                    line=dict(color='black', width=2.5),
                    hovertemplate=(f"Line: {vel_row['line']}<br>"
                                  f"Freq: {freq:.6f} GHz<br>"
                                  f"Velocity: {vel:.1f} km/s<extra></extra>"),
                    showlegend=False,
                    legendgroup=legendgroup,
                ), row=row, col=col)


def target_scan_figure(table_dict, meta_dict, show=False,
                       scatter_plot=go.Scattergl,
                       corrs=['RR', 'LL'],
                       spw_dict=None,
                       show_linesonly=False,
                       continuum_only=False,
                       telescope='vla',
                       velocity_table=None):
    '''
    Make a 3-panel figure for target scans.

    `show_linesonly` and `continuum_only` are mutually exclusive SPW
    filters (both need `spw_dict` to classify SPWs by their label; with
    neither set, or without `spw_dict`, every SPW present in the data is
    shown together). `make_field_plots` uses these to produce two
    separate figures per target -- a line-SPW view and a continuum-only
    view -- rather than one figure mixing both.

    `velocity_table`, if given (see `qaplotter.utils.load_velocity_table`),
    shades the protected velocity range of each spectral line identified
    for this target on the Amp vs. Freq panel. Meaningless for a
    continuum-only figure -- pass velocity_table=None there.
    '''

    exp_keys = ['amp_chan', 'amp_time', 'amp_uvdist']
    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    subplot_titles = [PLOT_CONFIG[key]['title'] for key in exp_keys]
    row_col = {key: (1, col) for col, key in enumerate(exp_keys, start=1)}

    fig = make_subplots(rows=1, cols=3, subplot_titles=subplot_titles)

    spw_nums = np.unique(table_dict['amp_chan']['spw'].tolist())

    # SPWs are classified as continuum or line by their spw_dict label
    # ("continuum" is only ever in a continuum SPW's label).
    spw_labels = {}
    if spw_dict is not None:
        for key in spw_dict:
            spw_labels[key] = spw_dict[key]['label']

    if continuum_only and spw_dict is not None:
        spw_nums = [key for key in spw_dict
                   if "continuum" in spw_dict[key]['label'] and key in spw_nums]
    elif show_linesonly and spw_dict is not None:
        spw_nums = [key for key in spw_dict
                   if "continuum" not in spw_dict[key]['label'] and key in spw_nums]

    colors_dict = _add_scan_traces(fig, exp_keys, table_dict, spw_nums, corrs,
                                   spw_labels, lambda key: row_col[key], telescope,
                                   first_trace_flag=lambda nn, nspw, nc: (nn == 0 and nc == 0))

    if velocity_table is not None and len(velocity_table) > 0:
        field_name = meta_dict['amp_time']['field']
        matching_rows = velocity_rows_for_field(velocity_table, field_name)
        if len(matching_rows) > 0:
            # Which SPW(s) each identified line belongs to, so its shading
            # can share that SPW's legendgroup (spw_dict labels are e.g.
            # "OH1665-OH1667" for a SPW carrying both lines).
            line_to_spw = {}
            if spw_dict is not None:
                for spw_id, info in spw_dict.items():
                    for line_name in info['label'].split('-'):
                        line_to_spw.setdefault(line_name, []).append(spw_id)

            row, col = row_col['amp_chan']
            _add_line_velocity_shading(fig, row, col, table_dict['amp_chan'],
                                       matching_rows, line_to_spw)

    fig.update_xaxes(rangeslider_visible=False,
                     tickformatstops=[dict(dtickrange=[None, 1000e3], value="%H:%M:%S"),
                                      dict(dtickrange=[1000e3, None], value="%H:%M:%S")],
                     row=1, col=2)

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
        title=f"Field: {meta['field']}  Intent: {meta_dict.get('intent', 'NONE')}<br>MS: {meta['vis']}",
        font=dict(family="Courier New, monospace", size=15, color="#7f7f7f")
    )

    _add_color_buttons(fig, colors_dict)

    if show:
        fig.show()

    return fig


def calibrator_scan_figure(table_dict, meta_dict, show=False, scatter_plot=go.Scattergl,
                           corrs=['RR', 'LL'], spw_dict=None,
                           telescope='vla'):
    '''
    Make a 12-panel (4x3) figure for calibrator scans.
    '''

    exp_keys = ['amp_chan', 'amp_time', 'amp_uvdist', 'amp_phase',
               'phase_chan', 'phase_time', 'phase_uvdist', 'ampresid_uvwave',
               'amp_ant1', 'phase_ant1']

    # Make the antenna plots optional because they were added later.
    if 'amp_ant1' not in table_dict.keys():
        exp_keys.remove('amp_ant1')
    if 'phase_ant1' not in table_dict.keys():
        exp_keys.remove('phase_ant1')

    for key in exp_keys:
        if key not in table_dict.keys():
            raise KeyError(f"Required dict key {key} not found.")

    grid_positions = {'amp_chan': (1, 1), 'amp_time': (1, 2), 'amp_uvdist': (1, 3),
                      'amp_phase': (1, 4), 'phase_chan': (2, 1), 'phase_time': (2, 2),
                      'phase_uvdist': (2, 3), 'ampresid_uvwave': (2, 4),
                      'amp_ant1': (3, 1), 'phase_ant1': (3, 2)}

    subplot_titles_bykey = {key: PLOT_CONFIG[key]['title'] for key in exp_keys}
    # Keep the original panel ordering (row-major over the 4x3 grid) for titles.
    subplot_titles = [subplot_titles_bykey[key] for key in
                      sorted(exp_keys, key=lambda key: grid_positions[key])]

    fig = make_subplots(rows=3, cols=4, subplot_titles=subplot_titles)

    spw_nums = np.unique(table_dict['amp_chan']['spw'].tolist())

    spw_labels = {}
    if spw_dict is not None:
        for key in spw_dict:
            if "continuum" in spw_dict[key]['label']:
                continue
            spw_labels[key] = spw_dict[key]['label']

    colors_dict = _add_scan_traces(fig, exp_keys, table_dict, spw_nums, corrs,
                                   spw_labels, lambda key: grid_positions[key], telescope,
                                   first_trace_flag=lambda nn, nspw, nc: (nn == 0 and nc == 0))

    for key in exp_keys:
        if "time" not in key:
            continue
        row, col = grid_positions[key]
        fig.update_xaxes(rangeslider_visible=False,
                         tickformatstops=[dict(dtickrange=[None, 1000], value="%H:%M:%S"),
                                          dict(dtickrange=[1000, None], value="%H:%M:%S")],
                         row=row, col=col)

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
    intent_str = meta_dict.get('intent', 'NONE')

    fig.update_layout(
        title=f"Field: {meta['field']}  Intent: {intent_str}<br>MS: {meta['vis']}",
        font=dict(family="Courier New, monospace", size=15, color="#7f7f7f")
    )

    _add_color_buttons(fig, colors_dict)

    if show:
        fig.show()

    return fig
