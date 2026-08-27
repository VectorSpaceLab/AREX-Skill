#!/usr/bin/env python3
"""Preflight DragGAN checkpoint directories without downloading model files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

KNOWN_CHECKPOINTS = {
    "stylegan2_lions_512_pytorch.pkl": "https://storage.googleapis.com/self-distilled-stylegan/lions_512_pytorch.pkl",
    "stylegan2_dogs_1024_pytorch.pkl": "https://storage.googleapis.com/self-distilled-stylegan/dogs_1024_pytorch.pkl",
    "stylegan2_horses_256_pytorch.pkl": "https://storage.googleapis.com/self-distilled-stylegan/horses_256_pytorch.pkl",
    "stylegan2_elephants_512_pytorch.pkl": "https://storage.googleapis.com/self-distilled-stylegan/elephants_512_pytorch.pkl",
    "stylegan2-ffhq-512x512.pkl": "https://api.ngc.nvidia.com/v2/models/nvidia/research/stylegan2/versions/1/files/stylegan2-ffhq-512x512.pkl",
    "stylegan2-afhqcat-512x512.pkl": "https://api.ngc.nvidia.com/v2/models/nvidia/research/stylegan2/versions/1/files/stylegan2-afhqcat-512x512.pkl",
    "stylegan2-car-config-f.pkl": "http://d36zk2xti64re0.cloudfront.net/stylegan2/networks/stylegan2-car-config-f.pkl",
    "stylegan2-cat-config-f.pkl": "http://d36zk2xti64re0.cloudfront.net/stylegan2/networks/stylegan2-cat-config-f.pkl",
}


def infer_family(path: Path) -> str:
    name = path.name.lower()
    if "stylegan_human" in name:
        return "stylegan_human"
    if "stylegan3" in name:
        return "stylegan3"
    if "stylegan2" in name:
        return "stylegan2"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DragGAN checkpoint files and renderer-friendly names.")
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"), help="Directory expected to contain .pkl checkpoints.")
    parser.add_argument("--require", action="append", default=[], help="Specific checkpoint filename that must exist. May be repeated.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    checkpoint_dir = args.checkpoint_dir.expanduser().resolve()
    files = sorted(checkpoint_dir.glob("*.pkl")) if checkpoint_dir.exists() else []
    rows = []
    for file in files:
        rows.append({"name": file.name, "family": infer_family(file), "known_manifest": file.name in KNOWN_CHECKPOINTS})

    missing_required = [name for name in args.require if not (checkpoint_dir / name).exists()]
    unknown_family = [row["name"] for row in rows if row["family"] == "unknown"]
    payload = {
        "checkpoint_dir": str(checkpoint_dir),
        "exists": checkpoint_dir.exists(),
        "count": len(rows),
        "checkpoints": rows,
        "missing_required": missing_required,
        "unknown_family": unknown_family,
        "known_manifest_names": sorted(KNOWN_CHECKPOINTS),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Checkpoint dir: {checkpoint_dir}")
        if not checkpoint_dir.exists():
            print("ERROR: directory does not exist. Create it and place DragGAN/StyleGAN .pkl files there.")
        elif not rows:
            print("ERROR: no .pkl checkpoint files found.")
        else:
            for row in rows:
                flag = "known" if row["known_manifest"] else "custom"
                warn = " (renderer family cannot be inferred from filename)" if row["family"] == "unknown" else ""
                print(f"- {row['name']}: family={row['family']} {flag}{warn}")
        if missing_required:
            print("Missing required files:")
            for name in missing_required:
                print(f"- {name}")
        if unknown_family:
            print("WARNING: DragGAN's renderer infers generator class from filename substrings such as stylegan2, stylegan3, or stylegan_human.")

    return 1 if (not checkpoint_dir.exists() or not rows or missing_required) else 0


if __name__ == "__main__":
    raise SystemExit(main())
