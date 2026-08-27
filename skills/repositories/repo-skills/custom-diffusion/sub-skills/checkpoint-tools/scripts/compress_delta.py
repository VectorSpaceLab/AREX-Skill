#!/usr/bin/env python3
# Adapted from Adobe Research Custom Diffusion source code.
# Copyright 2022 Adobe Research. All rights reserved.
# To view a copy of the license, visit LICENSE.md.
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import torch

def _ensure_device(device: str) -> torch.device:
    selected = torch.device(device)
    if selected.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested for compression but is not available")
    return selected

def _default_output(delta_ckpt: Path) -> Path:
    name = delta_ckpt.name.replace("delta", "compressed_delta")
    return delta_ckpt.with_name(name)

def _compress_matrix(delta_w: torch.Tensor, compression_ratio: float) -> tuple[torch.Tensor, torch.Tensor]:
    u, s, vh = torch.linalg.svd(delta_w, full_matrices=False)
    if s.numel() == 0:
        raise ValueError("SVD produced no singular values")
    total = float(s.sum().item())
    cumulative = 0.0
    rank = len(s)
    for index, value in enumerate(s.tolist()):
        cumulative += float(value)
        if total > 0 and cumulative / total > compression_ratio:
            rank = max(1, index + 1)
            break
    u_part = u[:, :rank] @ torch.diag(s[:rank])
    v_part = vh[:rank, :]
    return u_part, v_part

def compress(delta_ckpt: str, ckpt: str, diffuser: bool = False, compression_ratio: float = 0.6, device: str = "cuda", output: str | None = None) -> Path:
    selected_device = _ensure_device(device)
    delta_path = Path(delta_ckpt)
    output_path = Path(output) if output else _default_output(delta_path)

    st = torch.load(delta_path, map_location="cpu", weights_only=False)
    if diffuser:
        from diffusers import StableDiffusionPipeline

        pipe = StableDiffusionPipeline.from_pretrained(
            ckpt,
            torch_dtype=torch.float16 if selected_device.type == "cuda" else torch.float32,
        ).to(selected_device)
        pretrained_st = pipe.unet.state_dict()
        compressed = {"unet": {}}
        if "modifier_token" in st:
            compressed["modifier_token"] = st["modifier_token"]
        source_state = st["unet"]
    else:
        pretrained_st = torch.load(ckpt, map_location="cpu", weights_only=False)["state_dict"]
        compressed = {"state_dict": {}}
        if "embed" in st.get("state_dict", {}):
            compressed["state_dict"]["embed"] = st["state_dict"]["embed"]
        source_state = st["state_dict"]

    for name, value in source_state.items():
        if "to_k" in name or "to_v" in name:
            delta_w = value.to(selected_device) - pretrained_st[name].to(selected_device)
            u_part, v_part = _compress_matrix(delta_w, compression_ratio)
            compressed_key = "unet" if diffuser else "state_dict"
            compressed[compressed_key][name] = {"u": u_part.cpu(), "v": v_part.cpu()}
        else:
            compressed_key = "unet" if diffuser else "state_dict"
            compressed[compressed_key][name] = value

    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(compressed, output_path)
    return output_path

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compress a Custom Diffusion delta with a low-rank SVD factorization.")
    parser.add_argument("--delta-ckpt", required=True, help="Path to the delta checkpoint to compress.")
    parser.add_argument("--ckpt", required=True, help="Path to the matching pretrained checkpoint or model id.")
    parser.add_argument("--diffuser", action="store_true", help="Treat the delta as a diffusers-style checkpoint.")
    parser.add_argument("--compression-ratio", type=float, default=0.6, help="Fraction of singular-value mass to keep.")
    parser.add_argument("--device", default="cuda", help="Device to use for the SVD and base-model comparison.")
    parser.add_argument("--output", default=None, help="Optional explicit output file path.")
    args = parser.parse_args(list(argv) if argv is not None else None)
    output = compress(args.delta_ckpt, args.ckpt, args.diffuser, args.compression_ratio, args.device, args.output)
    print(output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
