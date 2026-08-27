#!/usr/bin/env python3
"""Probe PyOD optional modality backends without downloads or training."""
from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.util
import io
import json
import os
import platform
import sys
from importlib import metadata
from typing import Any, Dict, List


EXTRAS: Dict[str, Dict[str, Any]] = {
    "torch": {
        "modules": ["torch"],
        "pyod_modules": [
            "pyod.models.auto_encoder",
            "pyod.models.vae",
            "pyod.models.ts_lstm",
            "pyod.models.ts_anomaly_transformer",
        ],
        "hint": "pip install 'pyod[torch]'",
        "enables": "torch-backed neural/tabular detectors, LSTMAD, AnomalyTransformer, AudioAE inner autoencoder, and LUNAR-based EmbeddingOD",
    },
    "graph": {
        "modules": ["torch", "torch_geometric"],
        "pyod_modules": ["pyod.models.pyg_dominant", "pyod.models.pyg_scan"],
        "hint": "pip install 'pyod[graph]'",
        "enables": "PyTorch Geometric graph detectors",
    },
    "embedding": {
        "modules": ["sentence_transformers"],
        "pyod_modules": ["pyod.models.embedding"],
        "hint": "pip install 'pyod[embedding]'",
        "enables": "SentenceTransformer text encoders for EmbeddingOD",
    },
    "openai": {
        "modules": ["openai"],
        "pyod_modules": ["pyod.utils.encoders.openai_encoder"],
        "credentials": ["OPENAI_API_KEY"],
        "hint": "pip install 'pyod[openai]' and set OPENAI_API_KEY for real API calls",
        "enables": "OpenAI embedding encoders such as text-embedding-3-small/large",
    },
    "huggingface": {
        "modules": ["transformers", "torch", "PIL"],
        "pyod_modules": ["pyod.utils.encoders.huggingface"],
        "credentials": ["HF_TOKEN", "HUGGINGFACE_HUB_TOKEN"],
        "hint": "pip install 'pyod[huggingface]'",
        "enables": "HuggingFace text/image encoders, DINOv2, CLIP, and local HF model paths",
    },
    "audio": {
        "modules": ["librosa", "soundfile"],
        "pyod_modules": ["pyod.utils.encoders.audio", "pyod.models.audio_ae"],
        "hint": "pip install 'pyod[audio]' (AudioAE also needs 'pyod[torch,audio]')",
        "enables": "audio-mfcc encoder, EmbeddingOD.for_audio, and audio file/waveform feature extraction",
    },
}


DIST_NAMES = {
    "PIL": "Pillow",
    "torch_geometric": "torch-geometric",
    "sentence_transformers": "sentence-transformers",
}


def module_spec_status(module_name: str) -> Dict[str, Any]:
    spec = importlib.util.find_spec(module_name)
    status: Dict[str, Any] = {"module": module_name, "available": spec is not None}
    dist_name = DIST_NAMES.get(module_name, module_name)
    try:
        status["version"] = metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        status["version"] = None
    return status


def pyod_import_status(module_name: str) -> Dict[str, Any]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        # Some optional PyOD modules print install hints during failed imports.
        # Capture that noise so JSON output stays machine-parseable.
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            importlib.import_module(module_name)
        return {
            "module": module_name,
            "importable": True,
            "error": None,
            "stdout": stdout.getvalue().strip(),
            "stderr": stderr.getvalue().strip(),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostic script should capture all import failures
        return {
            "module": module_name,
            "importable": False,
            "error": f"{exc.__class__.__name__}: {exc}",
            "stdout": stdout.getvalue().strip(),
            "stderr": stderr.getvalue().strip(),
        }


def torch_runtime_status() -> Dict[str, Any]:
    if importlib.util.find_spec("torch") is None:
        return {"importable": False}
    try:
        import torch  # type: ignore

        status: Dict[str, Any] = {
            "importable": True,
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
        }
        if status["cuda_available"]:
            status["cuda_device_count"] = int(torch.cuda.device_count())
            status["cuda_device_names"] = [
                torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
            ]
        if hasattr(torch.backends, "mps"):
            status["mps_available"] = bool(torch.backends.mps.is_available())
        return status
    except Exception as exc:  # noqa: BLE001
        return {"importable": False, "error": f"{exc.__class__.__name__}: {exc}"}


def pyod_status() -> Dict[str, Any]:
    status: Dict[str, Any] = {"importable": False, "version": None}
    try:
        import pyod  # type: ignore

        status["importable"] = True
        status["version"] = getattr(pyod, "__version__", None)
    except Exception as exc:  # noqa: BLE001
        status["error"] = f"{exc.__class__.__name__}: {exc}"
    try:
        status["distribution_version"] = metadata.version("pyod")
    except metadata.PackageNotFoundError:
        status["distribution_version"] = None
    return status


def probe_extra(name: str, import_pyod_modules: bool = True) -> Dict[str, Any]:
    spec = EXTRAS[name]
    module_status = [module_spec_status(m) for m in spec["modules"]]
    missing = [m["module"] for m in module_status if not m["available"]]
    pyod_modules = []
    if import_pyod_modules:
        pyod_modules = [pyod_import_status(m) for m in spec.get("pyod_modules", [])]
    credential_names = spec.get("credentials", [])
    credentials = {env: bool(os.environ.get(env)) for env in credential_names}
    return {
        "extra": name,
        "available": not missing,
        "missing_modules": missing,
        "modules": module_status,
        "pyod_modules": pyod_modules,
        "credentials_present": credentials,
        "install_hint": spec["hint"],
        "enables": spec["enables"],
    }


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    extras = args.extras or sorted(EXTRAS)
    report = {
        "python": {
            "executable_basename": os.path.basename(sys.executable),
            "version": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "pyod": pyod_status(),
        "torch_runtime": torch_runtime_status(),
        "extras": {name: probe_extra(name, not args.no_pyod_imports) for name in extras},
    }
    return report


def render_text(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    pyod = report["pyod"]
    lines.append(f"pyod: {'OK' if pyod.get('importable') else 'MISSING'} version={pyod.get('version') or pyod.get('distribution_version')}")
    torch_status = report["torch_runtime"]
    if torch_status.get("importable"):
        lines.append(
            "torch: OK version={version} cuda_available={cuda} mps_available={mps}".format(
                version=torch_status.get("version"),
                cuda=torch_status.get("cuda_available"),
                mps=torch_status.get("mps_available", False),
            )
        )
    else:
        lines.append(f"torch: MISSING {torch_status.get('error', '')}".rstrip())
    for name, status in report["extras"].items():
        mark = "OK" if status["available"] else "MISSING"
        lines.append(f"{name}: {mark} - {status['enables']}")
        if status["missing_modules"]:
            lines.append(f"  missing: {', '.join(status['missing_modules'])}")
            lines.append(f"  install: {status['install_hint']}")
        if status["credentials_present"]:
            creds = ", ".join(f"{k}={'set' if v else 'unset'}" for k, v in status["credentials_present"].items())
            lines.append(f"  credentials: {creds}")
        failed_imports = [m for m in status["pyod_modules"] if not m["importable"]]
        if failed_imports:
            lines.append("  pyod module import issues:")
            for item in failed_imports:
                lines.append(f"    - {item['module']}: {item['error']}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe PyOD optional modality backends without downloads, API calls, training, or installs."
    )
    parser.add_argument(
        "--extra",
        dest="extras",
        choices=sorted(EXTRAS),
        action="append",
        help="Limit the report to one extra. Repeat for multiple extras. Default: all modality extras.",
    )
    parser.add_argument(
        "--require",
        choices=sorted(EXTRAS),
        action="append",
        default=[],
        help="Require an extra's import modules to be available; exits 2 if missing. Repeatable.",
    )
    parser.add_argument(
        "--require-credentials",
        action="store_true",
        help="When used with --require for credentialed extras, also require their environment credentials to be set.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format. Default: json.",
    )
    parser.add_argument(
        "--no-pyod-imports",
        action="store_true",
        help="Only check third-party module specs; do not import PyOD optional modules.",
    )
    parser.add_argument(
        "--list-extras",
        action="store_true",
        help="List probeable extras and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_extras:
        print("\n".join(sorted(EXTRAS)))
        return 0

    if args.require:
        selected = set(args.extras or []) | set(args.require)
        args.extras = sorted(selected)

    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))

    failures: List[str] = []
    for name in args.require:
        status = report["extras"][name]
        if not status["available"]:
            failures.append(f"{name}: missing {', '.join(status['missing_modules'])}; install with {status['install_hint']}")
        if args.require_credentials:
            missing_creds = [k for k, v in status["credentials_present"].items() if not v]
            if missing_creds:
                failures.append(f"{name}: missing credential env {', '.join(missing_creds)}")
    if failures:
        print("\nRequirement failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
