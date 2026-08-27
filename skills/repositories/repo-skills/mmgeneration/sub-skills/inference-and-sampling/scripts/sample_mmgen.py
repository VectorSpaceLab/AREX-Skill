#!/usr/bin/env python
"""Run a safe MMGeneration sampling workflow from a config and checkpoint.

Supported modes:
- unconditional: sample_from_noise for GAN-like models
- conditional: sample_from_noise with labels
- translation: sample_img2img_model for Pix2Pix/CycleGAN-style models
- ddpm: sample_ddpm_model for diffusion models

The script saves the raw tensor or output dict as `.pt` and, when possible,
also writes a small preview image grid.

Example:
    python sample_mmgen.py configs/dcgan/dcgan_celeba-cropped_64_b128x1_300k.py \
        checkpoint.pth --mode unconditional --out-dir out --num-samples 8
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import torch
from mmcv import Config, DictAction
from torchvision.utils import save_image

from mmgen.apis import (init_model, sample_conditional_model,
                        sample_ddpm_model, sample_img2img_model,
                        sample_unconditional_model)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Sample from an MMGeneration config and checkpoint')
    parser.add_argument('config', help='config file path')
    parser.add_argument('checkpoint', help='checkpoint file path')
    parser.add_argument(
        '--mode',
        choices=['unconditional', 'conditional', 'translation', 'ddpm'],
        default='unconditional',
        help='which public sampling API to call')
    parser.add_argument(
        '--device',
        default='auto',
        help=('device to use; pass cpu, cuda:0, or auto. auto selects cuda:0 '
              'when CUDA is available, otherwise cpu'))
    parser.add_argument(
        '--out-dir',
        default='mmgeneration-samples',
        help='directory where .pt and preview files are written')
    parser.add_argument(
        '--save-name',
        default=None,
        help='optional output stem; defaults to the selected mode')
    parser.add_argument(
        '--num-samples',
        type=int,
        default=16,
        help='total number of samples to request for tensor-returning modes')
    parser.add_argument(
        '--num-batches',
        type=int,
        default=4,
        help='batch count passed to the sampling helper')
    parser.add_argument(
        '--sample-model',
        choices=['ema', 'orig'],
        default='ema',
        help='which model branch to use when both are available')
    parser.add_argument(
        '--label',
        type=int,
        nargs='+',
        default=None,
        help='label(s) for conditional sampling')
    parser.add_argument(
        '--image-path',
        default=None,
        help='input image for translation sampling')
    parser.add_argument(
        '--target-domain',
        default=None,
        help='target domain for translation sampling')
    parser.add_argument(
        '--same-noise',
        action='store_true',
        help='use the same initial noise tensor for DDPM batches')
    parser.add_argument(
        '--cfg-options',
        nargs='+',
        action=DictAction,
        help='MMCV-style overrides merged into the config before loading')
    parser.add_argument(
        '--sample-cfg',
        nargs='+',
        action=DictAction,
        help='extra kwargs forwarded to the selected sampling function')
    return parser.parse_args()


def resolve_device(device: str) -> str:
    if device == 'auto':
        return 'cuda:0' if torch.cuda.is_available() else 'cpu'
    return device


def save_tensor_or_dict(output: Any, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    pt_path = out_dir / f'{stem}.pt'
    torch.save(output, pt_path)
    print(f'saved: {pt_path}')

    if isinstance(output, dict):
        print(f'dict keys: {list(output.keys())[:10]}')
        return

    if not isinstance(output, torch.Tensor):
        print(f'unsupported output type for preview: {type(output)}')
        return

    preview = output.detach().cpu()
    if preview.dim() == 3:
        preview = preview.unsqueeze(0)
    if preview.size(1) == 3:
        preview = preview[:, [2, 1, 0], ...]
    preview = ((preview + 1) / 2).clamp_(0, 1)
    png_path = out_dir / f'{stem}.png'
    save_image(preview, png_path, nrow=min(preview.shape[0], 4))
    print(f'saved: {png_path}')


def main() -> int:
    args = parse_args()
    cfg = Config.fromfile(args.config)
    if args.cfg_options is not None:
        cfg.merge_from_dict(args.cfg_options)

    device = resolve_device(args.device)
    model = init_model(cfg, checkpoint=args.checkpoint, device=device)

    sample_cfg = args.sample_cfg or {}
    out_dir = Path(args.out_dir)
    stem = args.save_name or args.mode

    if args.mode == 'unconditional':
        output = sample_unconditional_model(
            model,
            num_samples=args.num_samples,
            num_batches=args.num_batches,
            sample_model=args.sample_model,
            **sample_cfg)
    elif args.mode == 'conditional':
        label: Any = args.label
        if label is not None and len(label) > 1:
            args.num_samples = len(label)
        if label is not None and len(label) == 1:
            label = label[0]
        output = sample_conditional_model(
            model,
            num_samples=args.num_samples,
            num_batches=args.num_batches,
            sample_model=args.sample_model,
            label=label,
            **sample_cfg)
    elif args.mode == 'translation':
        if args.image_path is None:
            raise ValueError('--image-path is required for translation mode')
        output = sample_img2img_model(
            model,
            args.image_path,
            target_domain=args.target_domain,
            **sample_cfg)
    else:
        output = sample_ddpm_model(
            model,
            num_samples=args.num_samples,
            num_batches=args.num_batches,
            sample_model=args.sample_model,
            same_noise=args.same_noise,
            **sample_cfg)

    save_tensor_or_dict(output, out_dir, stem)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
