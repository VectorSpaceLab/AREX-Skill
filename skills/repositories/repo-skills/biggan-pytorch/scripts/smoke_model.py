#!/usr/bin/env python3
"""Tiny CUDA generator smoke test for BigGAN or BigGANdeep.

This allocates a deliberately small 32x32 model and performs one inference
forward pass. It does not load weights, download data, or write files.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import torch


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--repo-root', type=Path, required=True)
    p.add_argument('--model', choices=['BigGAN', 'BigGANdeep'], default='BigGAN')
    args = p.parse_args()
    sys.path.insert(0, str(args.repo_root.resolve()))
    if not torch.cuda.is_available():
        print('CUDA unavailable; smoke test not run')
        return 2
    module = __import__(args.model)
    dim_z = 16 if args.model == 'BigGAN' else 32
    config = dict(G_ch=16, G_depth=1, dim_z=dim_z, bottom_width=4,
                  resolution=32, G_kernel_size=3, G_attn='0', n_classes=10,
                  num_G_SVs=1, num_G_SV_itrs=1, G_shared=True, shared_dim=16,
                  hier=(args.model == 'BigGANdeep'), cross_replica=False, mybn=False,
                  G_activation=torch.nn.ReLU(inplace=False), G_lr=5e-5,
                  G_B1=0.0, G_B2=0.999, adam_eps=1e-8, BN_eps=1e-5,
                  SN_eps=1e-12, G_mixed_precision=False, G_fp16=False,
                  G_init='ortho', skip_init=False, no_optim=True, G_param='SN',
                  norm_style='bn')
    generator = module.Generator(**config).cuda().eval()
    z = torch.randn(2, generator.dim_z, device='cuda')
    y = generator.shared(torch.randint(0, 10, (2,), device='cuda'))
    out = generator(z, y)
    expected = (2, 3, 32, 32)
    print(f'model={args.model} output_shape={tuple(out.shape)} device={out.device}')
    return 0 if tuple(out.shape) == expected else 1


if __name__ == '__main__':
    raise SystemExit(main())
