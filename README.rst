# QAPlotter
Make interactive figures for QA of VLA data

This package expects the name scheme and outputs created by the LGLBS
`pipeline <https://github.com/LocalGroup-VLALegacy/ReductionPipeline>`).

Install this package a python 3.8 environment using::

    pip install -e .

from within the repo directory.


To use this with the LGLBS pipeline products, enter the "products" folder created
by the `hifv_exportdata` and do the following steps.

1. Extract the `weblog.tgz` to a folder named "weblog". Note that by default the folder will be named from the pipeline run with a date and time.

2. Run the following in an python environment (or run from the cmd line or in a script):

    >> import qaplotter
    >>> qaplotter.make_all_plots()

Now open the "index.html" file to access the expanded weblog.
