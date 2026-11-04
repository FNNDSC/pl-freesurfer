pl-freesurfer
=============

**FreeSurfer 8.2 over every scan of an input tree, as a ChRIS plugin.**

``pl-freesurfer`` is a `ChRIS <https://chrisproject.org/>`_ DS plugin that runs FreeSurfer's ``recon-all`` once per scan. The scans are found in its input tree, the first positional argument, ``/incoming`` below: every NIfTI or MGZ file, and every directory of DICOM files as one series. Each scan's reconstruction is saved in the output tree, the second positional argument, ``/outgoing``, in the directory matching the scan's own, as a FreeSurfer subject named after the directory, or after the scan when the directory holds several, with a record of the run beside it: ``/incoming/sub-01/t1.nii.gz`` gives ``/outgoing/sub-01/sub-01``, and ``scan01.nii.gz`` beside ``scan02.nii.gz`` gives a subject ``scan01``. The common case needs no flags:

.. code-block:: bash

    freesurfer /incoming /outgoing

Any other FreeSurfer program runs the same way through ``--exec``, with the program's whole command line available. One instance runs its scans one after another; to run many at the same time, see `One scan at a time, or many at once`_.

pl-freesurfer has no engine of its own. It is `pl-shexec <https://github.com/FNNDSC/pl-shexec>`_, the plugin that runs a command template once per directory of a tree, built into an image that also holds FreeSurfer 8.2.0 and given ``recon-all`` as its default command. Walking the tree, choosing the scans, running the command and recording each run are pl-shexec's code; pl-freesurfer supplies the image, the default arguments and its manual.

What it runs
------------

The default command is a template that pl-shexec resolves once per scan:

.. code-block:: text

    recon-all -all -i %{inputWorkingDir}/%{inputWorkingFile} -s %{volumeName} -sd %{outputWorkingDir}

``%{inputWorkingDir}`` is the scan's directory in the input tree, ``%{inputWorkingFile}`` the scan's file, ``%{outputWorkingDir}`` the matching directory in the output tree, and ``%{volumeName}`` the scan's name: the directory's name for a scan alone in it or a DICOM series, as one subject per directory always was, and for a file beside other scans its name less its extension, ``scan01.nii.gz`` as ``scan01``. A name therefore depends on its neighbours: a second scan added beside ``t1.nii.gz`` renames it ``t1`` on the next run. ``--analyzeFileIndex v`` runs each scan once: every file passing ``--fileFilter`` on its own, except the ``.dcm`` files of a directory, which are one series, started from the first of them, since ``recon-all`` reads the series from one of its files. ``--fileFilter`` defaults to ``glob:*.nii.gz,glob:*.nii,glob:*.mgz,glob:*.mgh,glob:*.dcm``, so a ``.json`` sidecar or a text file beside the scans is never handed to ``recon-all``; ``--fileFilter 'glob:*.dcm'`` runs only the DICOM series.

To give ``recon-all`` its own options, pass the template with them in:

.. code-block:: bash

    freesurfer --exec "recon-all -all -openmp 4 -3T
                       -i %{inputWorkingDir}/%{inputWorkingFile}
                       -s %{volumeName} -sd %{outputWorkingDir}" /incoming /outgoing

To run a different program, say ``mri_convert`` over every DICOM series:

.. code-block:: bash

    freesurfer --fileFilter 'glob:*.dcm' \
        --exec "mri_convert %{inputWorkingDir}/%{inputWorkingFile} %{outputWorkingDir}/%{volumeName}.nii.gz" \
        /incoming /outgoing

``freesurfer --man`` lists every tag and function.

What each run leaves behind
---------------------------

For a directory ``sub-02`` holding ``scan01.nii.gz`` and ``scan02.nii.gz``, the output tree gets:

.. code-block:: text

    sub-02/
    ├── scan01/            recon-all's subject directory: mri, surf, label, stats, scripts
    ├── scan02/
    └── jobs.jsonl         one line per scan: the command, its output, its exit status, the host, the timing

``pflog read /outgoing/*/jobs.jsonl`` prints the runs as a table, ``--failed`` keeps the ones that went wrong, and a log collector indexes the lines. ``--jobFiles`` also writes the command, stdout, stderr and return code as four files beside the subject directory, for reading in an editor; ``--noJobLogging`` keeps no record. The plugin's own run is one line of JSON on standard error, which CUBE keeps with the plugin instance.

A scan whose ``recon-all`` fails is recorded as failed and the run goes on to the next; the plugin exits 0 when every scan of at least one directory completed, 1 otherwise, 2 on a usage error.

Which files are scans
---------------------

A scan is a file passing ``--fileFilter``, at any depth, or the ``.dcm`` files of one directory together. Each is named by ``%{volumeName}``, and its results go to the directory of the same path in the output tree:

.. code-block:: text

    /incoming/sub-01/t1.nii.gz              subject sub-01  ->  /outgoing/sub-01/sub-01/
    /incoming/sub-01/t1.json                not a scan: passed over
    /incoming/sub-02/scan01.nii.gz          subject scan01  ->  /outgoing/sub-02/scan01/
    /incoming/sub-02/scan02.nii.gz          subject scan02  ->  /outgoing/sub-02/scan02/
    /incoming/sub-03/MPRAGE/*.dcm           subject MPRAGE  ->  /outgoing/sub-03/MPRAGE/MPRAGE/

A directory holding a series and a NIfTI file is two scans. The series is named after its directory and the NIfTI file after itself, so when the file is named after the directory, ``MPRAGE/MPRAGE.nii`` beside ``MPRAGE/*.dcm``, both name the subject ``MPRAGE`` and the second ``recon-all`` stops on finding it: rename one, or run with a ``--fileFilter`` naming one kind. ``--dirFilter`` keeps only directories whose path matches. ``--analyzeFileIndex f`` gives ``recon-all`` only the first file of each directory, as 1.0 did, and a warning names every scan it leaves out.

One scan at a time, or many at once
-----------------------------------

A ``recon-all`` takes hours. How many run at the same time depends on how the plugin is run, and there are three ways.

**One plugin instance, in ChRIS or anywhere: one at a time.** The instance walks the input tree and runs its scans in sequence, one ``recon-all`` finishing before the next starts, in the order of the walk. Twenty scans take about twenty times as long as one. In ChRIS this is all an instance does: its container has 32Gi, one ``recon-all`` peaks near 16 GB in its SynthSeg step, two at once would be killed for lack of memory, and so ``--threads`` is not among the parameters ChRIS is given.

**Many instances in ChRIS, one per directory: all at once.** Parallelism in ChRIS is more plugin instances, not more work per instance. Each instance is given one directory with ``--dirFilter``, and ChRIS schedules the instances as separate 32Gi containers, on as many nodes as the cluster has room for. `pl-dymap <https://github.com/FNNDSC/pl-dymap>`_ creates them: run on the data node with ``--plugin pl-freesurfer``, it adds one pl-freesurfer instance per directory beneath that node, and running it again on the same node makes again only the directories whose instance failed or was cancelled. The scans of one directory run in sequence within its instance, so a folder of three scans is one branch running three ``recon-all`` in turn. On a ChRIS that offers them, a pipeline holding pl-dymap with these defaults is the one-click form, for example the ``FreeSurfer 8.2.0 per subject`` pipelines on BCH's CUBE.

.. code-block:: text

    data node ── pl-dymap ──┬── pl-freesurfer  --dirFilter sub-01   (container 1)
                            ├── pl-freesurfer  --dirFilter sub-02   (container 2)
                            └── pl-freesurfer  --dirFilter sub-03   (container 3)

**One process from a shell, with --threads N: up to N at once.** Outside ChRIS the plugin is a FreeSurfer batch runner, from a virtual environment on a machine with FreeSurfer 8.2 and a licence, as a Slurm job, or through Apptainer, which needs neither:

.. code-block:: bash

    apptainer exec docker://fnndsc/pl-freesurfer freesurfer --threads 8 /data/in /data/out

``--threads N`` runs up to N directories at once, each ``recon-all`` its own program, a new directory starting as one ends; the scans of one directory run in sequence. N is capped at the memory the process may use, the limit of its container or Slurm job or else the machine's available memory, divided by 16 GiB, and the plugin says on standard error when it lowers N: a Slurm job with ``--mem=40G`` asking for ``--threads 4`` runs two at a time. Each ``recon-all`` also uses as many cores as its ``-openmp`` option gives it, so ``--threads 4`` with ``-openmp 2`` wants eight cores.

From the PACS to results, as one script
---------------------------------------

The ChRIS form above, from a patient on the PACS to one result per series, is five lines in `chell <https://github.com/FNNDSC/mise>`_, the ChRIS shell. ``examples/t1_mgz.mise`` is that script: it queries the patient's MR studies, keeps the T1 series, pulls them into a new feed, runs the per-series pipeline on the feed's root and waits for the feed to finish. Played as

.. code-block:: bash

    play examples/t1_mgz.mise --param MRN=<mrn>

it answers with the feed. The pipeline it names runs ``mri_convert`` rather than ``recon-all``, so the whole play takes about a minute and a half; a ``recon-all`` pipeline is the same script with another ``PIPELINE``.

The image
---------

``fnndsc/pl-freesurfer`` is the FreeSurfer 8.2.0 image with Python and this plugin installed. FreeSurfer's licence file is in the image under ``FS_LICENSE``, FNNDSC's own key, for research use within the terms FreeSurfer grants; a site running the plugin for another purpose supplies its own key by mounting a file over that path.

Running it
----------

From ChRIS, add the plugin to a pipeline after a plugin that leaves scans, NIfTI files or DICOM series; the defaults do the rest. From the command line, with the image:

.. code-block:: bash

    docker run --rm -v $PWD/in:/incoming:ro -v $PWD/out:/outgoing:rw fnndsc/pl-freesurfer \
        freesurfer /incoming /outgoing

    docker run --rm fnndsc/pl-freesurfer freesurfer --man

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
