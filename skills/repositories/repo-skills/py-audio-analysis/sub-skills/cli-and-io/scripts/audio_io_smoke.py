#!/usr/bin/env python3
"""Smoke-test pyAudioAnalysis audioBasicIO with a generated WAV.

This script creates a tiny synthetic WAV, reads it through pyAudioAnalysis, and
reports optional media dependencies. It does not read repository data or run
maintainer tests.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Dict, List, Tuple


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def dependency_report() -> Dict[str, str]:
    modules = {
        "numpy": "numpy",
        "scipy": "scipy",
        "pydub": "pydub",
        "eyed3": "eyeD3",
    }
    report: Dict[str, str] = {}
    for import_name, dist_name in modules.items():
        if module_available(import_name):
            report[import_name] = "available (" + package_version(dist_name) + ")"
        else:
            report[import_name] = "missing"
    report["aifc"] = "available (stdlib)" if module_available("aifc") else "missing"
    for exe in ["ffmpeg", "avconv"]:
        report[exe] = "available" if shutil.which(exe) else "missing"
    return report


def locate_package() -> Path:
    spec = importlib.util.find_spec("pyAudioAnalysis")
    if spec is None or spec.origin is None:
        raise RuntimeError("pyAudioAnalysis is not importable in this Python environment")
    package_dir = Path(spec.origin).resolve().parent
    if str(package_dir) not in sys.path:
        # Needed by legacy modules that import package siblings by top-level name.
        sys.path.insert(0, str(package_dir))
    return package_dir


def synthesize_wav(path: Path, rate: int, duration: float, frequency: float, channels: int) -> Tuple[Tuple[int, ...], str]:
    import numpy as np
    from scipy.io import wavfile

    n_samples = max(1, int(rate * duration))
    t = np.arange(n_samples, dtype=np.float64) / float(rate)
    mono = (0.25 * np.sin(2.0 * math.pi * frequency * t) * 32767.0).astype(np.int16)
    if channels == 1:
        data = mono
    else:
        right = (0.5 * mono).astype(np.int16)
        data = np.column_stack([mono, right])
    wavfile.write(path, rate, data)
    return tuple(data.shape), str(data.dtype)


def run_wav_read(path: Path) -> Tuple[int, Tuple[int, ...], str, Tuple[int, ...], str]:
    from pyAudioAnalysis import audioBasicIO

    fs, signal = audioBasicIO.read_audio_file(str(path))
    mono = audioBasicIO.stereo_to_mono(signal)
    return (
        int(fs),
        tuple(getattr(signal, "shape", ())),
        str(getattr(signal, "dtype", "unknown")),
        tuple(getattr(mono, "shape", ())),
        str(getattr(mono, "dtype", "unknown")),
    )


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a tiny WAV, read it through pyAudioAnalysis.audioBasicIO, "
            "and report optional media dependencies."
        )
    )
    parser.add_argument("--rate", type=int, default=8000, help="Synthetic WAV sample rate (default: 8000).")
    parser.add_argument("--duration", type=float, default=0.25, help="Synthetic WAV duration in seconds (default: 0.25).")
    parser.add_argument("--frequency", type=float, default=440.0, help="Synthetic sine frequency in Hz (default: 440).")
    parser.add_argument("--channels", type=int, choices=[1, 2], default=1, help="Number of WAV channels to synthesize (default: 1).")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for the generated WAV. If omitted, a temporary directory is cleaned up.",
    )
    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="Keep the generated WAV when --output-dir is omitted by creating a persistent temp directory.",
    )
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="Print generated file paths. Off by default to avoid exposing local environment details.",
    )
    return parser.parse_args(argv)


def print_report(report: Dict[str, str]) -> None:
    print("== Dependency availability ==")
    for key in ["numpy", "scipy", "aifc", "pydub", "eyed3", "ffmpeg", "avconv"]:
        print(f"{key}: {report[key]}")


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.duration <= 0:
        raise SystemExit("--duration must be positive")
    if args.rate <= 0:
        raise SystemExit("--rate must be positive")

    report = dependency_report()
    print_report(report)

    try:
        locate_package()
        print("\npyAudioAnalysis import: available")
    except Exception as exc:
        print(f"\npyAudioAnalysis import: failed ({exc})")
        return 2

    missing_core = [name for name in ["numpy", "scipy", "aifc"] if report[name] == "missing"]
    if missing_core:
        print("Cannot synthesize/read the WAV because core import dependencies are missing: " + ", ".join(missing_core))
        if "aifc" in missing_core:
            print("audioBasicIO imports aifc at module import time; Python versions without aifc need a compatible runtime or validated shim.")
        return 2

    temp_context = None
    if args.output_dir is not None:
        workdir = args.output_dir
        workdir.mkdir(parents=True, exist_ok=True)
    elif args.keep_output:
        workdir = Path(tempfile.mkdtemp(prefix="paa-io-smoke-"))
    else:
        temp_context = tempfile.TemporaryDirectory(prefix="paa-io-smoke-")
        workdir = Path(temp_context.name)

    wav_path = workdir / "synthetic_smoke.wav"
    try:
        shape, dtype = synthesize_wav(wav_path, args.rate, args.duration, args.frequency, args.channels)
        print("\n== Generated WAV ==")
        print(f"samples_shape: {shape}")
        print(f"samples_dtype: {dtype}")
        if args.show_paths:
            print(f"wav_path: {wav_path}")

        try:
            fs, read_shape, read_dtype, mono_shape, mono_dtype = run_wav_read(wav_path)
        except Exception as exc:
            print("\npyAudioAnalysis audioBasicIO read: failed")
            print(f"error: {type(exc).__name__}: {exc}")
            if "No module named 'aifc'" in str(exc):
                print("audioBasicIO imports aifc at module import time; use a Python runtime that provides aifc or a validated compatibility shim.")
            if report.get("pydub") == "missing" or report.get("eyed3") == "missing":
                print("audioBasicIO imports pydub and eyed3 at module import time; install missing packages and retry.")
            return 3

        print("\n== pyAudioAnalysis audioBasicIO read ==")
        print(f"sampling_rate: {fs}")
        print(f"read_shape: {read_shape}")
        print(f"read_dtype: {read_dtype}")
        print(f"mono_shape: {mono_shape}")
        print(f"mono_dtype: {mono_dtype}")

        if fs != args.rate:
            print("status: fail (sample rate mismatch)")
            return 4
        if not read_shape:
            print("status: fail (empty signal)")
            return 4
        print("status: ok")
        if args.keep_output and args.output_dir is None:
            print("kept_output: true")
            if args.show_paths:
                print(f"output_dir: {workdir}")
        return 0
    finally:
        if temp_context is not None:
            temp_context.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
