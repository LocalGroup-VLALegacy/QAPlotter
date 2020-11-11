
'''
Function for embedding interactive plots and adding links, etc.
'''

from pathlib import Path


def make_all_html_links(folder, field_list, ms_info_dict):
    '''
    Make and save all html files for linking the interactive plots
    together.
    '''

    mypath = Path(folder)

    # CSS style
    css_file = mypath / "qa_plot.css"

    if css_file.exists():
        css_file.unlink()

    print(css_page_style(), file=open(css_file, 'a'))

    # index file
    index_file = mypath / "index.html"

    if index_file.exists():
        index_file.unlink()

    print(make_index_html_page(field_list, ms_info_dict), file=open(index_file, 'a'))

    # Loop through the fields
    for i, field in enumerate(field_list):

        field_file = mypath / f"linker_{field}.html"

        if field_file.exists():
            field_file.unlink()

        print(make_plot_html_page(field_list, active_idx=i),
              file=open(field_file, 'a'))


def make_index_html_page(field_list, ms_info_dict):

    html_string = make_html_preamble()

    html_string += make_sidebar(field_list, active_idx=None)

    # Add in MS info:
    html_string += '<div class="content" id="basic">\n'
    html_string += f'<h2>{ms_info_dict["vis"]}</h2>\n'
    # html_string += f'<p>{ms_info_dict["date"]}</p>\n'
    html_string += '</div>\n\n'

    html_string += make_html_suffix()

    return html_string


def make_plot_html_page(field_list, active_idx=0):

    html_string = make_html_preamble()

    prev_field = field_list[active_idx - 1] if active_idx != 0 else None
    next_field = field_list[active_idx + 1] if active_idx < len(field_list) - 1 else None

    html_string += make_next_previous_navbar(prev_field, next_field,
                                             current_field=field_list[active_idx])

    html_string += make_sidebar(field_list, active_idx=active_idx)

    html_string += make_content_div(field_list[active_idx])

    html_string += make_html_suffix()

    return html_string


def css_page_style():
    '''
    '''

    css_style_str = \
'''
body {
  margin: 0;
  font-family: "Lato", sans-serif;
}


 /* The navigation bar */
.navbar {
  overflow: auto;
  background-color: #f1f1f1;
  position: fixed; /* Set the navbar to fixed position */
  top: 0; /* Position the navbar at the top of the page */
  width: 100%; /* Full width */
  margin-left: 200px;
}

/* Links inside the navbar */
.navbar a {
  float: left;
  display: block;
  color: black;
  text-align: center;
  padding: 14px 16px;
  text-decoration: none;
}

/* Change background on mouse-over */
.navbar a:hover {
  background: #555;
  color: white;
}

/* Main content */
.main {
  margin-top: 30px; /* Add a top margin to avoid content overlay */
}

.sidebar {
  margin: 0;
  padding: 0;
  width: 200px;
  background-color: #f1f1f1;
  position: fixed;
  height: 100%;
  overflow: auto;
}

.sidebar a {
  display: block;
  color: black;
  padding: 16px;
  text-decoration: none;
}

.sidebar a.active {
  background-color: #4CAF50;
  color: white;
}

.sidebar a:hover:not(.active) {
  background-color: #555;
  color: white;
}

div.content {
  margin-top: 45px;
  margin-left: 200px;
  padding: 1px 16px;
  height: 1000px;
}

@media screen and (max-width: 700px) {
  .sidebar {
    width: 100%;
    height: auto;
    position: relative;
  }
  .sidebar a {float: left;}
  div.content {margin-left: 0;}
}

@media screen and (max-width: 400px) {
  .sidebar a {
    text-align: center;
    float: none;
  }
}
'''

    return css_style_str


def make_html_preamble():

    html_preamble_string = \
'''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" type="text/css" href="qa_plot.css">
</head>
<body>\n\n
'''

    return html_preamble_string

def make_html_suffix():

    html_suffix_string = "</body>\n</html>\n"

    return html_suffix_string


def make_next_previous_navbar(prev_field=None, next_field=None,
                              current_field=None):
    '''
    Navbar links
    '''

    if prev_field is None and next_field is None:
        return ""

    navbar_string = '<div class="navbar">\n'

    if prev_field is not None:
        navbar_string += f'    <a href="linker_{prev_field}.html">{prev_field} (Previous)</a>\n'
    else:
        # If None, use current field
        navbar_string += f'    <a href="linker_{current_field}.html">{current_field} (Previous)</a>\n'

    if next_field is not None:
        navbar_string += f'    <a href="linker_{next_field}.html">{next_field} (Next)</a>\n'
    else:
        # If None, use current field
        navbar_string += f'    <a href="linker_{current_field}.html">{current_field} (Next)</a>\n'

    navbar_string += "</div>\n\n"

    return navbar_string


def make_sidebar(field_list, active_idx=0):
    '''
    Persistent side bar with all field names. For quick switching.
    '''

    sidebar_string = '<div class="sidebar">\n'

    if active_idx is None:
        sidebar_string += '    <a class="active" href="index.html">Home</a>\n'
    else:
        sidebar_string += '    <a class="" href="index.html">Home</a>\n'

    for i, field in enumerate(field_list):

        # Set as active
        if i == active_idx:
            class_is = "active"
        else:
            class_is = ""

        sidebar_string += f'    <a class="{class_is}" href="linker_{field}.html">{i}. {field}</a>\n'

    sidebar_string += '</div>\n\n'

    return sidebar_string


def make_content_div(field):

    content_string = f'<div class="content" id="{field}">\n'

    content_string += f'    <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="{field}_plotly_interactive.html" height="1000" width="100%"></iframe>\n'

    content_string += '</div>\n\n'

    return content_string


#################################
# Functions for the bandpass plots, not the per field plots


def make_bandpass_all_html_links(folder, bandpass_plots, ms_info_dict):
    '''
    Make and save all html files for linking the interactive plots
    together.
    '''

    mypath = Path(folder)

    # CSS style
    css_file = mypath / "qa_plot.css"

    if css_file.exists():
        css_file.unlink()

    print(css_page_style(), file=open(css_file, 'a'))

    # index file
    index_file = mypath / "index.html"

    if index_file.exists():
        index_file.unlink()

    print(make_index_bandpass_html_page(bandpass_plots, ms_info_dict), file=open(index_file, 'a'))

    # Loop through the fields
    for i, bpplot in enumerate(bandpass_plots):

        field_file = mypath / f"linker_bp_{i}.html"

        if field_file.exists():
            field_file.unlink()

        print(make_plot_bandpass_html_page(bandpass_plots, active_idx=i),
              file=open(field_file, 'a'))


def make_index_bandpass_html_page(bandpass_plots, ms_info_dict):

    html_string = make_html_preamble()

    html_string += make_sidebar_bandpass(bandpass_plots, active_idx=None)

    # Add in MS info:
    html_string += '<div class="content" id="basic">\n'
    html_string += f'<h2>{ms_info_dict["vis"]}</h2>\n'
    # html_string += f'<p>{ms_info_dict["date"]}</p>\n'
    html_string += '</div>\n\n'

    html_string += make_html_suffix()

    return html_string


def make_plot_bandpass_html_page(bandpass_plots, active_idx=0):

    html_string = make_html_preamble()

    prev_field = active_idx - 1 if active_idx != 0 else None
    next_field = active_idx + 1 if active_idx < len(bandpass_plots) - 1 else None

    html_string += make_next_previous_navbar_bandpass(prev_field, next_field)

    html_string += make_sidebar_bandpass(bandpass_plots, active_idx=active_idx)

    html_string += make_content_bandpass_div(bandpass_plots[active_idx])

    html_string += make_html_suffix()

    return html_string


def make_next_previous_navbar_bandpass(prev_field=None, next_field=None):
    '''
    Navbar links
    '''

    if prev_field is None and next_field is None:
        return ""

    navbar_string = '<div class="navbar">\n'

    if prev_field is not None:
        navbar_string += f'    <a href="linker_bp_{prev_field}.html">Bandpass Plot {prev_field} (Previous)</a>\n'

    if next_field is not None:
        navbar_string += f'    <a href="linker_bp_{next_field}.html">Bandpass Plot {next_field} (Next)</a>\n'

    navbar_string += "</div>\n\n"

    return navbar_string


def make_sidebar_bandpass(bandpass_plots, active_idx=0):
    '''
    Persistent side bar with all field names. For quick switching.
    '''

    sidebar_string = '<div class="sidebar">\n'

    if active_idx is None:
        sidebar_string += '    <a class="active" href="index.html">Home</a>\n'
    else:
        sidebar_string += '    <a class="" href="index.html">Home</a>\n'

    for i, bpplot in enumerate(bandpass_plots):

        # Set as active
        if i == active_idx:
            class_is = "active"
        else:
            class_is = ""

        sidebar_string += f'    <a class="{class_is}" href="linker_bp_{i}.html">Bandpass {i}</a>\n'

    sidebar_string += '</div>\n\n'

    return sidebar_string


def make_content_bandpass_div(bandpass_plot):

    content_string = f'<div class="content" id="{bandpass_plot.rstrip(".html")[-1]}">\n'

    content_string += f'    <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="{bandpass_plot}" height="1000" width="100%"></iframe>\n'

    content_string += '</div>\n\n'

    return content_string
