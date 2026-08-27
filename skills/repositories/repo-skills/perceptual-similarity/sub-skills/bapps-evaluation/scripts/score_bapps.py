#!/usr/bin/env python3
"""Score BAPPS-style 2AFC or JND splits with LPIPS-style metrics.

This helper avoids the stock JND loader bug and uses a modern SSIM fallback,
so it remains usable on current environments.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SKILL_ROOT = Path(__file__).resolve().parents[3]
ROOT_SCRIPTS = SKILL_ROOT / "scripts"
if str(ROOT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ROOT_SCRIPTS))

import numpy as np
import torch
from tqdm import tqdm

from bapps_common import accuracy_2afc, ap_jnd, load_bapps_dataset, make_loader
from lpips_common import l2_distance_batch, make_lpips_model, ssim_distance_batch


DEFAULT_2AFC_SPLITS = ["val/traditional", "val/cnn", "val/superres", "val/deblur", "val/color", "val/frameinterp"]
DEFAULT_JND_SPLITS = ["val/traditional", "val/cnn"]


def build_metric(args):
    metric_name = args.model.lower()
    device = torch.device("cpu")
    metric = None
    if metric_name in {"lpips", "baseline"}:
        metric, device = make_lpips_model(
            model=metric_name,
            net=args.net,
            version=args.version,
            use_gpu=args.use_gpu,
            pnet_rand=args.from_scratch,
            pnet_tune=args.train_trunk,
            spatial=False,
            model_path=str(args.model_path) if args.model_path else None,
            verbose=False,
        )
    return metric_name, metric, device


def score_split(args, metric_name, metric, device, split_name: str) -> float:
    dataset = load_bapps_dataset(
        args.dataset_root,
        args.dataset_mode,
        [split_name],
        load_size=args.load_size,
    )
    loader = make_loader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers)

    if args.dataset_mode == "2afc":
        d0s, d1s, judges = [], [], []
        for batch in tqdm(loader, desc=split_name):
            ref = batch["ref"].to(device)
            p0 = batch["p0"].to(device)
            p1 = batch["p1"].to(device)
            judge = batch["judge"].detach().cpu().numpy().reshape(-1)
            if metric_name in {"lpips", "baseline"}:
                d0 = metric(ref, p0)
                d1 = metric(ref, p1)
            elif metric_name == "l2":
                d0 = l2_distance_batch(ref, p0, colorspace=args.colorspace, use_gpu=args.use_gpu)
                d1 = l2_distance_batch(ref, p1, colorspace=args.colorspace, use_gpu=args.use_gpu)
            elif metric_name == "ssim":
                d0 = ssim_distance_batch(ref, p0, colorspace=args.colorspace, use_gpu=args.use_gpu)
                d1 = ssim_distance_batch(ref, p1, colorspace=args.colorspace, use_gpu=args.use_gpu)
            else:
                raise ValueError(f"unsupported model: {metric_name}")
            d0s.extend(d0.detach().cpu().reshape(-1).tolist())
            d1s.extend(d1.detach().cpu().reshape(-1).tolist())
            judges.extend(judge.tolist())
        score, _ = accuracy_2afc(np.asarray(d0s), np.asarray(d1s), np.asarray(judges))
        print(f"  Dataset [{split_name}]: {100.0 * score:.2f}")
        return score

    if args.dataset_mode == "jnd":
        distances, sames = [], []
        for batch in tqdm(loader, desc=split_name):
            p0 = batch["p0"].to(device)
            p1 = batch["p1"].to(device)
            same = batch["same"].detach().cpu().numpy().reshape(-1)
            if metric_name in {"lpips", "baseline"}:
                dist = metric(p0, p1)
            elif metric_name == "l2":
                dist = l2_distance_batch(p0, p1, colorspace=args.colorspace, use_gpu=args.use_gpu)
            elif metric_name == "ssim":
                dist = ssim_distance_batch(p0, p1, colorspace=args.colorspace, use_gpu=args.use_gpu)
            else:
                raise ValueError(f"unsupported model: {metric_name}")
            distances.extend(dist.detach().cpu().reshape(-1).tolist())
            sames.extend(same.tolist())
        score, _ = ap_jnd(np.asarray(distances), np.asarray(sames))
        print(f"  Dataset [{split_name}]: {100.0 * score:.2f}")
        return score

    raise ValueError(f"unsupported dataset_mode: {args.dataset_mode}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--dataset_mode", choices=["2afc", "jnd"], default="2afc", help="Which BAPPS split family to evaluate.")
    parser.add_argument("--dataset_root", type=Path, default=Path("dataset"), help="Root containing the BAPPS branches.")
    parser.add_argument("--datasets", nargs="+", default=None, help="Split names such as val/traditional or tiny.")
    parser.add_argument("--model", choices=["lpips", "baseline", "l2", "ssim"], default="lpips", help="Metric to score.")
    parser.add_argument("--net", choices=["squeeze", "alex", "vgg"], default="alex", help="LPIPS backbone used by the learned metric.")
    parser.add_argument("--colorspace", choices=["Lab", "RGB"], default="Lab", help="Colorspace used by L2 and SSIM-style metrics.")
    parser.add_argument("--batch_size", type=int, default=50, help="Batch size for the data loader.")
    parser.add_argument("--num_workers", type=int, default=0, help="Data-loader worker count.")
    parser.add_argument("--load_size", type=int, default=64, help="Resize shorter side to this value before scoring.")
    parser.add_argument("--use_gpu", action="store_true", help="Use CUDA when available.")
    parser.add_argument("--gpu_ids", type=int, nargs="+", default=[0], help="CUDA device ids used by the LPIPS model.")
    parser.add_argument("--version", default="0.1", help="LPIPS weight version.")
    parser.add_argument("--model_path", type=Path, default=None, help="Optional custom LPIPS weight file.")
    parser.add_argument("--from_scratch", action="store_true", help="Use random LPIPS trunk weights.")
    parser.add_argument("--train_trunk", action="store_true", help="Allow tuning the LPIPS trunk.")
    args = parser.parse_args(argv)

    if args.datasets is None:
        args.datasets = DEFAULT_2AFC_SPLITS if args.dataset_mode == "2afc" else DEFAULT_JND_SPLITS

    metric_name, metric, device = build_metric(args)

    if metric_name in {"l2", "ssim"} and args.batch_size != 1:
        print(f"note: {metric_name} works best with batch size 1; the helper will still iterate safely.")

    total = []
    for split_name in args.datasets:
        total.append(score_split(args, metric_name, metric, device, split_name))
    if total:
        print(f"Mean over {len(total)} split(s): {100.0 * float(np.mean(total)):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
