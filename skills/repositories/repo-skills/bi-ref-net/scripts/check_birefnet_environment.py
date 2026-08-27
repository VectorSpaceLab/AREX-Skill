#!/usr/bin/env python3
"""Safe BiRefNet environment probe.

This script checks base dependencies, optional CUDA visibility, and optionally
source-module imports from an explicit BiRefNet checkout. It does not download
weights, start training, or run full inference.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

BASE_IMPORTS = [
    "torch",
    "torchvision",
    "cv2",
    "numpy",
    "PIL",
    "timm",
    "scipy",
    "skimage",
    "kornia",
    "einops",
    "tqdm",
    "prettytable",
    "tabulate",
    "huggingface_hub",
    "accelerate",
]

SOURCE_IMPORTS = [
    "config",
    "dataset",
    "image_proc",
    "utils",
    "models.birefnet",
    "evaluation.metrics",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check BiRefNet dependencies, optional backend visibility, and source imports.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", help="BiRefNet checkout root to use for source-module checks.")
    parser.add_argument("--check-source", action="store_true", help="Import BiRefNet source modules from --repo-root.")
    parser.add_argument(
        "--construct-model",
        action="store_true",
        help="With --check-source, instantiate BiRefNet(bb_pretrained=False). This may use memory but should not download backbone weights.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    return parser


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        return {
            "module": module_name,
            "ok": True,
            "version": getattr(module, "__version__", None),
            "error": None,
        }
    except Exception as exc:  # pragma: no cover - user environment dependent
        return {
            "module": module_name,
            "ok": False,
            "version": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def torch_backend_report() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    report: dict[str, Any] = {
        "ok": True,
        "torch_version": getattr(torch, "__version__", None),
        "cuda_build": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()),
        "devices": [],
    }
    if torch.cuda.is_available():
        for index in range(torch.cuda.device_count()):
            device = {"index": index, "name": torch.cuda.get_device_name(index)}
            try:
                device["capability"] = list(torch.cuda.get_device_capability(index))
            except Exception:
                device["capability"] = None
            report["devices"].append(device)
        try:
            torch.empty((1,), device="cuda")
            report["tiny_cuda_allocation"] = "passed"
        except Exception as exc:
            report["tiny_cuda_allocation"] = f"failed: {type(exc).__name__}: {exc}"
    return report


def configure_source_path(repo_root_text: str | None) -> Path:
    if not repo_root_text:
        raise SystemExit("--check-source requires --repo-root.")
    repo_root = Path(repo_root_text).expanduser().resolve()
    required = [repo_root / "config.py", repo_root / "models" / "birefnet.py", repo_root / "evaluation" / "metrics.py"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("--repo-root does not look like BiRefNet; missing: " + ", ".join(missing))
    sys.path.insert(0, str(repo_root))
    return repo_root


def source_smokes(construct_model: bool) -> dict[str, Any]:
    report: dict[str, Any] = {}
    try:
        import torch
        from models.birefnet import BiRefNet, image2patches, patches2image
        from utils import check_state_dict

        state = {
            "module._orig_mod.bb.weight": torch.ones(1),
            "_orig_mod.decoder.bias": torch.zeros(1),
            "plain.weight": torch.ones(1),
        }
        cleaned = check_state_dict(dict(state))
        report["state_dict_prefix_cleanup"] = {
            "ok": sorted(cleaned) == ["bb.weight", "decoder.bias", "plain.weight"],
            "cleaned_keys": sorted(cleaned),
        }

        x = torch.arange(1 * 3 * 4 * 4).reshape(1, 3, 4, 4)
        patches = image2patches(x, grid_h=2, grid_w=2)
        rebuilt = patches2image(patches, grid_h=2, grid_w=2)
        report["patch_roundtrip"] = {"ok": bool(torch.equal(x, rebuilt)), "patches_shape": list(patches.shape)}

        if construct_model:
            model = BiRefNet(bb_pretrained=False)
            report["model_constructed"] = {"ok": True, "class": type(model).__name__}
        else:
            report["model_constructed"] = "skipped"
    except Exception as exc:  # pragma: no cover - environment dependent
        report["error"] = f"{type(exc).__name__}: {exc}"
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report: dict[str, Any] = {
        "base_imports": [import_status(name) for name in BASE_IMPORTS],
        "torch_backend": torch_backend_report(),
        "source_imports": [],
        "source_smokes": {},
        "warnings": [],
    }

    if args.check_source:
        configure_source_path(args.repo_root)
        report["source_imports"] = [import_status(name) for name in SOURCE_IMPORTS]
        report["source_smokes"] = source_smokes(args.construct_model)
    elif args.construct_model:
        report["warnings"].append("--construct-model ignored because --check-source was not supplied.")

    base_ok = all(item["ok"] for item in report["base_imports"])
    source_ok = all(item["ok"] for item in report["source_imports"]) if args.check_source else True
    smoke_error = isinstance(report["source_smokes"], dict) and bool(report["source_smokes"].get("error"))
    report["ok"] = bool(base_ok and source_ok and not smoke_error)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("BiRefNet environment check:", "OK" if report["ok"] else "FAILED")
        print(f"Base imports: {sum(1 for item in report['base_imports'] if item['ok'])}/{len(report['base_imports'])}")
        backend = report["torch_backend"]
        if backend.get("ok"):
            print(
                "Torch:",
                backend.get("torch_version"),
                "cuda_build=", backend.get("cuda_build"),
                "cuda_available=", backend.get("cuda_available"),
                "devices=", backend.get("device_count"),
            )
        if args.check_source:
            print(f"Source imports: {sum(1 for item in report['source_imports'] if item['ok'])}/{len(report['source_imports'])}")
            if report["source_smokes"]:
                print("Source smokes:", json.dumps(report["source_smokes"], sort_keys=True))
        for item in report["base_imports"] + report["source_imports"]:
            if not item["ok"]:
                print(f"MISSING {item['module']}: {item['error']}")
        for warning in report["warnings"]:
            print("WARNING:", warning)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
