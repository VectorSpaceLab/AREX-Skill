#!/usr/bin/env python3
"""Activation-map visualization helper for Torchreid.

Preview mode is the default. Pass --run to execute the dataset-backed
visualization pass.
"""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
GRID_SPACING = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Preview or run Torchreid activation-map visualization. The script '
            'does nothing expensive unless --run is supplied.'
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--root', help='Dataset root used for a real run.')
    parser.add_argument('-d', '--dataset', default='market1501', help='Dataset key.')
    parser.add_argument('-m', '--model', default='osnet_x1_0', help='Model key.')
    parser.add_argument(
        '--weights',
        help='Local checkpoint used for a real run. No download is attempted.',
    )
    parser.add_argument('--save-dir', default='log', help='Visualization output directory.')
    parser.add_argument('--height', type=int, default=256, help='Image height.')
    parser.add_argument('--width', type=int, default=128, help='Image width.')
    parser.add_argument(
        '--device',
        default='cpu',
        help='Device string for the real run. Keep cpu for the safest preview workflow.',
    )
    parser.add_argument(
        '--run',
        action='store_true',
        help='Execute the dataset-backed visualization instead of previewing.',
    )
    return parser.parse_args()


def preview_run(args: argparse.Namespace) -> int:
    preview = {
        'run_requested': False,
        'model': args.model,
        'dataset': args.dataset,
        'root': args.root,
        'weights': args.weights,
        'save_dir': args.save_dir,
        'height': args.height,
        'width': args.width,
        'device': args.device,
        'note': 'Re-run with --run to execute the full activation-map workflow.',
    }
    if args.weights:
        preview['weights_exists'] = Path(args.weights).expanduser().is_file()
    print(json.dumps(preview, indent=2, sort_keys=True))
    return 0


def visactmap(
    model,
    test_loader,
    save_dir,
    width,
    height,
    use_gpu,
    img_mean=None,
    img_std=None,
):
    import os.path as osp

    import cv2
    import numpy as np
    from torch.nn import functional as F
    from torchreid.utils import mkdir_if_missing

    if img_mean is None or img_std is None:
        img_mean = IMAGENET_MEAN
        img_std = IMAGENET_STD

    model.eval()

    for target in list(test_loader.keys()):
        data_loader = test_loader[target]['query']
        actmap_dir = osp.join(save_dir, 'actmap_' + target)
        mkdir_if_missing(actmap_dir)
        print(f'Visualizing activation maps for {target} ...')

        for batch_idx, data in enumerate(data_loader):
            imgs, paths = data['img'], data['impath']
            if use_gpu:
                imgs = imgs.cuda()

            try:
                outputs = model(imgs, return_featuremaps=True)
            except TypeError as exc:
                raise TypeError(
                    'forward() got unexpected keyword argument "return_featuremaps". '
                    'Please add return_featuremaps as an input argument to forward(). '
                    'When return_featuremaps=True, return feature maps only.'
                ) from exc

            if outputs.dim() != 4:
                raise ValueError(
                    'The model output is supposed to have shape of (b, c, h, w), '
                    f'i.e. 4 dimensions, but got {outputs.dim()} dimensions. '
                    'Please make sure you set the model output at eval mode to be the '
                    'last convolutional feature maps.'
                )

            outputs = (outputs**2).sum(1)
            b, h, w = outputs.size()
            outputs = outputs.view(b, h * w)
            outputs = F.normalize(outputs, p=2, dim=1)
            outputs = outputs.view(b, h, w)

            if use_gpu:
                imgs, outputs = imgs.cpu(), outputs.cpu()

            for j in range(outputs.size(0)):
                path = paths[j]
                imname = osp.basename(osp.splitext(path)[0])

                img = imgs[j, ...]
                for t, m, s in zip(img, img_mean, img_std):
                    t.mul_(s).add_(m).clamp_(0, 1)
                img_np = np.uint8(np.floor(img.numpy() * 255))
                img_np = img_np.transpose((1, 2, 0))

                am = outputs[j, ...].numpy()
                am = cv2.resize(am, (width, height))
                am = 255 * (am - np.min(am)) / (np.max(am) - np.min(am) + 1e-12)
                am = np.uint8(np.floor(am))
                am = cv2.applyColorMap(am, cv2.COLORMAP_JET)

                overlapped = img_np * 0.3 + am * 0.7
                overlapped[overlapped > 255] = 255
                overlapped = overlapped.astype(np.uint8)

                grid_img = 255 * np.ones(
                    (height, 3 * width + 2 * GRID_SPACING, 3), dtype=np.uint8
                )
                grid_img[:, :width, :] = img_np[:, :, ::-1]
                grid_img[:, width + GRID_SPACING : 2 * width + GRID_SPACING, :] = am
                grid_img[:, 2 * width + 2 * GRID_SPACING :, :] = overlapped
                cv2.imwrite(osp.join(actmap_dir, imname + '.jpg'), grid_img)

            if (batch_idx + 1) % 10 == 0:
                print(f'- done batch {batch_idx + 1}/{len(data_loader)}')

    print(f'Done. Images have been saved to "{save_dir}" ...')


def run_visualization(args: argparse.Namespace) -> int:
    if not args.root:
        raise SystemExit('--root is required when using --run')
    if not args.weights:
        raise SystemExit('--weights is required when using --run')

    root = Path(args.root).expanduser()
    weights = Path(args.weights).expanduser()
    if not root.exists():
        raise SystemExit(f'Dataset root not found: {root}')
    if not weights.is_file():
        raise SystemExit(
            f'Local checkpoint not found: {weights}. '
            'Provide a verified file path to avoid downloads.'
        )

    import torch
    import torchreid
    from torchreid.utils import load_pretrained_weights

    use_gpu = args.device.startswith('cuda')
    if use_gpu and not torch.cuda.is_available():
        raise SystemExit(
            f'CUDA device {args.device!r} was requested, but torch.cuda.is_available() is False.'
        )

    datamanager = torchreid.data.ImageDataManager(
        root=str(root),
        sources=args.dataset,
        height=args.height,
        width=args.width,
        batch_size_train=100,
        batch_size_test=100,
        transforms=None,
        train_sampler='SequentialSampler',
    )
    test_loader = datamanager.test_loader

    model = torchreid.models.build_model(
        name=args.model,
        num_classes=datamanager.num_train_pids,
        use_gpu=use_gpu,
        pretrained=False,
    )
    if use_gpu:
        model = model.cuda()
    load_pretrained_weights(model, str(weights))

    try:
        forward_params = inspect.signature(model.forward).parameters
    except (TypeError, ValueError):
        forward_params = {}
    if 'return_featuremaps' not in forward_params:
        raise SystemExit(
            'forward() does not accept return_featuremaps=True. '
            'Choose an OSNet-family model or add that support before running actmap.'
        )

    visactmap(
        model,
        test_loader,
        args.save_dir,
        args.width,
        args.height,
        use_gpu,
    )
    return 0


def main() -> int:
    args = parse_args()
    if not args.run:
        return preview_run(args)
    return run_visualization(args)


if __name__ == '__main__':
    raise SystemExit(main())
