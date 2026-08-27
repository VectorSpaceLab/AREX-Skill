#!/usr/bin/env python3
"""Check the most important Lumina-T2X runtime dependencies.

This helper is intentionally safe: it only imports modules, reports missing
packages, and prints CUDA visibility. It never downloads checkpoints or runs
sampling/training.

Example:
    python scripts/check_env.py --workflow image --repo-root /path/to/checkout
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path

import torch

WORKFLOW_IMPORTS = {
    "image": [
        "diffusers",
        "fairscale",
        "accelerate",
        "transformers",
        "gradio",
        "torchdiffeq",
        "flash_attn",
        "safetensors",
    ],
    "image-training": [
        "diffusers",
        "fairscale",
        "accelerate",
        "transformers",
        "torchdiffeq",
        "flash_attn",
        "h5py",
        "yaml",
    ],
    "audio": ["soundfile", "omegaconf", "torchdyn", "pytorch_lightning", "torchlibrosa", "openai", "flash_attn"],
    "music": ["soundfile", "omegaconf", "torchdyn", "pytorch_lightning", "torchlibrosa", "flash_attn"],
    "visual-anagrams": ["diffusers", "transformers", "flash_attn", "einops", "imageio", "imageio_ffmpeg"],
    "imagenet": ["diffusers", "flash_attn", "einops", "torchvision"],
}

WORKFLOW_MODULES = {
    "image": [
        "lumina_t2i.entry_point",
        "lumina_next_t2i.entry_point",
        "lumina_next_t2i_mini.sample",
    ],
    "image-training": [
        "lumina_t2i.train",
        "lumina_next_t2i.train",
        "lumina_next_t2i_mini.train",
        "lumina_next_t2i_mini.train_dreambooth_sd3",
    ],
    "visual-anagrams": ["visual_anagrams.generate", "visual_anagrams.animate"],
}

WORKFLOW_FILES = {
    "audio": ["lumina_audio/demo_audio.py", "lumina_audio/n2s_openai.py"],
    "music": ["lumina_music/demo_music.py"],
    "imagenet": ["Flag-DiT-ImageNet/train.py", "Next-DiT-ImageNet/train.py", "Next-DiT-MoE/train.py"],
}


def import_module(name: str):
    return importlib.import_module(name)


def import_file(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_imports(names: list[str]) -> list[tuple[str, bool, str]]:
    results = []
    for name in names:
        try:
            mod = import_module(name)
            results.append((name, True, getattr(mod, "__version__", "")))
        except Exception as exc:  # noqa: BLE001 - report every import failure clearly
            results.append((name, False, f"{type(exc).__name__}: {exc}"))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workflow",
        choices=["all", "image", "image-training", "audio", "music", "visual-anagrams", "imagenet"],
        default="all",
        help="Which workflow family to probe.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional repository root to add to sys.path before importing repo modules.",
    )
    args = parser.parse_args()

    if args.repo_root is not None:
        repo_root = args.repo_root.resolve()
        sys.path.insert(0, str(repo_root))
        visual_root = repo_root / "visual_anagrams"
        if visual_root.exists():
            sys.path.insert(0, str(visual_root))
        print(f"repo_root={repo_root}")

    print(f"python={sys.version.split()[0]}")
    print(f"torch={torch.__version__}")
    print(f"cuda_available={torch.cuda.is_available()} device_count={torch.cuda.device_count()}")
    if torch.cuda.is_available():
        try:
            x = torch.zeros(1, device="cuda")
            print(f"cuda_smoke=ok device={x.device}")
        except Exception as exc:  # noqa: BLE001
            print(f"cuda_smoke=fail {type(exc).__name__}: {exc}")

    workflows = [args.workflow] if args.workflow != "all" else list(WORKFLOW_IMPORTS)
    failed = False

    for workflow in workflows:
        print(f"\n[{workflow}]")
        imports = check_imports(WORKFLOW_IMPORTS.get(workflow, []))
        for name, ok, detail in imports:
            status = "OK" if ok else "FAIL"
            print(f"  import {name}: {status}{f' ({detail})' if detail else ''}")
            failed = failed or not ok

        for mod in WORKFLOW_MODULES.get(workflow, []):
            try:
                import_module(mod)
                print(f"  module {mod}: OK")
            except Exception as exc:  # noqa: BLE001
                print(f"  module {mod}: FAIL ({type(exc).__name__}: {exc})")
                failed = True

        for rel in WORKFLOW_FILES.get(workflow, []):
            if args.repo_root is None:
                print(f"  file {rel}: SKIP (provide --repo-root to check script-based modules)")
                continue
            file_path = (args.repo_root / rel).resolve()
            if not file_path.exists():
                print(f"  file {rel}: FAIL (missing)")
                failed = True
                continue
            try:
                import_file(file_path, rel.replace("/", ".").replace("-", "_"))
                print(f"  file {rel}: OK")
            except Exception as exc:  # noqa: BLE001
                print(f"  file {rel}: FAIL ({type(exc).__name__}: {exc})")
                failed = True

    if failed:
        print("\nResult: environment is not ready for every selected workflow.")
        return 1

    print("\nResult: environment checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
