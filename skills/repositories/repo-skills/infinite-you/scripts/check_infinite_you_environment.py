#!/usr/bin/env python3
"""Check an InfiniteYou runtime environment without downloading models or running generation.

The checker imports the bundled runtime under ../runtime by default, so it does
not require the original repository checkout. An optional implementation root can
be supplied only when intentionally comparing a refreshed source tree.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

DEPENDENCIES = [
    "torch",
    "torchvision",
    "diffusers",
    "transformers",
    "accelerate",
    "gradio",
    "insightface",
    "facexlib",
    "onnxruntime",
    "optimum.quanto",
    "peft",
    "huggingface_hub",
    "PIL",
    "pillow_heif",
    "pillow_avif",
    "cv2",
    "numpy",
    "sentencepiece",
]

MODEL_VARIANTS = ("aes_stage2", "sim_stage1")


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def bundled_runtime_root() -> Path:
    return skill_root() / "runtime"


def configure_no_network_checks() -> None:
    os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")
    os.environ.setdefault("ALBUMENTATIONS_DISABLE_VERSION_CHECK", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely check InfiniteYou imports, CUDA readiness, bundled runtime, and optional local model layout.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--implementation-root",
        "--repo-root",
        dest="implementation_root",
        help="Optional override root containing pipelines/. Omit this to inspect the bundled runtime. The --repo-root alias is kept for compatibility.",
    )
    parser.add_argument("--model-dir", help="Optional local InfiniteYou model root to validate.")
    parser.add_argument("--base-model-path", help="Optional local FLUX base model directory or gated repo id to describe.")
    parser.add_argument("--require-cuda", action="store_true", help="Return nonzero if CUDA is unavailable.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser.parse_args()


def configure_implementation_path(implementation_root: str | None, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    runtime = bundled_runtime_root()
    report: dict[str, Any] = {
        "bundled_runtime": str(runtime),
        "implementation_root": implementation_root,
        "selected": None,
        "bundled_runtime_complete": False,
    }

    if (runtime / "pipelines" / "pipeline_infu_flux.py").is_file():
        sys.path.insert(0, str(runtime))
        report["selected"] = str(runtime)
        report["bundled_runtime_complete"] = True
    else:
        errors.append(f"Bundled runtime is incomplete: {runtime}")

    if implementation_root:
        root = Path(implementation_root).expanduser().resolve()
        if not root.is_dir():
            errors.append(f"--implementation-root does not exist or is not a directory: {implementation_root}")
        elif not (root / "pipelines" / "pipeline_infu_flux.py").is_file():
            errors.append("--implementation-root must contain pipelines/pipeline_infu_flux.py")
        else:
            sys.path.insert(0, str(root))
            report["selected"] = str(root)
            warnings.append("Using an implementation override instead of the bundled runtime.")
    return report


def import_report(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": version, "file": getattr(module, "__file__", None)}


def cuda_report(require_cuda: bool, errors: list[str]) -> dict[str, Any]:
    torch_info = import_report("torch")
    if not torch_info["ok"]:
        if require_cuda:
            errors.append("torch import failed, so CUDA readiness cannot be checked")
        return {"torch_import": False, "cuda_available": False, "error": torch_info.get("error")}
    import torch

    info: dict[str, Any] = {
        "torch_import": True,
        "torch_version": torch.__version__,
        "torch_cuda_runtime": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
    }
    if torch.cuda.is_available() and torch.cuda.device_count() > 0:
        info["device0_name"] = torch.cuda.get_device_name(0)
        info["device0_capability"] = list(torch.cuda.get_device_capability(0))
        try:
            torch.empty((1,), device="cuda")
            info["tiny_allocation"] = "passed"
        except Exception as exc:
            info["tiny_allocation"] = f"failed: {type(exc).__name__}: {exc}"
            if require_cuda:
                errors.append("CUDA is visible but tiny allocation failed")
    elif require_cuda:
        errors.append("CUDA is required for InfiniteYou generation but is not available")
    return info


def model_layout_report(model_dir_value: str | None) -> dict[str, Any] | None:
    if not model_dir_value:
        return None
    root = Path(model_dir_value).expanduser()
    required = []
    missing = []
    for variant in MODEL_VARIANTS:
        for rel, kind in [
            (Path("infu_flux_v1.0") / variant / "InfuseNetModel", "dir"),
            (Path("infu_flux_v1.0") / variant / "image_proj_model.bin", "file"),
        ]:
            path = root / rel
            exists = path.is_dir() if kind == "dir" else path.is_file()
            required.append({"relative_path": str(rel), "kind": kind, "exists": exists})
            if not exists:
                missing.append(str(rel))
    support = root / "supports" / "insightface"
    support_exists = support.is_dir()
    required.append({"relative_path": "supports/insightface", "kind": "dir", "exists": support_exists})
    if not support_exists:
        missing.append("supports/insightface")
    return {"model_dir": str(root), "required": required, "missing": missing, "ok": not missing}


def main() -> int:
    configure_no_network_checks()
    args = parse_args()
    warnings: list[str] = []
    errors: list[str] = []
    implementation = configure_implementation_path(args.implementation_root, warnings, errors)

    imports = {name: import_report(name) for name in DEPENDENCIES}
    pipeline_imports = {
        "pipelines.pipeline_infu_flux": import_report("pipelines.pipeline_infu_flux"),
        "pipelines.pipeline_flux_infusenet": import_report("pipelines.pipeline_flux_infusenet"),
        "pipelines.resampler": import_report("pipelines.resampler"),
    }
    for name, item in {**imports, **pipeline_imports}.items():
        if not item["ok"]:
            errors.append(f"{name} import failed: {item['error']}")
    cuda = cuda_report(args.require_cuda, errors)
    model_layout = model_layout_report(args.model_dir)
    if model_layout and not model_layout["ok"]:
        warnings.append("Local InfiniteYou model layout is incomplete; full generation will fail unless downloads are explicitly allowed and model access is available.")

    if args.base_model_path == "black-forest-labs/FLUX.1-dev":
        warnings.append("The FLUX.1-dev base model id is gated; license acceptance and authentication may be required.")
    elif args.base_model_path:
        base = Path(args.base_model_path).expanduser()
        if base.exists() and not base.is_dir():
            warnings.append("base-model-path exists but is not a directory; FLUX loading expects a directory-style model layout.")
        elif args.base_model_path.startswith((".", "/", "~")) and not base.exists():
            warnings.append("base-model-path looks local but does not exist.")

    ok = not errors
    report = {
        "ok": ok,
        "implementation": implementation,
        "imports": imports,
        "pipeline_imports": pipeline_imports,
        "cuda": cuda,
        "model_layout": model_layout,
        "warnings": warnings,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"InfiniteYou environment: {'OK' if ok else 'NOT OK'}")
        print(f"Implementation source: {implementation.get('selected')}")
        if errors:
            print("Errors:", file=sys.stderr)
            for item in errors:
                print(f"  - {item}", file=sys.stderr)
        if warnings:
            print("Warnings:")
            for item in warnings:
                print(f"  - {item}")
        missing_imports = [name for name, item in {**imports, **pipeline_imports}.items() if not item["ok"]]
        if missing_imports:
            print("Missing or failing imports:")
            for name in missing_imports:
                source = imports.get(name) or pipeline_imports.get(name)
                print(f"  - {name}: {source['error']}")
        print(f"CUDA available: {cuda.get('cuda_available')} ({cuda.get('device_count')} device(s))")
        if model_layout:
            print(f"Model layout OK: {model_layout['ok']}")
            if model_layout["missing"]:
                print("Missing model paths:")
                for item in model_layout["missing"]:
                    print(f"  - {item}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
