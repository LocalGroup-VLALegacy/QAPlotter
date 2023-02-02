# QAPlotter
Make interactive figures for QA of VLA data

This package expects the name scheme and outputs created by the LGLBS
`pipeline <https://github.com/LocalGroup-VLALegacy/ReductionPipeline>`_). For an example of the additional
products needed for QAPlotter to work, see `this script <>`_.

Install this package a python 3.8 environment using::

    pip install -e .

from within the repo directory.


To use this with the LGLBS pipeline products, enter the "products" folder created
by the `hifv_exportdata` and do the following steps.

- Extract the `weblog.tgz` to a folder named "weblog". Note that by default the folder will be named from the
  pipeline run with a date and time. Apart from manually renaming, you can extract the tar file to a new folder with::

    cd products/
    mkdir weblog
    tar --strip-components=1 -C weblog -xf weblog.tgz

- Run the following in an python environment (or run from the cmd line or in a script)::

    (from cmd line) python -c "import qaplotter; qaplotter.make_all_plots()"

    (from python interpreter)
    import qaplotter
    qaplotter.make_all_plots()

Within the products folder, there should now be a new "index.html" file. This track homepage should
have the pipeline weblog embedded and additional links along the top for the interactive plots and quicklook
imaging.
