#!/usr/bin/env python3
"""Validate a Stable Diffusion WebUI asset layout without importing WebUI modules.

The script checks expected directories and recognized file suffixes. It does not
load model weights, import torch, read safetensors metadata, or contact network
URLs.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

CHECKPOINT_SUFFIXES = (".safetensors", ".ckpt")
CHECKPOINT_VAE_SUFFIXES = (".vae.safetensors", ".vae.ckpt", ".vae.pt")
VAE_SUFFIXES = (".safetensors", ".ckpt", ".pt")
LORA_SUFFIXES = (".safetensors", ".ckpt", ".pt")
HYPERNETWORK_SUFFIXES = (".pt",)
EMBEDDING_SUFFIXES = (".pt", ".bin", ".safetensors", ".png", ".webp", ".jxl", ".avif")
UPSCALER_SUFFIXES = {
    "ESRGAN": (".pt", ".pth"),
    "RealESRGAN": (".pth",),
    "DAT": (".pt", ".pth"),
    "HAT": (".pt", ".pth"),
    "GFPGAN": (".pth",),
    "Codeformer": (".pth",),
    "BSRGAN": (".pt", ".pth"),
}


def path_arg(value: str | None) -> Path | None:
    if value is None:
        return None
    return Path(value).expanduser().resolve()


def relative_to(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def has_suffix(path: Path, suffixes: Iterable[str]) -> bool:
    lower_name = path.name.lower()
    return any(lower_name.endswith(suffix) for suffix in suffixes)


def walk_matching(directory: Path, suffixes: Iterable[str]) -> list[Path]:
    if not directory.is_dir():
        return []
    matches: list[Path] = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            candidate = Path(root) / filename
            if has_suffix(candidate, suffixes):
                matches.append(candidate)
    return sorted(matches, key=lambda item: str(item).lower())


def count_files(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    total = 0
    for _, _, filenames in os.walk(directory):
        total += len(filenames)
    return total


def directory_record(name: str, path: Path, suffixes: Iterable[str], root: Path) -> dict:
    matches = walk_matching(path, suffixes)
    return {
        "name": name,
        "path": str(path),
        "exists": path.is_dir(),
        "recognized_count": len(matches),
        "recognized_files": [relative_to(item, root) for item in matches],
        "unrecognized_file_count": max(count_files(path) - len(matches), 0),
        "suffixes": list(suffixes),
    }


def add_message(messages: list[str], condition: bool, message: str) -> None:
    if condition:
        messages.append(message)


def build_report(args: argparse.Namespace) -> dict:
    data_dir = path_arg(args.data_dir) or Path.cwd().resolve()
    models_dir = path_arg(args.models_dir) or (data_dir / "models")
    checkpoint_dir = path_arg(args.ckpt_dir) or (models_dir / "Stable-diffusion")
    vae_dir = path_arg(args.vae_dir) or (models_dir / "VAE")
    embeddings_dir = path_arg(args.embeddings_dir) or (data_dir / "embeddings")
    hypernetwork_dir = path_arg(args.hypernetwork_dir) or (models_dir / "hypernetworks")
    lora_dir = path_arg(args.lora_dir) or (models_dir / "Lora")
    lyco_dir = path_arg(args.lyco_dir_backcompat) or (models_dir / "LyCORIS")

    upscaler_dirs = {
        "ESRGAN": path_arg(args.esrgan_models_path) or (models_dir / "ESRGAN"),
        "RealESRGAN": path_arg(args.realesrgan_models_path) or (models_dir / "RealESRGAN"),
        "DAT": path_arg(args.dat_models_path) or (models_dir / "DAT"),
        "HAT": models_dir / "HAT",
        "GFPGAN": path_arg(args.gfpgan_models_path) or (models_dir / "GFPGAN"),
        "Codeformer": path_arg(args.codeformer_models_path) or (models_dir / "Codeformer"),
        "BSRGAN": path_arg(args.bsrgan_models_path) or (models_dir / "BSRGAN"),
    }

    records = [
        directory_record("checkpoints", checkpoint_dir, CHECKPOINT_SUFFIXES, data_dir),
        directory_record("checkpoint-adjacent-vaes", checkpoint_dir, CHECKPOINT_VAE_SUFFIXES, data_dir),
        directory_record("vaes", vae_dir, VAE_SUFFIXES, data_dir),
        directory_record("embeddings", embeddings_dir, EMBEDDING_SUFFIXES, data_dir),
        directory_record("hypernetworks", hypernetwork_dir, HYPERNETWORK_SUFFIXES, data_dir),
        directory_record("loras", lora_dir, LORA_SUFFIXES, data_dir),
        directory_record("lycoris-backcompat", lyco_dir, LORA_SUFFIXES, data_dir),
    ]

    for name, path in upscaler_dirs.items():
        records.append(directory_record(f"upscaler-{name.lower()}", path, UPSCALER_SUFFIXES[name], data_dir))

    explicit_ckpt = path_arg(args.ckpt)
    explicit_vae = path_arg(args.vae_path)
    checkpoint_files = walk_matching(checkpoint_dir, CHECKPOINT_SUFFIXES)
    checkpoint_files = [item for item in checkpoint_files if not has_suffix(item, CHECKPOINT_VAE_SUFFIXES)]
    checkpoint_vae_files = walk_matching(checkpoint_dir, CHECKPOINT_VAE_SUFFIXES)
    vae_files = walk_matching(vae_dir, VAE_SUFFIXES)
    lora_files = walk_matching(lora_dir, LORA_SUFFIXES) + walk_matching(lyco_dir, LORA_SUFFIXES)
    hypernetwork_files = [item for item in walk_matching(hypernetwork_dir, HYPERNETWORK_SUFFIXES) if item.stem != "None"]
    ignored_hypernetworks = [item for item in walk_matching(hypernetwork_dir, HYPERNETWORK_SUFFIXES) if item.stem == "None"]

    if explicit_ckpt and explicit_ckpt.is_file() and has_suffix(explicit_ckpt, CHECKPOINT_SUFFIXES):
        checkpoint_files.append(explicit_ckpt)
    if explicit_vae and explicit_vae.is_file() and has_suffix(explicit_vae, VAE_SUFFIXES):
        vae_files.append(explicit_vae)

    errors: list[str] = []
    warnings: list[str] = []
    add_message(errors, not data_dir.exists(), "data directory does not exist")
    add_message(errors, not models_dir.exists(), "models directory does not exist")
    add_message(errors, len(checkpoint_files) == 0, "no regular .safetensors or .ckpt checkpoint found")
    add_message(errors, explicit_ckpt is not None and not explicit_ckpt.exists(), "--ckpt points to a missing file")
    add_message(errors, explicit_ckpt is not None and explicit_ckpt.exists() and not has_suffix(explicit_ckpt, CHECKPOINT_SUFFIXES), "--ckpt file has an unsupported checkpoint suffix")
    add_message(errors, explicit_vae is not None and not explicit_vae.exists(), "--vae-path points to a missing file")
    add_message(errors, explicit_vae is not None and explicit_vae.exists() and not has_suffix(explicit_vae, VAE_SUFFIXES), "--vae-path file has an unsupported VAE suffix")
    add_message(warnings, len(vae_files) == 0 and len(checkpoint_vae_files) == 0, "no VAE files found in VAE directory or beside checkpoints")
    add_message(warnings, len(ignored_hypernetworks) > 0, "one or more hypernetworks named None.pt will be ignored")

    unsafe_candidates = []
    for collection in (checkpoint_files, vae_files, checkpoint_vae_files, lora_files, hypernetwork_files):
        unsafe_candidates.extend(item for item in collection if item.suffix.lower() in {".ckpt", ".pt", ".bin"})
    add_message(warnings, len(unsafe_candidates) > 0, "pickle-based .ckpt/.pt/.bin assets present; prefer safetensors when available and keep safe unpickle enabled")

    likely_misplaced_vaes = [item for item in walk_matching(checkpoint_dir, VAE_SUFFIXES) if has_suffix(item, CHECKPOINT_VAE_SUFFIXES)]
    likely_misplaced_checkpoints = [item for item in walk_matching(vae_dir, CHECKPOINT_SUFFIXES) if not has_suffix(item, VAE_SUFFIXES)]
    add_message(warnings, len(likely_misplaced_checkpoints) > 0, "regular checkpoint-looking files exist in the VAE directory")

    upscaler_counts = {
        name: len(walk_matching(path, UPSCALER_SUFFIXES[name]))
        for name, path in upscaler_dirs.items()
    }

    summary = {
        "data_dir": str(data_dir),
        "models_dir": str(models_dir),
        "checkpoint_count": len(set(checkpoint_files)),
        "checkpoint_adjacent_vae_count": len(set(likely_misplaced_vaes)),
        "vae_count": len(set(vae_files)),
        "embedding_count": len(walk_matching(embeddings_dir, EMBEDDING_SUFFIXES)),
        "hypernetwork_count": len(hypernetwork_files),
        "lora_or_lycoris_count": len(set(lora_files)),
        "upscaler_counts": upscaler_counts,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }

    return {
        "ok": len(errors) == 0,
        "summary": summary,
        "directories": records,
        "errors": errors,
        "warnings": warnings,
        "notes": [
            "Refresh WebUI lists after adding files; this script only scans disk layout.",
            "List endpoints can discover files that may still fail later during model load or activation.",
            "Restart WebUI after changing launch path flags; refresh endpoints do not change startup path policy.",
        ],
    }


def print_text(report: dict) -> None:
    summary = report["summary"]
    print("Stable Diffusion WebUI asset layout")
    print(f"  data_dir: {summary['data_dir']}")
    print(f"  models_dir: {summary['models_dir']}")
    print(f"  checkpoints: {summary['checkpoint_count']}")
    print(f"  VAEs: {summary['vae_count']} general, {summary['checkpoint_adjacent_vae_count']} checkpoint-adjacent")
    print(f"  embeddings: {summary['embedding_count']}")
    print(f"  hypernetworks: {summary['hypernetwork_count']}")
    print(f"  Lora/LyCORIS: {summary['lora_or_lycoris_count']}")
    print("  upscalers:")
    for name, count in summary["upscaler_counts"].items():
        print(f"    {name}: {count}")

    if report["errors"]:
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  - {error}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")

    if not report["errors"] and not report["warnings"]:
        print("\nNo layout warnings found.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Stable Diffusion WebUI model/asset directory layout without loading models.")
    parser.add_argument("--data-dir", help="Base user data directory; default is current directory.")
    parser.add_argument("--models-dir", help="Base model directory; default is <data-dir>/models.")
    parser.add_argument("--ckpt", help="Explicit checkpoint file to include in discovery.")
    parser.add_argument("--ckpt-dir", help="Directory containing Stable Diffusion checkpoints.")
    parser.add_argument("--vae-dir", help="Directory containing VAE files.")
    parser.add_argument("--vae-path", help="Explicit VAE file override.")
    parser.add_argument("--embeddings-dir", help="Textual inversion embeddings directory.")
    parser.add_argument("--hypernetwork-dir", help="Hypernetwork directory.")
    parser.add_argument("--lora-dir", help="Lora directory.")
    parser.add_argument("--lyco-dir-backcompat", help="Legacy LyCORIS directory.")
    parser.add_argument("--esrgan-models-path", help="ESRGAN model directory.")
    parser.add_argument("--realesrgan-models-path", help="RealESRGAN model directory.")
    parser.add_argument("--dat-models-path", help="DAT model directory.")
    parser.add_argument("--gfpgan-models-path", help="GFPGAN model directory.")
    parser.add_argument("--codeformer-models-path", help="CodeFormer model directory.")
    parser.add_argument("--bsrgan-models-path", help="BSRGAN model directory.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
