"""pl-freesurfer: a ChRIS DS plugin that runs FreeSurfer once per scan of its input tree.

Built on pl-shexec: this package contributes a spec, the FreeSurfer image and nothing else.

Key components:
    - SPEC, RECON_ALL, SCAN_FILTER, FREESURFER_VERSION: what the plugin says about itself
    - the records of shexec and everything below, re-exported through freesurfer.models

Dependencies:
    - chris_plugin, shexec
"""

from __future__ import annotations

__version__: str = "1.1.0"

from freesurfer.freesurfer import COMMAND, FREESURFER_VERSION, RECON_ALL, SCAN_FILTER, SPEC
from freesurfer.models import FileJob, JobResult, Plugin, PluginSpec, RunResult, Span

__all__: list[str] = [
    "COMMAND",
    "FREESURFER_VERSION",
    "RECON_ALL",
    "SCAN_FILTER",
    "SPEC",
    "FileJob",
    "JobResult",
    "Plugin",
    "PluginSpec",
    "RunResult",
    "Span",
    "__version__",
]
