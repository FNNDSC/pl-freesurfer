"""The ``freesurfer`` command: the plugin, built by shexec's factory from this package's spec.

Key components:
    - PLUGIN: the built plugin
    - parser, main: its flags and the console script's target

Typical usage:
    freesurfer /incoming /outgoing
    freesurfer --man

Dependencies:
    - shexec.plugin, freesurfer.freesurfer
"""

from __future__ import annotations

import argparse
from collections.abc import Callable

from shexec.plugin import plugin_build

from freesurfer.freesurfer import SPEC
from freesurfer.models import Plugin

PLUGIN: Plugin = plugin_build(SPEC)
parser: argparse.ArgumentParser = PLUGIN.parser
main: Callable[..., int] = PLUGIN.main
