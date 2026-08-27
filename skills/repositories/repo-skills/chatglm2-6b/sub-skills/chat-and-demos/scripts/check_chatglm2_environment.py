#!/usr/bin/env python3
"""Check ChatGLM2-6B runtime prerequisites without downloading weights.

Examples:
  python check_chatglm2_environment.py --backend auto
  python check_chatglm2_environment.py --backend cuda --model-path /models/chatglm2-6b
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import sys


def version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("auto", "cpu", "cuda", "mps"), default="auto")
    parser.add_argument("--model-path", type=Path, help="Existing local model directory; never downloaded by this helper.")
    parser.add_argument("--check-gradio-legacy", action="store_true", help="Warn when Gradio is newer than the legacy .style() demo expects.")
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of human-readable output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report: dict[str, object] = {"python": sys.version.split()[0], "packages": {}, "backend": args.backend}
    required = ["torch", "transformers"]
    optional = ["accelerate", "cpm_kernels", "gradio", "streamlit"]
    packages: dict[str, str | None] = {}
    for name in required + optional:
        packages[name] = version(name)
    report["packages"] = packages

    missing = [name for name in required if packages[name] is None]
    if args.model_path is not None:
        report["model_path"] = str(args.model_path)
        report["model_path_exists"] = args.model_path.is_dir()
    else:
        report["model_path_exists"] = None

    backend_ok = True
    backend_details: dict[str, object] = {}
    try:
        import torch  # type: ignore

        backend_details["torch"] = torch.__version__
        backend_details["cuda_available"] = bool(torch.cuda.is_available())
        backend_details["cuda_devices"] = int(torch.cuda.device_count())
        if torch.cuda.is_available():
            backend_details["cuda_device_0"] = torch.cuda.get_device_name(0)
            backend_details["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
        backend_details["mps_available"] = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
        if args.backend == "cuda":
            backend_ok = bool(torch.cuda.is_available())
        elif args.backend == "mps":
            backend_ok = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    except Exception as exc:  # pragma: no cover - diagnostic path
        backend_details["error"] = f"{type(exc).__name__}: {exc}"
        backend_ok = args.backend in {"auto", "cpu"}
    report["backend_details"] = backend_details

    if args.check_gradio_legacy:
        gradio_version = packages.get("gradio")
        report["gradio_legacy_compatible"] = bool(gradio_version and gradio_version.startswith("3."))
        if gradio_version and not gradio_version.startswith("3."):
            report["gradio_warning"] = "The repository demo calls the legacy .style() method; use a 3.x-compatible Gradio or adapt the UI."

    report["missing_required"] = missing
    report["ok"] = not missing and backend_ok and (args.model_path is None or bool(report["model_path_exists"]))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Python: {report['python']}")
        print("Packages:")
        for name, value in packages.items():
            print(f"  {name}: {value or 'missing'}")
        print(f"Backend {args.backend}: {'ok' if backend_ok else 'unavailable'}")
        if args.model_path is not None:
            print(f"Model path: {'exists' if report['model_path_exists'] else 'missing'} ({args.model_path})")
        if report.get("gradio_warning"):
            print(f"Warning: {report['gradio_warning']}")
    return 0 if bool(report["ok"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
