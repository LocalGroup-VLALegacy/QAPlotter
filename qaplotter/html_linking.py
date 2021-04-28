
'''
Function for embedding interactive plots and adding links, etc.
'''

from pathlib import Path

from .utils import datetime_from_msname


def return_webserver_link():
    '''
    Return a link to the webserver home page.
    '''

    return "../"


def generate_webserver_track_link(flagging_sheet_link):
    '''
    Return a link to the home page for a given track.

    '''

    # TODO: Update to handle both continuum and lines in one page.

    track_links = {}

    # track_links["Webserver Home"] = return_webserver_link()
    track_links["Webserver Home"] = "../../../../"

    track_links["Project Home"] = "../../"

    track_links["Track Home"] = "index.html"

    if flagging_sheet_link is not None:
        track_links["Flagging Sheet"] = flagging_sheet_link
    else:
        track_links["Flagging Sheet"] = ""

    track_links["Weblog"] = "weblog/html/index.html"

    track_links['Field QA Plots'] = "scan_plots_QAplots/index.html"

    track_links['Calib QA Plots'] = "final_caltable_QAplots/index.html"

    track_links['Field Names'] = "scan_plots_QAplots/fieldnames.txt"

    return track_links


def make_index_html_homepage(folder, ms_info_dict, flagging_sheet_link=None):
    '''
    Home page for the track with links to the weblogs, QA plots, etc.
    '''


    html_string = make_html_preamble()

    link_locations = generate_webserver_track_link(flagging_sheet_link)

    html_string += '<div class="navbar">\n'

    for linkname in link_locations:

        html_string += f'    <a href="{link_locations[linkname]}">{linkname}</a>\n'

    html_string += "</div>\n\n"

    # Add in MS info:
    html_string += '<div class="content" id="basic">\n'
    html_string += f'<h2>{ms_info_dict["vis"]}</h2>\n'

    # If the msname keeps the SDM naming format, extract the UTC datetime
    try:
        utc_datetime = datetime_from_msname(ms_info_dict["vis"])
        html_string += f'<p>UTC datetime: {utc_datetime.strftime("%Y/%m/%d/%H:%M")}</p>\n'
    except (AssertionError, ValueError):
        pass

    # Embed the weblog into the main page.
    html_string += '\n'
    html_string += '<iframe src="weblog/html/index.html" height="100%" width=90%>\n'
    html_string += 'If you are seeing this, you need a browser understands IFrames.\n'
    html_string += '</iframe>\n'

    html_string += '</div>\n\n'

    html_string += make_html_suffix()

    return html_string


def make_html_homepage(folder, ms_info_dict, flagging_sheet_link=None):

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

    print(make_index_html_homepage(folder, ms_info_dict,
                                   flagging_sheet_link=flagging_sheet_link),
          file=open(index_file, 'a'))


def make_all_html_links(track_folder, folder, field_list, ms_info_dict,
                        flagging_sheet_link=None):
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

    print(make_index_html_page(flagging_sheet_link, field_list, ms_info_dict),
          file=open(index_file, 'a'))

    # Loop through the fields
    for i, field in enumerate(field_list):

        field_file = mypath / f"linker_{field}.html"

        if field_file.exists():
            field_file.unlink()

        print(make_plot_html_page(flagging_sheet_link, field_list, active_idx=i),
              file=open(field_file, 'a'))


def make_index_html_page(flagging_sheet_link, field_list, ms_info_dict):

    html_string = make_html_preamble()

    # Add navigation bar with link to other QA products
    active_idx = 0
    html_string += make_next_previous_navbar(flagging_sheet_link, prev_field=None,
                                             next_field=field_list[min(active_idx + 1, len(field_list))],
                                             current_field=field_list[active_idx])

    html_string += make_sidebar(field_list, active_idx=None)

    # Add in MS info:
    html_string += '<div class="content" id="basic">\n'
    html_string += f'<h2>{ms_info_dict["vis"]}</h2>\n'

    # If the msname keeps the SDM naming format, extract the UTC datetime
    try:
        utc_datetime = datetime_from_msname(ms_info_dict["vis"])
        html_string += f'<p>UTC datetime: {utc_datetime.strftime("%Y/%m/%d/%H:%M")}</p>\n'
    except (AssertionError, ValueError):
        pass

    html_string += '</div>\n\n'

    html_string += make_html_suffix()

    return html_string


def make_plot_html_page(flagging_sheet_link, field_list, active_idx=0):

    html_string = make_html_preamble()

    prev_field = field_list[active_idx - 1] if active_idx != 0 else None
    next_field = field_list[active_idx + 1] if active_idx < len(field_list) - 1 else None

    html_string += make_next_previous_navbar(flagging_sheet_link, prev_field, next_field,
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


def make_next_previous_navbar(flagging_sheet_link, prev_field=None, next_field=None,
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

    # Add in links to other QA products + home page
    link_locations = generate_webserver_track_link(flagging_sheet_link)

    for linkname in link_locations:

        navbar_string += f'    <a href="../{link_locations[linkname]}">{linkname}</a>\n'


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

        sidebar_string += f'    <a class="{class_is}" href="linker_{field}.html">{i+1}. {field}</a>\n'

    sidebar_string += '</div>\n\n'

    return sidebar_string


def make_content_div(field):

    content_string = f'<div class="content" id="{field}">\n'

    content_string += f'    <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="{field}_plotly_interactive.html" height="1000" width="100%"></iframe>\n'

    content_string += '</div>\n\n'

    return content_string


#################################
# Functions for the calibration table plots, not the per field plots


def make_caltable_all_html_links(track_folder, folder, cal_plots, ms_info_dict,
                                 flagging_sheet_link=None):
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

    print(make_index_caltable_html_page(flagging_sheet_link, cal_plots, ms_info_dict),
          file=open(index_file, 'a'))

    # Loop through the fields
    for i, calplot in enumerate(cal_plots):

        field_file = mypath / f"linker_bp_{i}.html"

        if field_file.exists():
            field_file.unlink()

        print(make_plot_caltable_html_page(flagging_sheet_link,
                                           cal_plots,
                                           active_idx=i),
              file=open(field_file, 'a'))


def make_index_caltable_html_page(flagging_sheet_link, cal_plots, ms_info_dict):

    html_string = make_html_preamble()

    # Add links to other index files, etc.
    active_idx = 0
    next_field = active_idx + 1 if active_idx < len(cal_plots) - 1 else None

    html_string += make_next_previous_navbar_caltables(flagging_sheet_link,
                                                      prev_field=None,
                                                      next_field=next_field,
                                                      next_field_name=list(cal_plots.keys())[next_field],
                                                      current_field=active_idx)

    html_string += make_sidebar_caltables(cal_plots, active_idx=None)

    # Add in MS info:
    html_string += '<div class="content" id="basic">\n'
    html_string += f'<h2>{ms_info_dict["vis"]}</h2>\n'

    # If the msname keeps the SDM naming format, extract the UTC datetime
    try:
        utc_datetime = datetime_from_msname(ms_info_dict["vis"])
        html_string += f'<p>UTC datetime: {utc_datetime.strftime("%Y/%m/%d/%H:%M")}</p>\n'
    except (AssertionError, ValueError):
        pass

    html_string += '</div>\n\n'

    html_string += make_html_suffix()

    return html_string


def make_plot_caltable_html_page(flagging_sheet_link, cal_plots, active_idx=0):

    html_string = make_html_preamble()

    prev_field = active_idx - 1 if active_idx != 0 else None
    next_field = active_idx + 1 if active_idx < len(cal_plots) - 1 else None

    cal_keys = list(cal_plots.keys())

    current_field_name = cal_keys[active_idx]
    prev_field_name = cal_keys[prev_field] if prev_field is not None else None
    next_field_name = cal_keys[next_field] if next_field is not None else None

    html_string += make_next_previous_navbar_caltables(flagging_sheet_link,
                                                       prev_field=prev_field,
                                                       prev_field_name=prev_field_name,
                                                       next_field=next_field,
                                                       next_field_name=next_field_name,
                                                       current_field=active_idx,
                                                       current_field_name=current_field_name)

    html_string += make_sidebar_caltables(cal_plots, active_idx=active_idx)

    html_string += make_content_caltables_div(cal_plots[current_field_name])

    html_string += make_html_suffix()

    return html_string


def make_next_previous_navbar_caltables(flagging_sheet_link, prev_field=None, next_field=None,
                                        prev_field_name=None, next_field_name=None,
                                        current_field=None, current_field_name=None):
    '''
    Navbar links
    '''

    navbar_string = '<div class="navbar">\n'

    if prev_field is not None:
        navbar_string += f'    <a href="linker_bp_{prev_field}.html">{prev_field_name} (Previous)</a>\n'
    else:
        # If None, use current field
        navbar_string += f'    <a href="linker_bp_{current_field}.html">{current_field_name} (Previous)</a>\n'

    if next_field is not None:
        navbar_string += f'    <a href="linker_bp_{next_field}.html">{next_field_name} (Next)</a>\n'
    else:
        # If None, use current field
        navbar_string += f'    <a href="linker_bp_{current_field}.html">{current_field_name} (Next)</a>\n'

    link_locations = generate_webserver_track_link(flagging_sheet_link)

    for linkname in link_locations:

        navbar_string += f'    <a href="../{link_locations[linkname]}">{linkname}</a>\n'

    navbar_string += "</div>\n\n"

    return navbar_string


def make_sidebar_caltables(cal_plots, active_idx=0):
    '''
    Persistent side bar with all field names. For quick switching.
    '''

    sidebar_string = '<div class="sidebar">\n'

    if active_idx is None:
        sidebar_string += '    <a class="active" href="index.html">Home</a>\n'
    else:
        sidebar_string += '    <a class="" href="index.html">Home</a>\n'

    for i, cal_name in enumerate(cal_plots):

        # Set as active
        if i == active_idx:
            class_is = "active"
        else:
            class_is = ""

        sidebar_string += f'    <a class="{class_is}" href="linker_bp_{i}.html">{cal_name}</a>\n'

    sidebar_string += '</div>\n\n'

    return sidebar_string


def make_content_caltables_div(cal_plot):

    content_string = f'<div class="content" id="{cal_plot.rstrip(".html")[-1]}">\n'

    content_string += f'    <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="{cal_plot}" height="1000" width="100%"></iframe>\n'

    content_string += '</div>\n\n'

    return content_string
