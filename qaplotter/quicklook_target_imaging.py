
import os
import warnings
import numpy as np
from glob import glob
import plotly.graph_objects as go
import plotly.express as px
import astropy.units as u
from astropy.stats import sigma_clip, mad_std
from pandas import DataFrame

from spectral_cube import SpectralCube
from spectral_cube.utils import StokesWarning

def make_quicklook_figures(foldername, output_foldername, suffix='image'):

    if not os.path.exists(output_foldername):
        os.mkdir(output_foldername)

    data_dict, data0_shape = load_quicklook_images(foldername, suffix=suffix)

    # Check if we have line or continuum data based on the cube shape.
    # NOTE: this assumes we have not mixed continuum and lines.
    is_line = data0_shape[0] > 1
    type_tag = "lines" if is_line else "continuum"

    targetname_dict = {}

    for target in data_dict:

        target_dict = data_dict[target]

        if is_line:
            fig = make_quicklook_lines_figure(target_dict, target)
        else:
            fig = make_quicklook_continuum_figure(target_dict, target)

        out_html_name = f"quicklook-{target}-{type_tag}-plotly_interactive.html"
        fig.write_html(f"{output_foldername}/{out_html_name}")

        targetname_dict[target] = out_html_name

    return targetname_dict

def load_quicklook_images(foldername, suffix='image'):
    '''
    Split by target and SPW.
    '''

    # Gather the requested files:
    all_cubenames = glob(f"{foldername}/*{suffix}")

    # Optionally could be FITS files instead. Check if no cubes are found in CASA format
    if len(all_cubenames) == 0:
        all_cubenames = glob(f"{foldername}/*{suffix}.fits")

    # The name format is quicklook-FIELD-spwNUM-LINE/CONT-MSNAME
    target_names = list(set([cubename.split('-')[1] for cubename in all_cubenames]))

    data_dict = {}

    data_shape = None

    for jj, target in enumerate(target_names):

        data_dict[target] = {}

        target_cubenames = [cubename for cubename in all_cubenames if f'{target}-' in cubename]

        spw_nums = [int(cubename.split('-')[2][3:]) for cubename in target_cubenames]
        line_names = [cubename.split('-')[3] for cubename in target_cubenames]

        # SPWs aren't unique b/c we have the 1665 and 1667 lines in the same SPW.
        # So we'll label with strings and iterate through multiples for keys.


        for ii, (spw, line, cubename) in enumerate(zip(spw_nums, line_names, target_cubenames)):
            # NOTE: this is OK because the continuum images still have 3 dimensions.
            # This works for now, but spectral-cube may eventually change

            # Read in single cubes until we get a valid shape out.
            # This is just to check continuum vs. spectral line.
            if data_shape is None:
                data0 = read_data(target_cubenames[ii])

                if data0 is not None:
                    data_shape = data0.shape

                    del data0

            # Make dict label
            current_keys = list(data_dict[target].keys())
            i = 0
            while True:
                spw_label = f"{spw}_{i}"
                if spw_label in current_keys:
                    i += 1
                else:
                    break

            data_dict[target][spw_label] = [line, cubename]

    return data_dict, data_shape


def read_data(cubename):

    with warnings.catch_warnings():
        warnings.simplefilter(action='ignore', category=StokesWarning)

        file_format = 'fits' if cubename.endswith('fits') else 'casa'

        try:
            this_cube = SpectralCube.read(cubename, format=file_format)
        except (ValueError, OSError) as err:
            print(f"{cubename} encountered error")
            print(f"{err}")

            return None

    # If an actual spectral line cube, change to VRAD
    if this_cube.shape[0] > 1:
        this_cube = this_cube.with_spectral_unit(u.m / u.s, velocity_convention='radio')

    return this_cube


def make_quicklook_continuum_figure(data_dict, target_name):
    '''
    One figure w/ N_SPW panels for each target.
    '''

    # Key are in form of SPW_i, where i is the ith line in that spw.
    spw_keys = np.array(list(data_dict.keys()))

    spw_order = np.argsort([int(key.split("_")[0]) for key in spw_keys])

    spw_keys_ordered = spw_keys[spw_order]

    # Handle the odd case where array shapes are not equal
    # Load the cubes in to get the shapes
    shape_dict = {}
    for key in spw_keys_ordered:
        this_cube = read_data(data_dict[key][1])
        if this_cube is None:
            continue

        shape_dict[key] = this_cube.shape
        del this_cube

    max_shape_key = max(shape_dict, key=lambda key: shape_dict[key][2])
    max_shape = shape_dict[max_shape_key]

    data_array = []
    data_info = {}
    valid_data = {}
    for key in spw_keys_ordered:

        # Load the cube in.
        this_cube = read_data(data_dict[key][1])
        if this_cube is None:
            valid_data[key] = False
        else:
            valid_data[key] = True

        try:
            this_data = this_cube.with_fill_value(0.).unitless_filled_data[:]
        except ValueError:
            valid_data[key] = False
            continue

        freq0 = (this_cube.header['CRVAL3'] * u.Unit(this_cube.header['CUNIT3'])).to(u.GHz)
        del_freq = (this_cube.header['CDELT3'] * u.Unit(this_cube.header['CUNIT3'])).to(u.GHz)

        data_unit = this_cube.unit

        del this_cube

        if this_data.shape != max_shape:
            new_data = np.zeros(max_shape, dtype=this_data.dtype)

            data_slice = tuple([slice(0, shape_i) for shape_i in this_data.shape])

            new_data[data_slice] = this_data

            data_array.append(new_data.squeeze())

        else:
            data_array.append(this_data.squeeze())

        # Estimate the noise. This is a ROUGH estimate only.
        rms_approx = mad_std(sigma_clip(this_data[np.nonzero(this_data)], sigma=3.)) * data_unit
        rms_approx = np.round(rms_approx.to(u.mJy / u.beam), 2)

        data_info[key] = [rms_approx, freq0, del_freq]

    data = np.stack(data_array, axis=-1)

    low_val, high_val = np.nanpercentile(data[np.nonzero(data)], [0.01, 99.99])

    facet_col_wrap = 5

    fig = px.imshow(data, facet_col=-1, facet_col_wrap=facet_col_wrap,
                    facet_col_spacing=0.01,
                    facet_row_spacing=0.04, origin='lower',
                    color_continuous_scale='gray_r',
                    range_color=[low_val, high_val],
                    binary_string=True, binary_compression_level=5)

    # Loop through cubes to extract the freq range from the headers
    # then include in the titles.
    # NOTE: the ordering is backwards by row and column... so the labels cannot
    # be given in the SPW order matching the data. Everything below is dealing with
    # this non-numpy axis ordering in plotly.

    ncols = facet_col_wrap
    nrows = (
        data.shape[-1] // ncols + 1
        if data.shape[-1] % ncols
        else data.shape[-1] // ncols
    )

    fig_order = np.arange(ncols * nrows)[::-1].reshape((nrows, ncols))[:, ::-1]
    # This matches the ordering in the subplots
    oned_order = fig_order.ravel()
    # Except that it includes >data.shape[-1] values that we first need to clip out.
    oned_order = oned_order[oned_order < data.shape[-1]]

    spw_keys_ordered = [spw for spw in spw_keys_ordered if valid_data[spw]]

    # These should now be the same shape
    assert len(oned_order) == len(spw_keys_ordered)


    for index in range(data.shape[-1]):

        # Get position in data from the 1D ordering
        idx = oned_order[index]

        # Get the corresponding SPW to that idx in the data
        spw_label = spw_keys_ordered[idx]

        spw = spw_label.split("_")[0]

        rms_approx, freq0, del_freq = data_info[spw_label]

        freq_min = np.round(freq0 - del_freq * 0.5, 2).value
        freq_max = np.round(freq0 + del_freq * 0.5, 2).value

        fig.layout.annotations[index]['text'] = f"SPW {spw} ({freq_min}-{freq_max} GHz)<br>rms={rms_approx}"

    fig.update_layout(
        title=target_name,
        margin=dict(t=100, pad=4),
        font=dict(family="Courier New, monospace",
                  size=15,
                  color="#7f7f7f")
    )

    return fig


def make_quicklook_lines_figure(data_dict, target_name):
    '''
    One figure animated along the spectral axis w/ N_SPW panels for each target.

    Note that we assume that the spectral axis is the same in all SPWs.
    '''

    # Key are in form of SPW_i, where i is the ith line in that spw.
    spw_keys = np.array(list(data_dict.keys()))
    line_names = np.array([data_dict[key][0] for key in data_dict])

    spw_order = np.argsort([int(key.split("_")[0]) for key in spw_keys])

    spw_keys_ordered = spw_keys[spw_order]

    # Handle the odd case where array shapes are not equal
    # Load the cubes in to get the shapes
    shape_dict = {}
    for key in spw_keys_ordered:
        this_cube = read_data(data_dict[key][1])
        if this_cube is None:
            continue

        shape_dict[key] = this_cube.shape
        del this_cube

    max_shape_key = max(shape_dict, key=lambda key: shape_dict[key][2])
    max_shape = shape_dict[max_shape_key]

    if "HI" in line_names:
        idx_noise_calc = spw_keys[line_names == "HI"][0]
    else:
        idx_noise_calc = spw_keys_ordered[0]

    data_array = []
    data_info = {}
    valid_data = {}
    for kk, key in enumerate(spw_keys_ordered):

        # Load the cube in.
        this_cube = read_data(data_dict[key][1])
        if this_cube is None:
            valid_data[key] = False
            continue
        else:
            valid_data[key] = True

        try:
            this_data = this_cube.with_fill_value(0.).unitless_filled_data[:]
        except ValueError:
            valid_data[key] = False
            continue

        if key == idx_noise_calc or kk == len(spw_keys_ordered) - 1:
            noise_rms = mad_std(this_data[np.nonzero(this_data)], ignore_nan=True)
            high_val = np.nanpercentile(this_data[np.nonzero(this_data)], 99.5)

        # Also get the spectral axis. Assumes cubes are spectrally matched which is our default.
        if kk == 0:
            spectral_axis = this_cube.spectral_axis.to(u.km / u.s)

            chan_width = np.round(np.abs(np.diff(spectral_axis)[0]), 1)

        data_unit = this_cube.unit

        del this_cube

        if this_data.shape != max_shape:
            new_data = np.zeros(max_shape, dtype=this_data.dtype)

            data_slice = tuple([slice(0, shape_i) for shape_i in this_data.shape])

            new_data[data_slice] = this_data

            data_array.append(new_data.squeeze())

        else:
            data_array.append(this_data.squeeze())

        rms_approx = mad_std(sigma_clip(this_data[np.nonzero(this_data)], sigma=3.)) * data_unit
        rms_approx = np.round(rms_approx.to(u.mJy / u.beam), 2)

        data_info[key] = [rms_approx, chan_width]


    data = np.stack(data_array)

    # Strip units if present
    noise_rms = noise_rms.value if hasattr(noise_rms, 'unit') else noise_rms
    high_val = high_val.value if hasattr(high_val, 'unit') else high_val

    low_val = -2 * noise_rms

    fig = px.imshow(data, animation_frame=1, facet_col=0,
                    labels=dict(animation_frame="Channel"),
                    origin='lower', color_continuous_scale='gray_r',
                    range_color=[low_val, high_val],
                    binary_string=True, binary_compression_level=5)

    i = 0
    for spw_label in spw_keys_ordered:

        # Check if the data was OK and we were able to load it in.
        if not valid_data[spw_label]:
            continue

        spw = spw_label.split("_")[0]

        line_label = data_dict[spw_label][0]

        rms_approx = data_info[spw_label][0]
        chan_width = data_info[spw_label][1]

        fig.layout.annotations[i]['text'] = f"SPW {spw} ({line_label})<br>rms={rms_approx}<br>in {chan_width} channels"

        i += 1

    # Velocity steps
    for step in fig.layout['sliders'][0]['steps']:
        chan_num = int(step.label)

        # Update the label to include the velocity:
        step.label = f"{chan_num} ({np.round(spectral_axis[chan_num], 1)})"

    fig.update_layout(autosize=True,
                      height=600,)

    fig.update_layout(
        title=target_name,
        margin=dict(t=100, pad=4),
        font=dict(family="Courier New, monospace",
                  size=15,
                  color="#7f7f7f")
    )

    return fig


def make_quicklook_continuum_noise_summary(all_data_dict, flux_unit=u.mJy / u.beam):
    '''
    Generate a noise summary per field per SPW to quickly identify
    outlier images.
    '''

    all_data_info = []

    for name in all_data_dict:

        data_dict = all_data_dict[name]

        # Key are in form of SPW_i, where i is the ith line in that spw.
        spw_keys = np.array(list(data_dict.keys()))

        spw_order = np.argsort([int(key.split("_")[0]) for key in spw_keys])

        spw_keys_ordered = spw_keys[spw_order]


        for key in spw_keys_ordered:

            # Load the cube in.
            this_cube = read_data(data_dict[key][1])
            if this_cube is None:
                continue

            try:
                this_data = this_cube.unitless_filled_data[:]
            except ValueError:
                continue

            freq0 = (this_cube.header['CRVAL3'] * u.Unit(this_cube.header['CUNIT3'])).to(u.GHz)
            del_freq = (this_cube.header['CDELT3'] * u.Unit(this_cube.header['CUNIT3'])).to(u.GHz)

            data_unit = this_cube.unit

            del this_cube

            # Estimate the noise. This is a ROUGH estimate only.
            rms_approx = mad_std(sigma_clip(this_data[np.isfinite(this_data)], sigma=3.)) * data_unit
            rms_approx = rms_approx.to(flux_unit).value

            all_data_info.append([name, key.split("_")[0],
                                  rms_approx, flux_unit.to_string(),
                                  freq0.value,
                                  del_freq.value])

    df = DataFrame(all_data_info,
                   columns=['name', "spw", "rms", "rms_unit", 'freq0', 'delta_freq'])

    # return df

    fig = px.line(df.sort_values(by='freq0'),
                  x='freq0', y='rms', line_group='name', error_x='delta_freq',
                  color='name',
                  hover_data={'spw': True, 'freq0': ":.3f"},
                  labels={"freq0": "Freq. (GHz)",
                          "delta_freq": "Bandwidth (GHz)",
                          "spw": "SPW",
                          "rms": f"RMS ({flux_unit.to_string()})",
                          "name": "Field"},
                  category_orders={"name": df.sort_values(by="name")['name']},
                  markers=True)


    spw_order = np.unique(df['spw']).astype("int")
    spw_order.sort()
    spw_order = [str(val) for val in spw_order]

    fig2 = px.line(df.sort_values(by='name'),
                  x='name', y='rms', line_group='spw', error_x='delta_freq',
                  color='spw',
                  hover_data={'spw': True, 'freq0': ":.3f"},
                  labels={"freq0": "Freq. (GHz)",
                          "delta_freq": "Bandwidth (GHz)",
                          "spw": "SPW",
                          "rms": f"RMS ({flux_unit.to_string()})",
                          "name": "Field"},
                  category_orders={"spw": spw_order,
                                   "name": df.sort_values(by="name")['name']},
                  markers=True)

    return fig, fig2, df


def make_quicklook_lines_noise_summary(all_data_dict, flux_unit=u.mJy / u.beam):
    '''
    Generate a noise summary per field per SPW to quickly identify
    outlier images.
    '''

    all_data_info = []

    for name in all_data_dict:

        data_dict = all_data_dict[name]

        # Key are in form of SPW_i, where i is the ith line in that spw.
        spw_keys = np.array(list(data_dict.keys()))

        spw_order = np.argsort([int(key.split("_")[0]) for key in spw_keys])

        spw_keys_ordered = spw_keys[spw_order]


        for key in spw_keys_ordered:

            line_label = data_dict[key][0]

            # Load the cube in.
            this_cube = read_data(data_dict[key][1])
            if this_cube is None:
                continue

            try:
                this_data = this_cube.unitless_filled_data[:]
            except ValueError:
                continue

            chan_width = np.round(np.abs(np.diff(this_cube.spectral_axis)[0]), 1)

            data_unit = this_cube.unit

            del this_cube

            # Estimate the noise. This is a ROUGH estimate only.
            rms_approx = mad_std(sigma_clip(this_data[np.isfinite(this_data)], sigma=3.)) * data_unit
            rms_approx = rms_approx.to(flux_unit).value


            all_data_info.append([name, key.split("_")[0],
                                  rms_approx, flux_unit.to_string(),
                                  chan_width.to(u.km / u.s).value,
                                  line_label])

    df = DataFrame(all_data_info,
                   columns=['name', "spw", "rms", "rms_unit", 'chan_width', 'line_name'])

    fig = px.line(df.sort_values(by='line_name'),
                  x='line_name', y='rms', line_group='name',
                  color='name',
                  hover_data={'spw': True, 'chan_width': ":.2f"},
                  labels={"spw": "SPW",
                          "rms": f"RMS ({flux_unit.to_string()})",
                          "name": "Field",
                          "chan_width": "Channel (km/s)",
                          "line_name": "Spectral Line"},
                  category_orders={"name": df.sort_values(by="name")['name']},
                  markers=True)

    fig2 = px.line(df.sort_values(by='name'),
                  x='name', y='rms', line_group='line_name',
                  color='line_name',
                  hover_data={'line_name': True, 'chan_width': ":.2f"},
                  labels={"spw": "SPW",
                          "rms": f"RMS ({flux_unit.to_string()})",
                          "name": "Field",
                          "chan_width": "Channel (km/s)",
                          "line_name": "Spectral Line"},
                  category_orders={"line_name": df.sort_values(by="line_name")['line_name'],
                                   "name": df.sort_values(by="name")['name']},
                  markers=True)

    return fig, fig2, df

