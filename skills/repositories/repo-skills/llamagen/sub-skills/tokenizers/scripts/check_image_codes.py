#!/usr/bin/env python3
"""Decode a saved tokenizer code tensor and save a preview grid."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Mapping

import numpy as np
import torch
from torchvision.utils import save_image


def load_codes(code_path: str) -> np.ndarray:
    loaded = np.load(code_path, allow_pickle=False)
    if isinstance(loaded, np.lib.npyio.NpzFile):
        if "arr_0" in loaded.files:
            return loaded["arr_0"]
        if len(loaded.files) == 1:
            return loaded[loaded.files[0]]
        raise ValueError(f"expected a single array in {code_path}, found {loaded.files}")
    return loaded


def load_weight(checkpoint_path: str) -> Mapping[str, torch.Tensor]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    if not isinstance(checkpoint, Mapping):
        raise ValueError(f"checkpoint {checkpoint_path} is not a mapping/state dict")
    for key in ("ema", "model", "state_dict"):
        value = checkpoint.get(key)
        if isinstance(value, Mapping):
            return value
    return checkpoint


def normalize_codes(codes_np: np.ndarray, tokens_per_image: int) -> torch.Tensor:
    codes = torch.from_numpy(np.asarray(codes_np)).long()
    if codes.ndim == 1:
        codes = codes.unsqueeze(0)
    elif codes.ndim == 2:
        pass
    elif codes.ndim == 3 and codes.shape[0] == 1:
        # LlamaGen cache probes sometimes keep a singleton image dimension plus
        # an augmentation axis such as [1, 2, tokens] or [1, 10, tokens].
        codes = codes.reshape(codes.shape[1], codes.shape[2])
    else:
        raise ValueError(
            "expected codes shaped [tokens], [batch, tokens], or [1, num_aug, tokens]; "
            f"got {tuple(codes.shape)}"
        )

    if codes.shape[1] != tokens_per_image:
        raise ValueError(
            f"expected {tokens_per_image} tokens per image for the requested image/downsample size; "
            f"got {codes.shape[1]} tokens per row"
        )
    return codes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=str, default=".", help="LlamaGen checkout root to add to sys.path")
    parser.add_argument("--code-path", type=str, required=True)
    parser.add_argument("--output-path", type=str, default="sample_image_code.png")
    parser.add_argument("--nrow", type=int, default=None)
    parser.add_argument("--vq-model", type=str, default="VQ-16")
    parser.add_argument("--vq-ckpt", type=str, required=True, help="ckpt path for vq model")
    parser.add_argument("--codebook-size", type=int, default=16384, help="codebook size for vector quantization")
    parser.add_argument("--codebook-embed-dim", type=int, default=8, help="codebook dimension for vector quantization")
    parser.add_argument("--image-size", type=int, choices=[256, 384, 448, 512], default=256)
    parser.add_argument("--downsample-size", type=int, choices=[8, 16], default=16)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    sys.path.insert(0, repo_root.as_posix())
    from tokenizer.tokenizer_image.vq_model import VQ_models  # noqa: PLC0415

    if args.vq_model not in VQ_models:
        available = ", ".join(sorted(VQ_models))
        raise ValueError(f"unknown --vq-model {args.vq_model!r}; available models: {available}")

    torch.manual_seed(args.seed)
    torch.set_grad_enabled(False)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = VQ_models[args.vq_model](
        codebook_size=args.codebook_size,
        codebook_embed_dim=args.codebook_embed_dim,
    )
    model.to(device)
    model.eval()
    model.load_state_dict(load_weight(args.vq_ckpt), strict=False)

    latent_size = args.image_size // args.downsample_size
    tokens_per_image = latent_size * latent_size
    codes = normalize_codes(load_codes(args.code_path), tokens_per_image).to(device)
    qzshape = (codes.shape[0], args.codebook_embed_dim, latent_size, latent_size)
    index_sample = codes.reshape(-1)
    samples = model.decode_code(index_sample, qzshape).cpu()

    output_path = Path(args.output_path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nrow = args.nrow if args.nrow is not None else max(1, min(codes.shape[0], 4))
    save_image(samples, output_path.as_posix(), nrow=nrow, normalize=True, value_range=(-1, 1))
    print(f"Saved reconstructed image grid to {output_path} (nrow={nrow}, codes_shape={tuple(codes.shape)})")


if __name__ == "__main__":
    main()
