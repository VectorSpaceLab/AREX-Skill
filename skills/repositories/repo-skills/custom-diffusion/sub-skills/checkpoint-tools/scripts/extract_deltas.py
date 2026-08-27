#!/usr/bin/env python3
# Adapted from Adobe Research Custom Diffusion source code.
# Copyright 2022 Adobe Research. All rights reserved.
# To view a copy of the license, visit LICENSE.md.
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import torch

def _candidate_checkpoints(root: Path) -> list[Path]:
    if root.is_file():
        return [] if "delta" in root.name else [root]
    checkpoint_root = root / "checkpoints" if (root / "checkpoints").is_dir() else root
    files: list[Path] = []
    for path in sorted(checkpoint_root.iterdir()):
        if not path.is_file():
            continue
        if "delta" in path.name:
            continue
        if "=" in path.name or "_" in path.name:
            files.append(path)
    return files

def _epoch_fragment(path: Path) -> str:
    name = path.name
    if "=" in name:
        return name.split("=")[-1].split(".ckpt")[0]
    return name.rsplit(".", 1)[0]

def extract_checkpoint(path: Path, newtoken: int, output_dir: Path | None, delete_source: bool, dry_run: bool) -> list[Path]:
    candidates = _candidate_checkpoints(path)
    if not candidates:
        raise FileNotFoundError(f"no checkpoint files found under {path}")

    extracted: list[Path] = []
    layers: list[str] = []
    for source in candidates:
        payload = torch.load(source, map_location="cpu", weights_only=False)
        state_dict = payload.get("state_dict")
        if not isinstance(state_dict, dict):
            raise ValueError(f"checkpoint does not contain a state_dict: {source}")

        if not layers:
            layers = [key for key in state_dict if "attn2.to_k" in key or "attn2.to_v" in key]
            if not layers:
                raise ValueError(f"no attn2.to_k / attn2.to_v keys found in {source}")

        delta_state = {"state_dict": {key: state_dict[key].clone() for key in layers}}
        if newtoken > 0 and "cond_stage_model.transformer.text_model.embeddings.token_embedding.weight" in state_dict:
            embed = state_dict["cond_stage_model.transformer.text_model.embeddings.token_embedding.weight"]
            delta_state["state_dict"]["embed"] = embed[-newtoken:].clone()

        destination_dir = output_dir if output_dir is not None else source.parent
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"delta_epoch={_epoch_fragment(source)}.ckpt"
        if not dry_run:
            torch.save(delta_state, destination)
            if delete_source:
                source.unlink()
        extracted.append(destination)
        print(f"{source} -> {destination}")
    return extracted

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely extract K/V deltas from a checkpoint folder.")
    parser.add_argument("--path", required=True, help="Folder containing checkpoint files or a checkpoint file.")
    parser.add_argument("--newtoken", type=int, default=1, help="Number of optimized embedding tokens to save.")
    parser.add_argument("--output-dir", default=None, help="Optional directory for the extracted delta files.")
    parser.add_argument("--delete-source", action="store_true", help="Delete each source checkpoint after extraction.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written without saving anything.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    path = Path(args.path)
    output_dir = Path(args.output_dir) if args.output_dir else None
    extract_checkpoint(path, args.newtoken, output_dir, args.delete_source, args.dry_run)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
