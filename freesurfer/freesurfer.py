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

        A ChRIS DS plugin that runs FreeSurfer once per directory of its
        input tree. By default each directory is a subject and the first
        file in it, a DICOM of the series or a NIfTI volume, is the input to
        recon-all -all; the subject's output lands in the matching directory
        of the output tree. Any FreeSurfer program runs through --exec.
"""

DESCRIPTION: str = f"""
    DESCRIPTION

        ``freesurfer`` runs FreeSurfer {FREESURFER_VERSION} once per directory of
        its input tree. Each directory is a subject; its first file, a DICOM
        of the series or a NIfTI, MGZ or any volume mri_convert reads, is the
        input; and the subject's output lands in the matching directory of the
        output tree. The default command is

            {RECON_ALL_ON_PAGE}

        so recon-all names the subject after its directory and creates the
        subject directory, mri, surf, label, stats and scripts, inside the
        directory's counterpart in the output tree. Beside it, jobs.jsonl
        records the command, its output, its exit status, the host and the
        timing. At --verbosity 2 recon-all's output streams to the console.

        --exec replaces the command with any FreeSurfer program, as a template
        whose tags name the current directory and file; --fileFilter and
        --analyzeFileIndex choose which file in each directory the command
        gets. recon-all's own options, such as -openmp to use more cores for
        one subject, go in the template.

        Subjects run one after another. The plugin does not run subjects in
        parallel within one container: FreeSurfer 8's recon-all peaks near
        16 GB in its SynthSeg step, so two at once would exhaust the
        container's memory. To process subjects in parallel, run one plugin
        instance per subject, each choosing its subject with --dirFilter.

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
    omit=("threads", "threadsSplit"),
    bannerArt=BANNER_ART,
    bannerTitle=BANNER_TITLE,
    bannerText=BANNER_TEXT,
    briefExample=BRIEF_EXAMPLE,
    description=DESCRIPTION,
    examples=EXAMPLES,
)
