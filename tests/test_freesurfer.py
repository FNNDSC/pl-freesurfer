"""The spec, the description for ChRIS, and a run through the default template with a stand-in recon-all."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

import pytest
from chris_plugin.parameters import serialize
from hostlib import JobSpec, job_run

from freesurfer import FREESURFER_VERSION, RECON_ALL, SPEC, __version__
from freesurfer.__main__ import main, parser


def tree_make(root: Path) -> tuple[Path, Path]:
    inputDir: Path = root / "incoming"
    outputDir: Path = root / "outgoing"
    for subject in ("sub-01", "sub-02"):
        (inputDir / subject).mkdir(parents=True)
        (inputDir / subject / "0001.dcm").write_bytes(b"not really dicom")
        (inputDir / subject / "notes.txt").write_text("x\n")
    outputDir.mkdir()
    return inputDir, outputDir


def reconAll_standIn(binDir: Path, exitStatus: int = 0) -> None:
    """A recon-all that records its arguments and creates the subject directory, as the real one would."""
    script: Path = binDir / "recon-all"
    script.write_text(
        "#!/bin/sh\n"
        'while [ $# -gt 0 ]; do case "$1" in -s) subject="$2"; shift;; -sd) sd="$2"; shift;; esac;'
        " shift; done\n"
        'mkdir -p "$sd/$subject/mri" && echo "done $subject"\n'
        f"exit {exitStatus}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)


def test_spec_namesFreeSurfer() -> None:
    assert (
        SPEC.name == "freesurfer" and FREESURFER_VERSION in SPEC.title and FREESURFER_VERSION in SPEC.version
    )
    assert SPEC.defaults["exec"] == RECON_ALL and SPEC.defaults["analyzeFileIndex"] == "f"
    assert "-i %{inputWorkingDir}/%{inputWorkingFile}" in RECON_ALL and "-sd %{outputWorkingDir}" in RECON_ALL


def test_defaults_runOneReconAllPerSubject(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    inputDir, outputDir = tree_make(tmp_path)
    binDir: Path = tmp_path / "bin"
    binDir.mkdir()
    reconAll_standIn(binDir)
    monkeypatch.setenv("PATH", f"{binDir}{os.pathsep}{os.environ['PATH']}")
    options: argparse.Namespace = parser.parse_args(["--verbosity", "0"])
    assert options.exec == RECON_ALL
    assert main(options, inputDir, outputDir) == 0
    for subject in ("sub-01", "sub-02"):
        assert (outputDir / subject / subject / "mri").is_dir()
        record = json.loads((outputDir / subject / "jobs.jsonl").read_text())
        assert record["returncode"] == 0 and record["argv"][0] == "recon-all"
        assert record["argv"][record["argv"].index("-i") + 1].endswith(f"{subject}/0001.dcm")
        assert record["argv"][record["argv"].index("-s") + 1] == subject
    span = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert span["name"] == "freesurfer" and span["status"] is True


def test_failingSubjects_failTheRun(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputDir, outputDir = tree_make(tmp_path)
    binDir: Path = tmp_path / "bin"
    binDir.mkdir()
    reconAll_standIn(binDir, exitStatus=1)
    monkeypatch.setenv("PATH", f"{binDir}{os.pathsep}{os.environ['PATH']}")
    assert main(parser.parse_args(["--verbosity", "0"]), inputDir, outputDir) == 1
    assert json.loads((outputDir / "sub-01" / "jobs.jsonl").read_text())["returncode"] == 1


def test_description_carriesTheDefaults_forChris() -> None:
    byName = {spec["name"]: spec for spec in serialize(parser)}
    assert byName["exec"]["default"] == RECON_ALL and byName["analyzeFileIndex"]["default"] == "f"


def test_manualAndVersion_areItsOwn(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(parser.parse_args(["--man"]), tmp_path, tmp_path) == 0
    out: str = capsys.readouterr().out
    assert "recon-all" in out and FREESURFER_VERSION in out and "TAGS" in out
    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])
    assert capsys.readouterr().out.strip() == f"freesurfer {__version__} (FreeSurfer {FREESURFER_VERSION})"


def test_chris_plugin_info_describesThePlugin() -> None:
    binDir: Path = Path(sys.executable).parent
    image: str = f"docker.io/fnndsc/pl-freesurfer:{__version__}"
    spec = JobSpec(
        argv=[str(binDir / "chris_plugin_info"), "--dock-image", image, "freesurfer"],
        env={"PATH": f"{binDir}{os.pathsep}{os.environ.get('PATH', '')}"},
    )
    result = job_run(spec)
    assert result.status, [*result.errors, result.stderr]
    description = json.loads(result.stdout)
    assert description["type"] == "ds" and description["selfexec"] == "freesurfer"
    assert description["version"] == __version__ and FREESURFER_VERSION in description["title"]
    assert description["documentation"] == "https://github.com/FNNDSC/pl-freesurfer"
    assert description["min_memory_limit"] == "32Gi"
