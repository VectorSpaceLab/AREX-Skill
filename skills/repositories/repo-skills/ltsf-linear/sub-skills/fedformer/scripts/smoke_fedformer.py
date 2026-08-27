#!/usr/bin/env python3
"""Tiny CUDA smoke test for FEDformer synthetic inputs.

This script instantiates the FEDformer model on synthetic tensors and runs one
forward pass for either the Fourier or Wavelets branch. It is intentionally
small so it can be used as a preflight check before a longer GPU run.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny FEDformer forward smoke on CUDA.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument("--repo-root", default=".", help="Repository root containing FEDformer/.")
    parser.add_argument("--version", choices=["Fourier", "Wavelets"], default="Wavelets")
    parser.add_argument("--seq-len", type=int, default=16)
    parser.add_argument("--label-len", type=int, default=8)
    parser.add_argument("--pred-len", type=int, default=8)
    parser.add_argument("--modes", type=int, default=4)
    parser.add_argument("--L", type=int, default=1)
    parser.add_argument("--base", default="legendre")
    parser.add_argument("--cross-activation", default="tanh")
    return parser.parse_args()


def load_model_class(repo_root: Path):
    fedformer_root = repo_root / "FEDformer"
    model_path = fedformer_root / "models" / "FEDformer.py"
    if not model_path.is_file():
        raise SystemExit(f"Expected FEDformer model file at {model_path}")

    if str(fedformer_root) not in sys.path:
        sys.path.insert(0, str(fedformer_root))

    spec = importlib.util.spec_from_file_location("fedformer_model", model_path)
    if spec is None or spec.loader is None:
        raise SystemExit("Could not load FEDformer model module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Model


@dataclass
class Config:
    version: str
    mode_select: str = "random"
    modes: int = 4
    seq_len: int = 16
    label_len: int = 8
    pred_len: int = 8
    output_attention: bool = False
    moving_avg: list[int] = None  # type: ignore[assignment]
    embed_type: int = 0
    enc_in: int = 2
    dec_in: int = 2
    c_out: int = 2
    d_model: int = 16
    n_heads: int = 8
    e_layers: int = 1
    d_layers: int = 1
    d_ff: int = 32
    factor: int = 1
    dropout: float = 0.0
    embed: str = "timeF"
    freq: str = "h"
    activation: str = "gelu"
    L: int = 1
    base: str = "legendre"
    cross_activation: str = "tanh"

    def __post_init__(self):
        if self.moving_avg is None:
            self.moving_avg = [4]


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required for this smoke test.")

    Model = load_model_class(repo_root)
    cfg = Config(
        version=args.version,
        modes=args.modes,
        seq_len=args.seq_len,
        label_len=args.label_len,
        pred_len=args.pred_len,
        L=args.L,
        base=args.base,
        cross_activation=args.cross_activation,
    )
    model = Model(cfg).cuda().eval()

    batch = 2
    x_enc = torch.randn(batch, cfg.seq_len, cfg.enc_in, device="cuda")
    x_mark_enc = torch.randn(batch, cfg.seq_len, 4, device="cuda")
    x_dec = torch.randn(batch, cfg.label_len + cfg.pred_len, cfg.dec_in, device="cuda")
    x_mark_dec = torch.randn(batch, cfg.label_len + cfg.pred_len, 4, device="cuda")

    with torch.no_grad():
        out = model(x_enc, x_mark_enc, x_dec, x_mark_dec)
    if isinstance(out, tuple):
        out = out[0]

    print(f"ok: version={args.version} output_shape={tuple(out.shape)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
