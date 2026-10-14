"""What pl-freesurfer says about itself: the spec shexec's factory builds the plugin from.

Everything this plugin changes from pl-shexec is here: its name and version, its
description for ChRIS, the defaults of its flags, and its words on the manual page.
FreeSurfer is in the image; the engine, the flags, the records and the exit status
are shexec's.

Key components:
    - FREESURFER_VERSION: the FreeSurfer the image carries
    - RECON_ALL: the default ``--exec`` template, one ``recon-all`` per subject directory
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

        ``freesurfer`` is pl-shexec with FreeSurfer {FREESURFER_VERSION} in the image.
        The input tree is walked; in each directory the files are selected by
        the filters and --analyzeFileIndex, and the --exec template is run once
        per selected file with its tags resolved against that directory and
        file, without a shell. The defaults make the common case need no
        flags: --analyzeFileIndex f selects the first file of each directory,
        and --exec is

            {RECON_ALL}

        so each directory is one subject, named after the directory, whose
        first file is the input volume. recon-all reads a DICOM file as the
        first file of its series, or a NIfTI, MGZ or any format mri_convert
        reads. The subject's directory, mri, surf, label, stats and scripts,
        is created inside the directory's counterpart in the output tree, and
        beside it jobs.jsonl records the command, its output, its exit status,
        the host and the timing. At --verbosity 2 recon-all's output streams
        to the console as it runs.

        The plugin's own run is timed: one line of JSON on standard error.

        FreeSurfer's licence is in the image under FS_LICENSE, for research
        use. The exit status is 0 when at least one subject completed, 1
        when every subject failed, 2 on a usage error.
"""

BRIEF_EXAMPLE: str = """
        freesurfer /incoming /outgoing
"""

EXAMPLES: str = """

    EXAMPLES

    One recon-all per subject directory, the first file of each as the input,
    which is the default:

        freesurfer /incoming /outgoing

    The same, choosing the input by name and running four subjects at once:

        freesurfer --fileFilter 'glob:*.nii.gz' --threads 4 /incoming /outgoing

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
    minMemory="8Gi",
    minCpu="2000m",
    defaults={"exec": RECON_ALL, "analyzeFileIndex": "f", "fileFilter": ""},
    bannerArt=BANNER_ART,
    bannerTitle=BANNER_TITLE,
    bannerText=BANNER_TEXT,
    briefExample=BRIEF_EXAMPLE,
    description=DESCRIPTION,
    examples=EXAMPLES,
)
