"""The pl-freesurfer plugin: one FreeSurfer ``recon-all`` per subject directory of an input tree.

Given an input tree in which each directory is a subject holding a DICOM series or a
NIfTI volume, the plugin runs ``recon-all -all`` on the first file of each directory,
names the subject after the directory, and places the subject's FreeSurfer output in
the matching directory of the output tree. Any other FreeSurfer program runs through
``--exec``, a template whose tags resolve to the current directory and file.

The engine that walks the tree, runs the command per file, records each job and sets
the exit status is pl-shexec's. This module holds what pl-freesurfer adds to it: the
plugin's name, version, title and resource limits for ChRIS, the default template, and
the text of its manual page, all in one ``PluginSpec`` that shexec's factory builds the
plugin from. FreeSurfer itself is in the image.

Key components:
    - FREESURFER_VERSION: the FreeSurfer release the image carries
    - RECON_ALL: the default ``--exec`` template
    - SPEC: the spec

Dependencies:
    - shexec.models
"""

from __future__ import annotations

from freesurfer import __version__
from freesurfer.models import PluginSpec

FREESURFER_VERSION: str = "8.2.0"

RECON_ALL: str = (
    "recon-all -all"
    " -i %{inputWorkingDir}/%{inputWorkingFile}"
    " -s %{inputWorkingDir|basename}"
    " -sd %{outputWorkingDir}"
)

COMMAND: str = RECON_ALL

RECON_ALL_ON_PAGE: str = RECON_ALL.replace(" -s ", "\n                      -s ")

BANNER_ART: str = r"""
   __
  / _|_ __ ___  ___  ___ _   _ _ __ / _| ___ _ __
 | |_| '__/ _ \/ _ \/ __| | | | '__| |_ / _ \ '__|
 |  _| | |  __/  __/\__ \ |_| | |  |  _|  __/ |
 |_| |_|  \___|\___||___/\__,_|_|  |_|  \___|_|
"""

BANNER_TITLE: str = f"FreeSurfer {FREESURFER_VERSION} over an input tree"

BANNER_TEXT: str = f"""
                     FreeSurfer {FREESURFER_VERSION} over an input tree

                             -- version {{version}} --

        A ChRIS DS plugin that runs FreeSurfer's recon-all -all once per
        subject. The input tree usually holds one directory per subject,
        and each subject's results go to a directory of the same name in
        the output tree; the first file of each subject, a DICOM of the
        series or a NIfTI volume, is the input. In ChRIS an instance
        runs its subjects one after another in one 32Gi container, and a
        pl-dymap node starts one instance per subject to run them in
        parallel. From a shell, --threads N runs N subjects at once, capped
        to the memory there is at 16 GiB a subject. Any FreeSurfer program
        runs through --exec.
"""

DESCRIPTION: str = f"""
    DESCRIPTION

        ``freesurfer`` runs FreeSurfer {FREESURFER_VERSION} once per subject. The subjects are
        found in its input tree, the <inputDir> positional argument, /incoming
        in the examples, which usually holds one directory per subject:
        /incoming/sub-01, /incoming/sub-02. Each subject's results are saved
        in the output tree, the <outputDir> positional argument, /outgoing, in
        a directory of the same name: /outgoing/sub-01, /outgoing/sub-02.

        Precisely, a subject is any directory, at any depth, that holds at
        least one file passing ``--fileFilter``; a directory with no such file is
        passed over. A subject is named after its own directory, so
        /incoming/sub-01/MPRAGE/*.dcm is a subject called MPRAGE whose results
        go to /outgoing/sub-01/MPRAGE, and a subject with two series
        directories is run twice. A file lying directly in /incoming makes
        /incoming itself a subject. ``--fileFilter``, such as 'glob:*.dcm', and
        ``--dirFilter`` choose which directories run. The first file of each
        subject, a DICOM of the series or a NIfTI, MGZ or any volume
        mri_convert reads, is the input. The default command is

            {RECON_ALL_ON_PAGE}

        so recon-all names the subject after its directory and creates the
        subject directory, mri, surf, label, stats and scripts, inside the
        directory's counterpart in the output tree. Beside it, jobs.jsonl
        records the command, its output, its exit status, the host and the
        timing. At ``--verbosity`` 2 recon-all's output streams to the console.

        ``--exec`` replaces the command with any FreeSurfer program, as a template
        whose tags name the current directory and file; ``--fileFilter`` and
        ``--analyzeFileIndex`` choose which file in each directory the command
        gets. recon-all's own options, such as -openmp to use more cores for
        one subject, go in the template.

        One plugin instance runs its subjects in sequence: one recon-all at a
        time, in the order of the walk, each starting when the one before it
        has ended. A subject that fails is recorded and the next one starts. A
        recon-all takes hours, so an instance given twenty subjects takes
        about twenty times as long as an instance given one.

        In ChRIS that is all an instance does. Its container has 32Gi, one
        recon-all peaks near 16 GB in its SynthSeg step, and ``--threads`` is not
        among the parameters ChRIS is given, so an instance never runs two
        subjects at once. Subjects run at the same time in ChRIS only as
        separate plugin instances, one per subject, each choosing its subject
        with ``--dirFilter``, which ChRIS schedules as separate containers on as
        many nodes as it has room for. pl-dymap creates those instances: run
        on the data node with ``--plugin`` pl-freesurfer, it adds one
        pl-freesurfer instance per subject directory under that node.

        Run from a shell instead, from a virtual environment on a machine with
        FreeSurfer installed, as a Slurm job, or with apptainer exec on the
        image, ``--threads`` N runs up to N subjects at once in the one process,
        each recon-all its own program. The plugin caps N at the memory it may
        use, the limit of its container or Slurm job or else the machine's
        available memory, divided by 16 GiB, and says so on standard error
        when it lowers N. Each recon-all also uses as many cores as its
        -openmp option gives it, so N subjects need N times that many.

        The plugin's own run is timed: one line of JSON on standard error.
        FreeSurfer's licence is in the image under FS_LICENSE, for research
        use. The exit status is 0 when at least one subject completed, 1 when
        every subject failed, 2 on a usage error.
"""

BRIEF_EXAMPLE: str = """
        freesurfer /incoming /outgoing
"""

EXAMPLES: str = """

    EXAMPLES

    One recon-all per subject directory, the first file of each as the input,
    which is the default:

        freesurfer /incoming /outgoing

    The same, choosing the input by name:

        freesurfer --fileFilter 'glob:*.nii.gz' /incoming /outgoing

    One subject only, as one of many instances run in parallel:

        freesurfer --dirFilter sub-01 /incoming /outgoing

    Pass recon-all's own options by giving the template with them in:

        freesurfer                                                              \\
            --exec "recon-all -all -openmp 4 -3T
                    -i %{inputWorkingDir}/%{inputWorkingFile}
                    -s %{inputWorkingDir|basename} -sd %{outputWorkingDir}"     \\
            /incoming /outgoing

    Run a different FreeSurfer program over every DICOM series:

        freesurfer                                                              \\
            --analyzeFileIndex f --fileFilter dcm                               \\
            --exec "mri_convert %{inputWorkingDir}/%{inputWorkingFile}
                    %{outputWorkingDir}/%{inputWorkingDir|basename}.nii.gz"     \\
            /incoming /outgoing

    Only the subjects whose directory names match, and watch them run:

        freesurfer --dirFilter sub-01,sub-02 --verbosity 2 /incoming /outgoing

    Outside ChRIS, up to eight subjects at once on a machine with the memory
    and cores for them, here through Apptainer:

        apptainer exec docker://fnndsc/pl-freesurfer                            \\
            freesurfer --threads 8 /incoming /outgoing

    From the image, with the directories mounted:

        docker run --rm -v $PWD/in:/incoming:ro -v $PWD/out:/outgoing:rw        \\
            fnndsc/pl-freesurfer freesurfer /incoming /outgoing
"""

SPEC: PluginSpec = PluginSpec(
    name="freesurfer",
    version=f"{__version__} (FreeSurfer {FREESURFER_VERSION})",
    title=f"FreeSurfer {FREESURFER_VERSION} recon-all over every subject",
    category="Neuroimaging",
    minMemory="32Gi",
    minCpu="2000m",
    defaults={"exec": RECON_ALL, "analyzeFileIndex": "f", "fileFilter": ""},
    chrisHidden=("threads", "threadsSplit"),
    jobMemory="16Gi",
    bannerArt=BANNER_ART,
    bannerTitle=BANNER_TITLE,
    bannerText=BANNER_TEXT,
    briefExample=BRIEF_EXAMPLE,
    description=DESCRIPTION,
    examples=EXAMPLES,
)
