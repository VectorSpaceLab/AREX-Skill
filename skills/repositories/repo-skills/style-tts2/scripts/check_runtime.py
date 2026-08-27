#!/usr/bin/env python3
"""Check a StyleTTS2 source checkout without training, downloading, or synthesizing."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

DEPENDENCY_IMPORTS = [
    "torch",
    "torchaudio",
    "yaml",
    "munch",
    "librosa",
    "soundfile",
    "pydub",
    "nltk",
    "matplotlib",
    "accelerate",
    "transformers",
    "einops",
    "einops_exts",
    "tqdm",
    "monotonic_align",
    "pandas",
    "tensorboard",
]

OPTIONAL_INFERENCE_IMPORTS = ["phonemizer"]

SOURCE_IMPORTS = [
    "models",
    "utils",
    "losses",
    "meldataset",
    "optimizers",
    "text_utils",
    "Modules.slmadv",
    "Modules.diffusion.sampler",
    "Modules.diffusion.diffusion",
    "Modules.discriminators",
    "Utils.ASR.models",
    "Utils.JDC.model",
    "Utils.PLBERT.util",
    "train_first",
    "train_second",
    "train_finetune",
    "train_finetune_accelerate",
]

HELPER_ASSETS = {
    "ASR_config": "Utils/ASR/config.yml",
    "ASR_path": "Utils/ASR/epoch_00080.pth",
    "F0_path": "Utils/JDC/bst.t7",
    "PLBERT_config": "Utils/PLBERT/config.yml",
    "PLBERT_checkpoint": "Utils/PLBERT/step_1000000.t7",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check StyleTTS2 imports, dependencies, CUDA, and optional helper assets safely.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="StyleTTS2 source checkout to inspect. Defaults to current directory.",
    )
    parser.add_argument(
        "--check-cuda",
        action="store_true",
        help="Run a tiny CUDA availability/allocation check with torch.",
    )
    parser.add_argument(
        "--check-inference-deps",
        action="store_true",
        help="Also check optional inference imports such as phonemizer.",
    )
    parser.add_argument(
        "--load-helper-models",
        action="store_true",
        help="Load ASR, F0/JDC, PL-BERT, and build the default model graph. This is heavier but still does not train or synthesize.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human summary.",
    )
    return parser.parse_args()


def import_one(name: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {"name": name, "status": "ok", "file": getattr(mod, "__file__", None)}
    except Exception as exc:
        return {"name": name, "status": "error", "error": f"{type(exc).__name__}: {exc}"}


def check_paths(repo_root: Path) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for label, rel_path in HELPER_ASSETS.items():
        path = repo_root / rel_path
        results.append({"label": label, "path": rel_path, "status": "ok" if path.exists() else "missing"})
    return results


def check_cuda() -> Dict[str, Any]:
    try:
        import torch

        info: Dict[str, Any] = {
            "status": "ok" if torch.cuda.is_available() else "missing",
            "torch": getattr(torch, "__version__", None),
            "torch_cuda": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            info["device0"] = torch.cuda.get_device_name(0)
            info["capability0"] = list(torch.cuda.get_device_capability(0))
            tensor = torch.empty(1, device="cuda")
            info["allocation_device"] = str(tensor.device)
        return info
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


def load_helper_models(repo_root: Path) -> Dict[str, Any]:
    try:
        import yaml
        from models import build_model, load_ASR_models, load_F0_models
        from utils import recursive_munch
        from Utils.PLBERT.util import load_plbert

        config_path = repo_root / "Configs" / "config.yml"
        with config_path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        text_aligner = load_ASR_models(str(repo_root / "Utils/ASR/epoch_00080.pth"), str(repo_root / "Utils/ASR/config.yml"))
        pitch_extractor = load_F0_models(str(repo_root / "Utils/JDC/bst.t7"))
        plbert = load_plbert(str(repo_root / "Utils/PLBERT"))
        model = build_model(recursive_munch(config["model_params"]), text_aligner, pitch_extractor, plbert)
        return {"status": "ok", "model_keys": sorted(model.keys())}
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    repo_root = Path(args.repo_root).expanduser().resolve()
    report: Dict[str, Any] = {
        "repo_root": str(repo_root),
        "python": sys.executable,
        "status": "ok",
        "dependency_imports": [],
        "source_imports": [],
        "helper_assets": [],
        "cuda": None,
        "helper_model_load": None,
        "notes": [
            "No training was started.",
            "No model downloads were attempted.",
            "No speech was synthesized.",
        ],
    }

    if not repo_root.is_dir():
        report["status"] = "error"
        report["error"] = f"repo root is not a directory: {repo_root}"
        return report

    imports = list(DEPENDENCY_IMPORTS)
    if args.check_inference_deps:
        imports.extend(OPTIONAL_INFERENCE_IMPORTS)
    dep_results = [import_one(name) for name in imports]
    report["dependency_imports"] = dep_results

    sys.path.insert(0, str(repo_root))
    source_results = [import_one(name) for name in SOURCE_IMPORTS]
    report["source_imports"] = source_results
    report["helper_assets"] = check_paths(repo_root)

    if args.check_cuda:
        report["cuda"] = check_cuda()
    if args.load_helper_models:
        report["helper_model_load"] = load_helper_models(repo_root)

    has_error = any(item["status"] == "error" for item in dep_results + source_results)
    has_missing_asset = any(item["status"] == "missing" for item in report["helper_assets"])
    cuda_bad = report["cuda"] is not None and report["cuda"].get("status") != "ok"
    helper_bad = report["helper_model_load"] is not None and report["helper_model_load"].get("status") != "ok"
    if has_error or has_missing_asset or cuda_bad or helper_bad:
        report["status"] = "error"
    return report


def print_human(report: Dict[str, Any]) -> None:
    print(f"status: {report['status']}")
    print(f"repo_root: {report['repo_root']}")
    print(f"python: {report['python']}")
    print()

    def show_imports(title: str, items: List[Dict[str, Any]]) -> None:
        print(f"[{title}]")
        for item in items:
            if item["status"] == "ok":
                print(f"  OK {item['name']}")
            else:
                print(f"  ERROR {item['name']}: {item['error']}")
        print()

    show_imports("dependencies", report.get("dependency_imports", []))
    show_imports("source", report.get("source_imports", []))

    print("[helper assets]")
    for item in report.get("helper_assets", []):
        print(f"  {item['status'].upper()} {item['label']}: {item['path']}")
    print()

    if report.get("cuda") is not None:
        print("[cuda]")
        for key, value in report["cuda"].items():
            print(f"  {key}: {value}")
        print()
    if report.get("helper_model_load") is not None:
        print("[helper model load]")
        for key, value in report["helper_model_load"].items():
            print(f"  {key}: {value}")
        print()

    for note in report.get("notes", []):
        print(f"note: {note}")


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
