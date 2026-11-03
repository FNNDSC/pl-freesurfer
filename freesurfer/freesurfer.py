"""The pl-freesurfer plugin: one FreeSurfer ``recon-all`` per scan of an input tree.

Given an input tree holding NIfTI or MGZ files and directories of DICOM files, the
plugin runs ``recon-all -all`` once per scan: each image file, and each directory's
``.dcm`` files as one series. It names the subject after the scan's directory, or
after the file's stem when the directory holds several scans, and places the subject's
FreeSurfer output in the matching directory of the output tree. Any other FreeSurfer program runs through
``--exec``, a template whose tags resolve to the current directory and file.

The engine that walks the tree, runs the command per file, records each job and sets
the exit status is pl-shexec's. This module holds what pl-freesurfer adds to it: the
plugin's name, version, title and resource limits for ChRIS, the default template, and
the text of its manual page, all in one ``PluginSpec`` that shexec's factory builds the
plugin from. FreeSurfer itself is in the image.

Key components:
    - FREESURFER_VERSION: the FreeSurfer release the image carries
    - RECON_ALL: the default ``--exec`` template
    - SCAN_FILTER: the default ``--fileFilter``, the names a scan can have
    - SPEC: the spec

Dependencies:
    - shexec.models
"""

from __future__ import annotations

from freesurfer import __version__
from freesurfer.models import PluginSpec

FREESURFER_VERSION: str = "8.2.0"

RECON_ALL: str = (
    "recon-all -all -i %{inputWorkingDir}/%{inputWorkingFile} -s %{volumeName} -sd %{outputWorkingDir}"
)

COMMAND: str = RECON_ALL

SCAN_FILTER: str = "glob:*.nii.gz,glob:*.nii,glob:*.mgz,glob:*.mgh,glob:*.dcm"

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
        scan of its input tree: each NIfTI or MGZ file, and each directory
        of DICOM files as one series. Each scan is a subject named after
        its directory, or after its file when the directory holds several
        scans, saved in the matching directory of the output tree. In ChRIS an instance
        runs its scans one after another in one 32Gi container, and a
        pl-dymap node starts one instance per directory to run them in
        parallel. From a shell, --threads N runs N directories at once,
        capped to the memory there is at 16 GiB a run. Any FreeSurfer
        program runs through --exec.
"""

DESCRIPTION: str = f"""
    DESCRIPTION

        ``freesurfer`` runs FreeSurfer {FREESURFER_VERSION} once per scan. The scans are found
        in its input tree, the <inputDir> positional argument, /incoming in
        the examples: every NIfTI or MGZ file, and every directory of DICOM
        files, which together are one series. Each scan's results are saved
        in the output tree, the <outputDir> positional argument, /outgoing,
        in the directory matching the scan's own, as a FreeSurfer subject
        named after the directory, or after the scan when the directory
        holds several:

            /incoming/sub-01/t1.nii.gz       subject sub-01  /outgoing/sub-01/sub-01/
            /incoming/sub-02/scan01.nii.gz   subject scan01  /outgoing/sub-02/scan01/
            /incoming/sub-02/scan02.nii.gz   subject scan02  /outgoing/sub-02/scan02/
            /incoming/sub-03/MPRAGE/*.dcm    subject MPRAGE  /outgoing/sub-03/MPRAGE/MPRAGE/

        A file is a scan when it passes ``--fileFilter``, by default a name ending
        .nii.gz, .nii, .mgz, .mgh or .dcm, so a .json sidecar or a text file
        beside the scans is passed over. ``--analyzeFileIndex`` v, the default,
        runs every scan: each file that passes on its own, except the .dcm
        files of a directory, which are one series and run once, from the
        first of them. The subject is named by %{{volumeName}}: the
        directory's name for a scan alone in it or a series, and for a file
        beside other scans its name less its extension.
        ``--fileFilter`` 'glob:*.dcm' runs only the series, ``--dirFilter`` only the
        directories whose path matches. The default command is

            {RECON_ALL_ON_PAGE}

        recon-all creates the subject directory, mri, surf, label, stats and
        scripts, inside the scan directory's counterpart in the output tree.
        Beside it, jobs.jsonl records, one line per scan, the command, its
        output, its exit status, the host and the timing. At ``--verbosity`` 2
        recon-all's output streams to the console.

        ``--exec`` replaces the command with any FreeSurfer program, as a template
        whose tags name the current directory, file and scan; ``--fileFilter``
        and ``--analyzeFileIndex`` choose which files the command gets.
        ``--analyzeFileIndex`` f gives the command only the first file of each
        directory, as 1.0 did, and a warning names every scan it leaves
        out. recon-all's own options, such as -openmp to use more cores for
        one subject, go in the template.

        One plugin instance runs its scans in sequence: one recon-all at a
        time, in the order of the walk, each starting when the one before it
        has ended. A scan that fails is recorded and the next one starts. A
        recon-all takes hours, so an instance given twenty scans takes about
        twenty times as long as an instance given one.

        In ChRIS that is all an instance does. Its container has 32Gi, one
        recon-all peaks near 16 GB in its SynthSeg step, and ``--threads`` is not
        among the parameters ChRIS is given, so an instance never runs two
        scans at once. Scans run at the same time in ChRIS only as separate
        plugin instances, each choosing its directory with ``--dirFilter``, which
        ChRIS schedules as separate containers on as many nodes as it has
        room for. pl-dymap creates those instances: run on the data node
        with ``--plugin`` pl-freesurfer, it adds one pl-freesurfer instance per
        directory under that node. The scans of one directory run in
        sequence within its instance.

        Run from a shell instead, from a virtual environment on a machine with
        FreeSurfer installed, as a Slurm job, or with apptainer exec on the
        image, ``--threads`` N runs up to N directories at once in the one
        process, each recon-all its own program; the scans of one directory
        run in sequence. The plugin caps N at the memory it may use, the
        limit of its container or Slurm job or else the machine's available
        memory, divided by 16 GiB, and says so on standard error when it
        lowers N. Each recon-all also uses as many cores as its -openmp
        option gives it, so N runs need N times that many.

        The plugin's own run is timed: one line of JSON on standard error.
        FreeSurfer's licence is in the image under FS_LICENSE, for research
        use. The exit status is 0 when every scan of at least one directory
        completed, 1 otherwise, 2 on a usage error.
"""

BRIEF_EXAMPLE: str = """
        freesurfer /incoming /outgoing
"""

EXAMPLES: str = """

    EXAMPLES

    One recon-all per scan, each NIfTI or MGZ file and each DICOM series,
    which is the default:

        freesurfer /incoming /outgoing

    The DICOM series only:

        freesurfer --fileFilter 'glob:*.dcm' /incoming /outgoing

    One directory only, as one of many instances run in parallel:

        freesurfer --dirFilter sub-01 /incoming /outgoing

    Pass recon-all's own options by giving the template with them in:

        freesurfer                                                              \\
            --exec "recon-all -all -openmp 4 -3T
                    -i %{inputWorkingDir}/%{inputWorkingFile}
                    -s %{volumeName} -sd %{outputWorkingDir}"                   \\
            /incoming /outgoing

    Run a different FreeSurfer program over every DICOM series:

        freesurfer --fileFilter 'glob:*.dcm'                                    \\
            --exec "mri_convert %{inputWorkingDir}/%{inputWorkingFile}
                    %{outputWorkingDir}/%{volumeName}.nii.gz"                   \\
            /incoming /outgoing

    Only the directories whose names match, and watch them run:

        freesurfer --dirFilter sub-01,sub-02 --verbosity 2 /incoming /outgoing

    Outside ChRIS, up to eight directories at once on a machine with the memory
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
    title=f"FreeSurfer {FREESURFER_VERSION} recon-all over every scan",
    category="Neuroimaging",
    minMemory="32Gi",
    minCpu="2000m",
    defaults={"exec": RECON_ALL, "analyzeFileIndex": "v", "fileFilter": SCAN_FILTER},
    chrisHidden=("threads", "threadsSplit"),
    jobMemory="16Gi",
    bannerArt=BANNER_ART,
    bannerTitle=BANNER_TITLE,
    bannerText=BANNER_TEXT,
    briefExample=BRIEF_EXAMPLE,
    description=DESCRIPTION,
    examples=EXAMPLES,
)
