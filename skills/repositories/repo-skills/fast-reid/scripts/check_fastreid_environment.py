#!/usr/bin/env python3
"""Check FastReID import, config, CPU/CUDA, and optional dependency readiness.

The script is safe by default: it imports modules, merges an optional config,
prints backend facts, and never downloads data, trains, evaluates, or writes
checkpoints.

Examples
--------
python check_fastreid_environment.py --repo-root <FASTREID_REPO>
python check_fastreid_environment.py --repo-root <FASTREID_REPO> --config-file <CONFIG_YAML> --device cpu --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

OPTIONAL_MODULES = {
    "torch": "core model/training backend",
    "torchvision": "transforms/backbone utilities",
    "cv2": "demo image I/O and preprocessing",
    "faiss": "optional nearest-neighbor acceleration",
    "onnx": "ONNX export",
    "onnxruntime": "ONNX inference",
    "onnxoptimizer": "ONNX graph optimization",
    "onnxsim": "ONNX simplification",
    "caffe": "Caffe inference/export runtime",
    "tensorrt": "TensorRT engine export/inference",
    "yacs": "FastReID config nodes",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check FastReID import/config/backend readiness without running training.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional FastReID checkout root to add to sys.path.")
    parser.add_argument("--config-file", default=None, help="Optional config YAML to merge for a config smoke check.")
    parser.add_argument("--device", default=None, help="Optional MODEL.DEVICE override before printing config facts.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if FastReID import/config check fails.")
    parser.add_argument("--opts", nargs=argparse.REMAINDER, default=[], help="Additional FastReID KEY VALUE config overrides; put last.")
    return parser


def add_repo_root(path: Path | None) -> str | None:
    if path is None:
        return None
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise SystemExit(f"--repo-root does not exist or is not a directory: {resolved}")
    sys.path.insert(0, str(resolved))
    return str(resolved)


def probe_module(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - depends on user env.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": version}


def normalize_opts(tokens: list[str], parser: argparse.ArgumentParser) -> list[str]:
    if tokens[:1] == ["--"]:
        tokens = tokens[1:]
    if len(tokens) % 2 != 0:
        parser.error("--opts must contain an even number of KEY VALUE tokens")
    return tokens


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = add_repo_root(args.repo_root)
    opts = normalize_opts(list(args.opts), parser)

    payload: dict[str, Any] = {
        "repo_root_supplied": repo_root is not None,
        "fastreid": {"ok": False},
        "config": None,
        "modules": {},
        "torch_backend": None,
        "warnings": [],
    }

    try:
        import fastreid
        from fastreid.config import get_cfg

        payload["fastreid"] = {"ok": True, "version": getattr(fastreid, "__version__", None)}
        if args.config_file:
            cfg = get_cfg()
            cfg.merge_from_file(args.config_file)
            if args.device:
                opts.extend(["MODEL.DEVICE", args.device])
            if opts:
                cfg.merge_from_list(opts)
            payload["config"] = {
                "ok": True,
                "config_file": args.config_file,
                "model_device": cfg.MODEL.DEVICE,
                "meta_architecture": cfg.MODEL.META_ARCHITECTURE,
                "datasets_names": list(cfg.DATASETS.NAMES),
                "datasets_tests": list(cfg.DATASETS.TESTS),
                "output_dir": cfg.OUTPUT_DIR,
            }
    except Exception as exc:  # pragma: no cover - depends on user env.
        payload["fastreid"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    for name, purpose in OPTIONAL_MODULES.items():
        result = probe_module(name)
        result["purpose"] = purpose
        payload["modules"][name] = result

    torch_info = payload["modules"].get("torch", {})
    if torch_info.get("ok"):
        try:
            import torch
            cuda = bool(torch.cuda.is_available())
            payload["torch_backend"] = {
                "torch_version": getattr(torch, "__version__", None),
                "cuda_available": cuda,
                "cuda_device_count": int(torch.cuda.device_count()),
            }
            if cuda:
                payload["torch_backend"]["cuda_device_0"] = torch.cuda.get_device_name(0)
        except Exception as exc:  # pragma: no cover - depends on user env.
            payload["torch_backend"] = {"error": f"{type(exc).__name__}: {exc}"}

    if payload["fastreid"].get("ok") and not payload["modules"].get("faiss", {}).get("ok"):
        payload["warnings"].append("faiss is optional but recommended by FastReID docs for retrieval/ranking acceleration.")
    if payload["modules"].get("torch", {}).get("ok") and not (payload.get("torch_backend") or {}).get("cuda_available"):
        payload["warnings"].append("Torch imports but CUDA is unavailable; realistic training/eval may need a CUDA-capable environment.")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"FastReID import: {payload['fastreid']}")
        if payload["config"] is not None:
            print(f"Config: {payload['config']}")
        print(f"Torch backend: {payload['torch_backend']}")
        for name, result in payload["modules"].items():
            status = "ok" if result.get("ok") else "missing/error"
            detail = result.get("version") or result.get("error") or ""
            print(f"{name}: {status} {detail}")
        if payload["warnings"]:
            print("Warnings:")
            for item in payload["warnings"]:
                print(f"- {item}")

    if args.strict and not payload["fastreid"].get("ok"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
