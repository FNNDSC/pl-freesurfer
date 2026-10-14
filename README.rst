pl-freesurfer
=============

**FreeSurfer 8.2 over every subject of an input tree, as a ChRIS plugin.**

``pl-freesurfer`` is a `ChRIS <https://chrisproject.org/>`_ DS plugin that runs FreeSurfer's ``recon-all`` once per directory of its input tree. Each directory is a subject; the first file in it, a DICOM of the series or a NIfTI volume, is the input; the subject's reconstruction lands in the matching directory of the output tree, with a record of the run beside it. The common case needs no flags:

.. code-block:: bash

    freesurfer /incoming /outgoing

Any other FreeSurfer program runs the same way through ``--exec``, with the program's whole command line available. The plugin is `pl-shexec <https://github.com/FNNDSC/pl-shexec>`_ with FreeSurfer 8.2.0 in the image and ``recon-all`` as the default command; it carries no engine code of its own.

What it runs
------------

The default command is a template that pl-shexec resolves once per subject:

.. code-block:: text

    recon-all -all -i %{inputWorkingDir}/%{inputWorkingFile} -s %{inputWorkingDir|basename} -sd %{outputWorkingDir}

``%{inputWorkingDir}`` is the subject's directory in the input tree, ``%{inputWorkingFile}`` the file chosen in it, ``%{outputWorkingDir}`` the matching directory in the output tree. The subject is named after its directory, so an input tree of ``sub-01/``, ``sub-02/`` gives subjects ``sub-01`` and ``sub-02``. ``--analyzeFileIndex f`` picks the first file of each directory, which for a DICOM series is any file of the series, since ``recon-all`` reads the series from one of its files; ``--fileFilter`` narrows the choice by name, ``--fileFilter 'glob:*.nii.gz'`` for NIfTI inputs in a mixed directory.

To give ``recon-all`` its own options, pass the template with them in:

.. code-block:: bash

    freesurfer --exec "recon-all -all -openmp 4 -3T
                       -i %{inputWorkingDir}/%{inputWorkingFile}
                       -s %{inputWorkingDir|basename} -sd %{outputWorkingDir}" /incoming /outgoing

To run a different program, say ``mri_convert`` over every DICOM series:

.. code-block:: bash

    freesurfer --fileFilter dcm \
        --exec "mri_convert %{inputWorkingDir}/%{inputWorkingFile} %{outputWorkingDir}/%{inputWorkingDir|basename}.nii.gz" \
        /incoming /outgoing

``freesurfer --man`` lists every tag and function.

What each run leaves behind
---------------------------

For a subject directory ``sub-01`` in the input tree, the output tree gets:

.. code-block:: text

    sub-01/
    ├── sub-01/            recon-all's subject directory: mri, surf, label, stats, scripts
    └── jobs.jsonl         one line: the command, its output, its exit status, the host, the timing

``pflog read /outgoing/*/jobs.jsonl`` prints the subjects as a table, ``--failed`` keeps the ones that went wrong, and a log collector indexes the lines. ``--jobFiles`` also writes the command, stdout, stderr and return code as four files beside the subject directory, for reading in an editor; ``--noJobLogging`` keeps no record. The plugin's own run is one line of JSON on standard error, which CUBE keeps with the plugin instance.

Subjects run one after another, never several at once in one container: FreeSurfer 8's ``recon-all`` peaks near 16 GB, so the plugin asks ChRIS for 32Gi and runs one subject at a time within it. Many subjects are processed in parallel by running one plugin instance per subject, each with ``--dirFilter`` naming its subject, which ChRIS schedules as separate containers. ``recon-all`` itself takes ``-openmp`` through the template, to give one subject more cores. A subject whose ``recon-all`` fails is recorded as failed and the run goes on to the next; the plugin exits 0 when at least one subject completed, 1 when every subject failed, 2 on a usage error.

The image
---------

``fnndsc/pl-freesurfer`` is the FreeSurfer 8.2.0 image with Python and this plugin installed. FreeSurfer's licence file is in the image under ``FS_LICENSE``, FNNDSC's own key, for research use within the terms FreeSurfer grants; a site running the plugin for another purpose supplies its own key by mounting a file over that path.

Running it
----------

From ChRIS, add the plugin to a pipeline after a plugin that leaves one directory per subject; the defaults do the rest. From the command line, with the image:

.. code-block:: bash

    docker run --rm -v $PWD/in:/incoming:ro -v $PWD/out:/outgoing:rw fnndsc/pl-freesurfer \
        freesurfer /incoming /outgoing

    docker run --rm fnndsc/pl-freesurfer freesurfer --man /tmp /tmp

Built on pl-shexec
------------------

This plugin is pl-shexec's ``plugin_build`` called with a spec: the name, the version, the title and resource limits ChRIS sees, the default template, and the manual's words. The filters, the tags, the records and the exit status are pl-shexec's and are documented there; a fix to them reaches this plugin on its next build. The plugin's own version is independent of FreeSurfer's: ``freesurfer --version`` prints both, the title names the FreeSurfer version, and ``docs/history.adoc`` records which FreeSurfer each plugin version carried.

Development
-----------

.. code-block:: bash

    uv venv --python /usr/bin/python3.14 .venv
    uv pip install --python .venv/bin/python -e ".[dev]"
    .venv/bin/ruff check . && .venv/bin/pytest -q

The tests run the plugin in-process with a stand-in ``recon-all`` on ``PATH``, so they need no FreeSurfer. The CI workflow lints and tests on Python 3.11 to 3.14, frees the runner's disk, builds the image on every push to ``main``, pushes it to Docker Hub and ghcr.io, and on a ``v*`` tag uploads the plugin's description to cube.chrisproject.org. The tag must match ``__version__`` in ``freesurfer/__init__.py``.

``docs/purpose.adoc`` says why the plugin exists, ``docs/architecture.adoc`` how it is built, ``docs/history.adoc`` where it came from.
