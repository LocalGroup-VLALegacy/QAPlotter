
import os
import numpy as np
from glob import glob
import plotly.graph_objects as go
import plotly.express as px
import astropy.units as u
from astropy.stats import sigma_clip, mad_std

from spectral_cube import SpectralCube

def make_quicklook_figures(foldername, output_foldername, suffix='image'):

    if not os.path.exists(output_foldername):
        os.mkdir(output_foldername)

    data_dict = load_quicklook_images(foldername, suffix=suffix)

    # Check if we have line or continuum data based on the cube shape.
    # NOTE: this assumes we have not mixed continuum and lines.
    targ0_dict = data_dict[list(data_dict.keys())[0]]
    targ_spw0_dict = targ0_dict[list(targ0_dict.keys())[0]]

    is_line = targ_spw0_dict[1].shape[0] > 1
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

    # The name format is quicklook-FIELD-spwNUM-LINE/CONT-MSNAME
    target_names = list(set([cubename.split('-')[1] for cubename in all_cubenames]))

    data_dict = {}

    for target in target_names:

        data_dict[target] = {}

        target_cubenames = [cubename for cubename in all_cubenames if target in cubename]

        spw_nums = [int(cubename.split('-')[2][3:]) for cubename in target_cubenames]
        line_names = [cubename.split('-')[3] for cubename in target_cubenames]

        # SPWs aren't unique b/c we have the 1665 and 1667 lines in the same SPW.
        # So we'll label with strings and iterate through multiples for keys.
        for i, (spw, line, cubename) in enumerate(zip(spw_nums, line_names, target_cubenames)):
            # NOTE: this is OK because the continuum images still have 3 dimensions.
            # This works for now, but spectral-cube may eventually change
            this_cube = SpectralCube.read(target_cubenames[i], format='casa')

            # If an actual spectral line cube, change to VRAD
            if this_cube.shape[0] > 1:
                this_cube = this_cube.with_spectral_unit(u.km / u.s, velocity_convention='radio')

            # Make dict label
            current_keys = list(data_dict[target].keys())
            i = 0
            while True:
                spw_label = f"{spw}_{i}"
                if spw_label in current_keys:
                    i += 1
                else:
                    break

            data_dict[target][spw_label] = [line, this_cube, cubename]

    return data_dict


def make_quicklook_continuum_figure(data_dict, target_name):
    '''
    One figure w/ N_SPW panels for each target.
    '''

    # Key are in form of SPW_i, where i is the ith line in that spw.
    spw_keys = np.array(list(data_dict.keys()))

    spw_order = np.argsort([int(key.split("_")[0]) for key in spw_keys])

    spw_keys_ordered = spw_keys[spw_order]

    # Handle the odd case where array shapes are not equal
    shape_dict = {}
    for key in spw_keys_ordered:
        shape_dict[key] = data_dict[key][1].shape

    max_shape_key = max(shape_dict, key=lambda key: shape_dict[key][2])
    max_shape = shape_dict[max_shape_key]

    data_array = []
    for key in spw_keys_ordered:
        this_data = data_dict[key][1].with_fill_value(0.).unitless_filled_data[:]

        if this_data.shape != max_shape:
            new_data = np.zeros(max_shape, dtype=this_data.dtype)

            data_slice = tuple([slice(0, shape_i) for shape_i in this_data.shape])

            new_data[data_slice] = this_data

            data_array.append(data_array)

        else:
            data_array.append(this_data)

    data = np.stack(data_array)

    fig = px.imshow(data, facet_col=0, facet_col_wrap=5, facet_col_spacing=0.01,
                    facet_row_spacing=0.04, origin='lower',
                    color_continuous_scale='gray_r')

    # Loop through cubes to extract the freq range from the headers
    # then include in the titles.
    for i, spw_label in enumerate(spw_keys_ordered):

        cube = data_dict[spw_label][1]

        # Estimate the noise. This is a ROUGH estimate only.
        rms_approx = mad_std(sigma_clip(cube, sigma=3.)) * cube.unit
        rms_approx = np.round(rms_approx.to(u.mJy / u.beam), 2)

        freq0 = (cube.header['CRVAL3'] * u.Unit(cube.header['CUNIT3'])).to(u.GHz)
        del_freq = (cube.header['CDELT3'] * u.Unit(cube.header['CUNIT3'])).to(u.GHz)

        freq_min = np.round(freq0 - del_freq * 0.5, 2).value
        freq_max = np.round(freq0 + del_freq * 0.5, 2).value

        spw = spw_label.split("_")[0]

        fig.layout.annotations[i]['text'] = f"SPW {spw} ({freq_min}-{freq_max} GHz)<br>rms={rms_approx}"

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

    data_array = []
    for key in spw_keys_ordered:
        this_data = data_dict[key][1].with_fill_value(0.).unitless_filled_data[:]

        if this_data.shape != max_shape:
            new_data = np.zeros(max_shape, dtype=this_data.dtype)

            data_slice = tuple([slice(0, shape_i) for shape_i in this_data.shape])

            new_data[data_slice] = this_data

            data_array.append(data_array)

        else:
            data_array.append(this_data)

    data = np.stack(data_array)

    # Use the HI data (if present) to estimate color range.
    if "HI" in line_names:
        hi_label = spw_keys[line_names == "HI"][0]

        noise_rms = data_dict[hi_label][1].mad_std()
        high_val = np.nanpercentile(data_dict[hi_label][1], 99.5)
    else:
        noise_rms = data_dict[list(data_dict.keys())[0]][1].mad_std()
        high_val = np.nanpercentile(data_dict[list(data_dict.keys())[0]][1], 99.5)

    noise_rms = noise_rms.value if hasattr(noise_rms, 'unit') else noise_rms
    high_val = high_val.value if hasattr(high_val, 'unit') else high_val

    low_val = -2 * noise_rms

    fig = px.imshow(data, animation_frame=1, facet_col=0, binary_string=False,
                    labels=dict(animation_frame="Channel"),
                    origin='lower', color_continuous_scale='gray_r',
                    range_color=[low_val, high_val])

    for i, spw_label in enumerate(spw_keys_ordered):

        spw = spw_label.split("_")[0]

        line_label = data_dict[spw_label][0]
        fig.layout.annotations[i]['text'] = f"SPW {spw} ({line_label})"

    spec_axis = data_dict[spw_keys_ordered[0]][1].spectral_axis

    # Velocity steps
    for step in fig.layout['sliders'][0]['steps']:
        chan_num = int(step.label)

        # Update the label to include the velocity:
        step.label = f"{chan_num} ({np.round(spec_axis[chan_num], 1)})"

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
