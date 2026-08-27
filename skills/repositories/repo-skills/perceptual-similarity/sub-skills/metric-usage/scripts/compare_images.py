#!/usr/bin/env python3
"""Compare image pairs or image directories with LPIPS-style metrics.

Modes:
- pair: compare two explicit images.
- dir-pair: compare matching filenames in two directories.
- all-pairs: compare all consecutive pairs, or all N(N-1)/2 pairs when enabled.

The script defaults to the bundled example assets so it can smoke-test without
any external checkout.
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
from PIL import Image

from lpips_common import (
    image_to_tensor,
    l2_distance_batch,
    lpips_distance,
    make_lpips_model,
    resolve_example_path,
    ssim_distance_batch,
)


DEFAULT_PAIR_0 = resolve_example_path("ex_ref.png")
DEFAULT_PAIR_1 = resolve_example_path("ex_p0.png")
DEFAULT_DIR_0 = resolve_example_path("ex_dir0")
DEFAULT_DIR_1 = resolve_example_path("ex_dir1")
DEFAULT_DIR_ALL = resolve_example_path("ex_dir_pair")

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".ppm", ".PNG", ".JPG", ".JPEG", ".BMP", ".PPM"}


def list_image_files(folder: Path) -> list[Path]:
    files = [path for path in sorted(folder.rglob("*")) if path.is_file() and path.suffix in SUPPORTED_IMAGE_EXTENSIONS]
    if not files:
        raise FileNotFoundError(f"no supported images found in {folder}")
    return files


def save_heatmap(distance_map: torch.Tensor, path: Path) -> None:
    array = distance_map.detach().cpu().float().squeeze().numpy()
    array = np.asarray(array)
    array = array - array.min()
    if array.max() > 0:
        array = array / array.max()
    image = Image.fromarray((array * 255).astype(np.uint8))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def scalarize(distance: torch.Tensor) -> float:
    return float(distance.detach().cpu().float().mean().item())


def compare_one(metric_name: str, args, model, device, path0: Path, path1: Path):
    img0 = image_to_tensor(path0).to(device)
    img1 = image_to_tensor(path1).to(device)

    if metric_name in {"lpips", "baseline"}:
        distance = lpips_distance(model, img0, img1)
        value = scalarize(distance)
        print(f"Distance: {value:.3f}")
        if args.spatial and args.spatial_map_out:
            save_heatmap(distance[0, 0], Path(args.spatial_map_out))
            print(f"Spatial map: {args.spatial_map_out}")
        return value

    if metric_name == "l2":
        distance = l2_distance_batch(img0, img1, colorspace=args.colorspace, use_gpu=args.use_gpu)
    elif metric_name == "ssim":
        distance = ssim_distance_batch(img0, img1, colorspace=args.colorspace, use_gpu=args.use_gpu)
    else:
        raise ValueError(f"unsupported metric: {metric_name}")

    value = scalarize(distance)
    print(f"Distance: {value:.3f}")
    return value


def compare_dir_pair(metric_name: str, args, model, device, dir0: Path, dir1: Path) -> int:
    files0 = {path.relative_to(dir0).as_posix(): path for path in list_image_files(dir0)}
    files1 = {path.relative_to(dir1).as_posix(): path for path in list_image_files(dir1)}
    shared = sorted(files0.keys() & files1.keys())
    if not shared:
        raise ValueError(f"no shared image names found between {dir0} and {dir1}")

    lines = []
    for rel in shared:
        value = compare_one(metric_name, args, model, device, files0[rel], files1[rel])
        lines.append(f"{rel}: {value:.6f}\n")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text("".join(lines), encoding="utf-8")
    return 0


def compare_all_pairs(metric_name: str, args, model, device, directory: Path) -> int:
    files = list_image_files(directory)
    if args.N is not None:
        files = files[: args.N]
    if len(files) < 2:
        raise ValueError(f"need at least two images in {directory} for all-pairs comparison")

    values = []
    lines = []
    for index, path0 in enumerate(files[:-1]):
        if args.all_pairs:
            targets = files[index + 1 :]
        else:
            targets = [files[index + 1]]
        for path1 in targets:
            value = compare_one(metric_name, args, model, device, path0, path1)
            values.append(value)
            lines.append(f"({path0.name},{path1.name}): {value:.6f}\n")

    avg = float(np.mean(values))
    stderr = float(np.std(values) / np.sqrt(len(values))) if values else 0.0
    print(f"Avg: {avg:.5f} +/- {stderr:.5f}")
    lines.append(f"Avg: {avg:.6f} +/- {stderr:.6f}\n")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text("".join(lines), encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--mode", choices=["pair", "dir-pair", "all-pairs"], default="pair", help="Which comparison workflow to run.")
    parser.add_argument("--metric", choices=["lpips", "baseline", "l2", "ssim"], default="lpips", help="Metric to compute.")
    parser.add_argument("--net", choices=["squeeze", "alex", "vgg"], default="alex", help="Backbone used for LPIPS/baseline.")
    parser.add_argument("--version", default="0.1", help="LPIPS weight version.")
    parser.add_argument("--model_path", default=None, help="Optional path to a custom LPIPS weight file.")
    parser.add_argument("--path0", type=Path, default=DEFAULT_PAIR_0, help="First image for pair mode.")
    parser.add_argument("--path1", type=Path, default=DEFAULT_PAIR_1, help="Second image for pair mode.")
    parser.add_argument("--dir0", type=Path, default=DEFAULT_DIR_0, help="First directory for dir-pair mode.")
    parser.add_argument("--dir1", type=Path, default=DEFAULT_DIR_1, help="Second directory for dir-pair mode.")
    parser.add_argument("--dir", dest="dir_single", type=Path, default=DEFAULT_DIR_ALL, help="Directory for all-pairs mode.")
    parser.add_argument("--out", type=Path, default=None, help="Optional output file for directory modes or pair mode.")
    parser.add_argument("--use_gpu", action="store_true", help="Use CUDA when available.")
    parser.add_argument("--spatial", action="store_true", help="Return a spatial map for pair mode.")
    parser.add_argument("--spatial_map_out", type=Path, default=None, help="Optional path for the pair-mode spatial map image.")
    parser.add_argument("--all-pairs", action="store_true", help="For all-pairs mode, compare all N(N-1)/2 pairs instead of only consecutive pairs.")
    parser.add_argument("-N", type=int, default=None, help="Limit the number of files used in all-pairs mode.")
    parser.add_argument("--colorspace", choices=["Lab", "RGB"], default="Lab", help="Colorspace used by L2 and SSIM-style metrics.")
    parser.add_argument("--from_scratch", action="store_true", help="Use random LPIPS trunk weights instead of pretrained trunk weights.")
    parser.add_argument("--train_trunk", action="store_true", help="Allow tuning the LPIPS trunk when constructing the model.")
    args = parser.parse_args(argv)

    metric_name = args.metric.lower()
    device = torch.device("cpu")
    model = None
    if metric_name in {"lpips", "baseline"}:
        model, device = make_lpips_model(
            model=metric_name,
            net=args.net,
            version=args.version,
            use_gpu=args.use_gpu,
            pnet_rand=args.from_scratch,
            pnet_tune=args.train_trunk,
            spatial=args.spatial,
            model_path=str(args.model_path) if args.model_path else None,
            verbose=False,
        )

    if args.mode == "pair":
        value = compare_one(metric_name, args, model, device, args.path0, args.path1)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(f"Distance: {value:.6f}\n", encoding="utf-8")
        return 0
    if args.mode == "dir-pair":
        return compare_dir_pair(metric_name, args, model, device, args.dir0, args.dir1)
    return compare_all_pairs(metric_name, args, model, device, args.dir_single)


if __name__ == "__main__":
    raise SystemExit(main())
