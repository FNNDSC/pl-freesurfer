"""The records freesurfer works with: shexec's, and through them every layer below.

Key components:
    - PluginSpec, Plugin: shexec's factory types, re-exported
    - FileJob, JobResult, JobSpec, RunResult, StageResult, DirNode, HostFacts, Span: re-exported

Dependencies:
    - shexec.models
"""

from __future__ import annotations

from shexec.models import (
    DirNode,
    FileJob,
    HostFacts,
    JobResult,
    JobSpec,
    Plugin,
    PluginSpec,
    RunResult,
    ShExecOptions,
    Span,
    StageResult,
)

__all__: list[str] = [
    "DirNode",
    "FileJob",
    "HostFacts",
    "JobResult",
    "JobSpec",
    "Plugin",
    "PluginSpec",
    "RunResult",
    "ShExecOptions",
    "Span",
    "StageResult",
]
