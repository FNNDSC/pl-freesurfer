pl-freesurfer
=============

**FreeSurfer 8.2 over every subject of an input tree, as a ChRIS plugin.**

``pl-freesurfer`` is a `ChRIS <https://chrisproject.org/>`_ DS plugin that runs FreeSurfer's ``recon-all`` once per subject. The subjects are found in its input tree, the first positional argument, ``/incoming`` below, which usually holds one directory per subject: ``/incoming/sub-01``, ``/incoming/sub-02``. Each subject's reconstruction is saved in the output tree, the second positional argument, ``/outgoing``, in a directory of the same name, ``/outgoing/sub-01``, with a record of the run beside it. The first file of each subject, a DICOM of the series or a NIfTI volume, is the input. The common case needs no flags:

.. code-block:: bash

    freesurfer /incoming /outgoing

Any other FreeSurfer program runs the same way through ``--exec``, with the program's whole command line available. One instance runs its subjects one after another; to run many subjects at the same time, see `One subject at a time, or many at once`_.

pl-freesurfer has no engine of its own. It is `pl-shexec <https://github.com/FNNDSC/pl-shexec>`_, the plugin that runs a command template once per directory of a tree, built into an image that also holds FreeSurfer 8.2.0 and given ``recon-all`` as its default command. Walking the tree, choosing each subject's file, running the command and recording each run are pl-shexec's code; pl-freesurfer supplies the image, the default arguments and its manual.

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

A subject whose ``recon-all`` fails is recorded as failed and the run goes on to the next; the plugin exits 0 when at least one subject completed, 1 when every subject failed, 2 on a usage error.

Which directories are subjects
------------------------------

Usually the input tree's first level, one directory per subject. Precisely, a subject is any directory, at any depth, that holds at least one file passing ``--fileFilter``; a directory with no such file is passed over. A subject is named after its own directory, and its results go to the directory of the same path in the output tree:

.. code-block:: text

    /incoming/sub-01/t1.nii.gz              subject sub-01  ->  /outgoing/sub-01/sub-01/
    /incoming/sub-02/MPRAGE/*.dcm           subject MPRAGE  ->  /outgoing/sub-02/MPRAGE/MPRAGE/
    /incoming/sub-02/T2/*.dcm               subject T2      ->  /outgoing/sub-02/T2/T2/
    /incoming/notes.txt                     subject incoming ->  /outgoing/incoming/  (the input directory itself)

So a subject with two series directories is run twice, once per series, and a stray file at the top makes the input directory a subject of its own. ``--fileFilter 'glob:*.dcm'`` keeps only directories with DICOM files, ``--dirFilter`` keeps only directories whose path matches, and both together pick exactly the runs wanted.

One subject at a time, or many at once
--------------------------------------

A ``recon-all`` takes hours. How many run at the same time depends on how the plugin is run, and there are three ways.

**One plugin instance, in ChRIS or anywhere: one at a time.** The instance walks the input tree and runs its subjects in sequence, one ``recon-all`` finishing before the next starts, in the order of the walk. Twenty subjects take about twenty times as long as one. In ChRIS this is all an instance does: its container has 32Gi, one ``recon-all`` peaks near 16 GB in its SynthSeg step, two at once would be killed for lack of memory, and so ``--threads`` is not among the parameters ChRIS is given.

**Many instances in ChRIS, one per subject: all at once.** Parallelism in ChRIS is more plugin instances, not more work per instance. Each instance is given one subject with ``--dirFilter``, and ChRIS schedules the instances as separate 32Gi containers, on as many nodes as the cluster has room for. `pl-dymap <https://github.com/FNNDSC/pl-dymap>`_ creates them: run on the data node with ``--plugin pl-freesurfer``, it adds one pl-freesurfer instance per subject directory beneath that node, and running it again on the same node makes again only the subjects whose instance failed or was cancelled. On a ChRIS that offers them, a pipeline holding pl-dymap with these defaults is the one-click form, for example the ``FreeSurfer 8.2.0 per subject`` pipelines on BCH's CUBE.

.. code-block:: text

    data node ── pl-dymap ──┬── pl-freesurfer  --dirFilter sub-01   (container 1)
                            ├── pl-freesurfer  --dirFilter sub-02   (container 2)
                            └── pl-freesurfer  --dirFilter sub-03   (container 3)

**One process from a shell, with --threads N: up to N at once.** Outside ChRIS the plugin is a FreeSurfer batch runner, from a virtual environment on a machine with FreeSurfer 8.2 and a licence, as a Slurm job, or through Apptainer, which needs neither:

.. code-block:: bash

    apptainer exec docker://fnndsc/pl-freesurfer freesurfer --threads 8 /data/in /data/out

``--threads N`` keeps up to N ``recon-all`` running at once, each its own program, a new one starting as one ends. N is capped at the memory the process may use, the limit of its container or Slurm job or else the machine's available memory, divided by 16 GiB, and the plugin says on standard error when it lowers N: a Slurm job with ``--mem=40G`` asking for ``--threads 4`` runs two at a time. Each ``recon-all`` also uses as many cores as its ``-openmp`` option gives it, so ``--threads 4`` with ``-openmp 2`` wants eight cores.

The image
---------

``fnndsc/pl-freesurfer`` is the FreeSurfer 8.2.0 image with Python and this plugin installed. FreeSurfer's licence file is in the image under ``FS_LICENSE``, FNNDSC's own key, for research use within the terms FreeSurfer grants; a site running the plugin for another purpose supplies its own key by mounting a file over that path.

Running it
----------

From ChRIS, add the plugin to a pipeline after a plugin that leaves one directory per subject; the defaults do the rest. From the command line, with the image:

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
