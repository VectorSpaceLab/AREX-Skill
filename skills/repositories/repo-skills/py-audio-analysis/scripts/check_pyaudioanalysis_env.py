#!/usr/bin/env python3
"""Check a pyAudioAnalysis installation for agent workflows.

This helper is self-contained runtime skill content. It verifies package imports,
core dependency imports, optional media tools, and the legacy CLI parser shape
without depending on a source checkout. It is safe by default: it does not run
analysis tasks, download data, or write outside a temporary directory.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
from importlib import metadata
from pathlib import Path
from typing import Any


def version_or_none(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def import_status(module: str) -> dict[str, Any]:
    try:
        importlib.import_module(module)
        return {"ok": True}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_feature_smoke() -> dict[str, Any]:
    try:
        import numpy as np
        from scipy.io import wavfile
        from pyAudioAnalysis import MidTermFeatures, ShortTermFeatures, audioBasicIO
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "stage": "import", "error": f"{type(exc).__name__}: {exc}"}

    try:
        fs = 8000
        duration = 0.5
        t = np.arange(int(fs * duration), dtype=float) / fs
        signal = (0.25 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
        short_window = int(round(0.05 * fs))
        short_step = int(round(0.05 * fs))
        short_features, short_names = ShortTermFeatures.feature_extraction(
            signal, fs, short_window, short_step
        )
        mid_features, short_from_mid, mid_names = MidTermFeatures.mid_feature_extraction(
            signal, fs, int(round(0.5 * fs)), int(round(0.5 * fs)), short_window, short_step
        )
        with tempfile.TemporaryDirectory(prefix="paa-env-check-") as tmp:
            wav_path = Path(tmp) / "tone.wav"
            wavfile.write(wav_path, fs, (signal * 32767).astype(np.int16))
            fs_read, read_signal = audioBasicIO.read_audio_file(str(wav_path))
        ok = (
            short_features.shape[0] == len(short_names)
            and mid_features.shape[0] == len(mid_names)
            and fs_read == fs
            and len(read_signal) == len(signal)
        )
        return {
            "ok": bool(ok),
            "short_shape": list(map(int, short_features.shape)),
            "short_name_count": len(short_names),
            "mid_shape": list(map(int, mid_features.shape)),
            "mid_name_count": len(mid_names),
            "short_from_mid_shape": list(map(int, short_from_mid.shape)),
            "wav_read_samples": int(len(read_signal)),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "stage": "feature_smoke", "error": f"{type(exc).__name__}: {exc}"}


def legacy_cli_help() -> dict[str, Any]:
    try:
        import pyAudioAnalysis
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    package_dir = Path(pyAudioAnalysis.__file__).resolve().parent
    script = package_dir / "audioAnalysis.py"
    if not script.exists():
        return {"ok": False, "error": "installed package has no audioAnalysis.py script"}

    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--help"],
            text=True,
            capture_output=True,
            timeout=20,
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    return {
        "ok": proc.returncode == 0 and "subcommands" in proc.stdout,
        "returncode": proc.returncode,
        "stdout_first_lines": proc.stdout.splitlines()[:8],
        "stderr_first_lines": proc.stderr.splitlines()[:8],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check pyAudioAnalysis import, dependencies, optional media tools, and safe feature smoke.")
    parser.add_argument("--skip-feature-smoke", action="store_true", help="Only check imports/tools; do not synthesize/read a WAV.")
    parser.add_argument("--skip-cli-help", action="store_true", help="Skip legacy audioAnalysis.py --help inspection.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    modules = [
        "pyAudioAnalysis",
        "pyAudioAnalysis.ShortTermFeatures",
        "pyAudioAnalysis.MidTermFeatures",
        "pyAudioAnalysis.audioBasicIO",
        "pyAudioAnalysis.audioTrainTest",
        "pyAudioAnalysis.audioSegmentation",
        "pyAudioAnalysis.audioVisualization",
    ]
    dependencies = [
        "numpy",
        "scipy",
        "sklearn",
        "hmmlearn",
        "matplotlib",
        "pandas",
        "plotly",
        "pydub",
        "eyed3",
        "imblearn",
    ]
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distribution_version": version_or_none("pyAudioAnalysis"),
        "imports": {module: import_status(module) for module in modules},
        "dependencies": {module: import_status(module) for module in dependencies},
        "dependency_versions": {
            "numpy": version_or_none("numpy"),
            "scipy": version_or_none("scipy"),
            "scikit-learn": version_or_none("scikit-learn"),
            "hmmlearn": version_or_none("hmmlearn"),
            "matplotlib": version_or_none("matplotlib"),
            "pandas": version_or_none("pandas"),
            "plotly": version_or_none("plotly"),
            "pydub": version_or_none("pydub"),
            "eyeD3": version_or_none("eyeD3"),
            "imbalanced-learn": version_or_none("imbalanced-learn"),
        },
        "optional_media_tools": {
            "ffmpeg": bool(shutil.which("ffmpeg")),
            "avconv": bool(shutil.which("avconv")),
        },
        "feature_smoke": None if args.skip_feature_smoke else run_feature_smoke(),
        "legacy_cli_help": None if args.skip_cli_help else legacy_cli_help(),
    }

    all_imports_ok = all(v["ok"] for v in report["imports"].values())
    all_deps_ok = all(v["ok"] for v in report["dependencies"].values())
    feature_ok = True if args.skip_feature_smoke else bool(report["feature_smoke"] and report["feature_smoke"].get("ok"))
    cli_ok = True if args.skip_cli_help else bool(report["legacy_cli_help"] and report["legacy_cli_help"].get("ok"))
    report["ok"] = all_imports_ok and all_deps_ok and feature_ok and cli_ok

    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
