#!/usr/bin/env python3
"""Check a DeepFilterNet Python installation without loading or downloading a model.

This helper is safe by default: it imports packages, inspects console entry
points, and optionally runs a tiny libdf STFT/ERB smoke test. It does not touch
network resources, model caches, training data, PipeWire, or Cargo builds.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - depends on caller env
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "module": getattr(module, "__name__", name)}


def cli_help_status(command: str, timeout: float) -> Dict[str, Any]:
    path = shutil.which(command)
    if path is None:
        # In venv/conda runs the executable can be a symlink; prefer the
        # active environment's bin/Scripts directory before resolving symlinks.
        candidates = [Path(sys.executable).parent / command, Path(sys.executable).resolve().parent / command]
        for sibling in candidates:
            if sibling.exists():
                path = str(sibling)
                break
    if path is None:
        return {"ok": False, "error": "not found on PATH or next to the active Python executable"}
    try:
        proc = subprocess.run(
            [path, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - depends on caller env
        return {"ok": False, "path": path, "error": f"{type(exc).__name__}: {exc}"}
    first_line = (proc.stdout or proc.stderr).splitlines()[:1]
    return {
        "ok": proc.returncode == 0,
        "path": path,
        "returncode": proc.returncode,
        "first_line": first_line[0] if first_line else "",
    }


def libdf_smoke(sr: int, fft: int, hop: int) -> Dict[str, Any]:
    try:
        import numpy as np
        from libdf import DF, erb, erb_norm, unit_norm
    except Exception as exc:  # pragma: no cover - depends on caller env
        return {"ok": False, "error": f"import failed: {type(exc).__name__}: {exc}"}

    try:
        state = DF(sr=sr, fft_size=fft, hop_size=hop, nb_bands=32)
        samples = max(sr // 10, hop * 4)
        audio = np.zeros((1, samples), dtype=np.float32)
        spec = state.analysis(audio)
        synth = state.synthesis(spec.copy())
        erb_feat = erb(spec, state.erb_widths())
        erb_norm_feat = erb_norm(erb_feat, 0.99)
        unit = unit_norm(spec, 0.99)
    except Exception as exc:  # pragma: no cover - depends on caller env
        return {"ok": False, "error": f"smoke failed: {type(exc).__name__}: {exc}"}

    return {
        "ok": True,
        "analysis_shape": list(spec.shape),
        "synthesis_shape": list(synth.shape),
        "erb_shape": list(erb_feat.shape),
        "erb_norm_shape": list(erb_norm_feat.shape),
        "unit_norm_shape": list(unit.shape),
        "state": {"sr": state.sr(), "fft_size": state.fft_size(), "hop_size": state.hop_size()},
    }


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check installed DeepFilterNet imports, CLI entry points, and optional libdf smoke behavior.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    parser.add_argument("--skip-cli", action="store_true", help="Do not run CLI --help probes.")
    parser.add_argument("--skip-libdf-smoke", action="store_true", help="Do not run the tiny libdf STFT smoke test.")
    parser.add_argument("--cli-timeout", type=float, default=15.0, help="Seconds for each CLI --help probe.")
    parser.add_argument("--sr", type=int, default=16000, help="Sample rate for the optional libdf smoke test.")
    parser.add_argument("--fft", type=int, default=320, help="FFT size for the optional libdf smoke test.")
    parser.add_argument("--hop", type=int, default=160, help="Hop size for the optional libdf smoke test.")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {
            "DeepFilterNet": dist_version("DeepFilterNet") or dist_version("deepfilternet"),
            "DeepFilterLib": dist_version("DeepFilterLib") or dist_version("deepfilterlib"),
            "DeepFilterDataLoader": dist_version("DeepFilterDataLoader") or dist_version("deepfilterdataloader"),
            "torch": dist_version("torch"),
            "torchaudio": dist_version("torchaudio"),
        },
        "imports": {name: import_status(name) for name in ["torch", "torchaudio", "df", "libdf"]},
        "optional_imports": {name: import_status(name) for name in ["libdfdata", "h5py", "onnx", "onnxruntime", "pystoi", "pesq"]},
    }
    if not args.skip_cli:
        report["cli"] = {cmd: cli_help_status(cmd, args.cli_timeout) for cmd in ["deepFilter", "deep-filter-py"]}
    if not args.skip_libdf_smoke:
        report["libdf_smoke"] = libdf_smoke(args.sr, args.fft, args.hop)

    required_ok = all(v.get("ok") for v in report["imports"].values())
    if not args.skip_cli:
        required_ok = required_ok and any(v.get("ok") for v in report.get("cli", {}).values())
    if not args.skip_libdf_smoke:
        required_ok = required_ok and bool(report.get("libdf_smoke", {}).get("ok"))
    report["ok"] = required_ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("DeepFilterNet install check:", "OK" if required_ok else "FAILED")
        for name, item in report["imports"].items():
            print(f"  import {name}: {'ok' if item.get('ok') else item.get('error')}")
        for name, version in report["distributions"].items():
            print(f"  dist {name}: {version or 'not installed'}")
        if "cli" in report:
            for cmd, item in report["cli"].items():
                print(f"  cli {cmd}: {'ok' if item.get('ok') else item.get('error', 'failed')}")
        if "libdf_smoke" in report:
            print("  libdf smoke:", "ok" if report["libdf_smoke"].get("ok") else report["libdf_smoke"].get("error"))
        missing_optional = [name for name, item in report["optional_imports"].items() if not item.get("ok")]
        if missing_optional:
            print("  optional imports missing:", ", ".join(missing_optional))
    return 0 if required_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
