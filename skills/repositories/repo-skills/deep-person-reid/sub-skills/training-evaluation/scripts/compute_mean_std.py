#!/usr/bin/env python3
"""Safe Torchreid image-dataset mean/std helper.

Default behavior is prerequisite checking only. Add --compute to construct an
ImageDataManager and iterate over local training images. No network access is
performed by this wrapper before prerequisite checks pass.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

IMAGE_DATASETS = [
    "market1501",
    "cuhk03",
    "dukemtmcreid",
    "msmt17",
    "viper",
    "grid",
    "cuhk01",
    "ilids",
    "sensereid",
    "prid",
    "cuhk02",
    "university1652",
    "cuhksysu",
]

# Each dataset maps to one or more alternative marker groups. A group passes
# only when every relative path in that group exists under root.
MARKERS: Dict[str, List[Tuple[str, ...]]] = {
    "market1501": [
        (
            "market1501/Market-1501-v15.09.15/bounding_box_train",
            "market1501/Market-1501-v15.09.15/query",
            "market1501/Market-1501-v15.09.15/bounding_box_test",
        )
    ],
    "dukemtmcreid": [
        (
            "dukemtmc-reid/DukeMTMC-reID/bounding_box_train",
            "dukemtmc-reid/DukeMTMC-reID/query",
            "dukemtmc-reid/DukeMTMC-reID/bounding_box_test",
        )
    ],
    "msmt17": [
        (
            "msmt17/MSMT17_V1/train",
            "msmt17/MSMT17_V1/test",
            "msmt17/MSMT17_V1/list_train.txt",
            "msmt17/MSMT17_V1/list_query.txt",
            "msmt17/MSMT17_V1/list_gallery.txt",
        ),
        (
            "msmt17/MSMT17_V2/train",
            "msmt17/MSMT17_V2/test",
            "msmt17/MSMT17_V2/list_train.txt",
            "msmt17/MSMT17_V2/list_query.txt",
            "msmt17/MSMT17_V2/list_gallery.txt",
        ),
    ],
    "cuhk03": [
        (
            "cuhk03/cuhk03_release",
            "cuhk03/cuhk03_new_protocol_config_detected.mat",
            "cuhk03/cuhk03_new_protocol_config_labeled.mat",
        )
    ],
    "viper": [("viper/VIPeR/cam_a", "viper/VIPeR/cam_b")],
    "grid": [("grid/underground_reid/probe", "grid/underground_reid/gallery")],
    "cuhk01": [("cuhk01/campus",)],
    "ilids": [("ilids/i-LIDS_Pedestrian/Persons",)],
    "sensereid": [("sensereid/SenseReID/test_probe", "sensereid/SenseReID/test_gallery")],
    "prid": [("prid2011/prid_2011/single_shot", "prid2011/prid_2011/multi_shot")],
    "cuhk02": [("cuhk02/Dataset",)],
    "cuhksysu": [("cuhksysu/cropped_images",)],
}


def marker_status(root: Path, source: str) -> Tuple[bool, List[str]]:
    groups = MARKERS.get(source)
    if not groups:
        return False, [f"No built-in prerequisite marker table for {source!r}; use --allow-unchecked only if the dataset is already registered and local."]
    missing_reports: List[str] = []
    for group in groups:
        missing = [rel for rel in group if not (root / rel).exists()]
        if not missing:
            return True, []
        missing_reports.append(", ".join(missing))
    return False, missing_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check prerequisites and optionally compute Torchreid image dataset channel mean/std.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("root", nargs="?", help="Parent directory containing ReID dataset folders.")
    parser.add_argument("sources", nargs="*", help="Image dataset key(s), e.g. market1501 dukemtmcreid.")
    parser.add_argument("--list-datasets", action="store_true", help="List built-in image dataset keys and exit.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-only", action="store_true", help="Only check local prerequisite paths; this is the default.")
    mode.add_argument("--compute", action="store_true", help="Actually import torchreid and iterate over local train images.")
    parser.add_argument("--allow-unchecked", action="store_true", help="Allow --compute for keys without a marker table or with missing markers. Use only for registered custom/local datasets.")
    parser.add_argument("--height", type=int, default=256, help="Input image height.")
    parser.add_argument("--width", type=int, default=128, help="Input image width.")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for statistics pass.")
    parser.add_argument("--workers", type=int, default=4, help="DataLoader workers; use 0 for debugging.")
    parser.add_argument("--max-batches", type=int, default=0, help="Optional cap for a quick approximate pass; 0 means all batches.")
    return parser


def require_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.list_datasets:
        return
    if not args.root or not args.sources:
        parser.error("root and at least one source dataset are required unless --list-datasets is used.")


def check_prereqs(root: Path, sources: Sequence[str], allow_unchecked: bool = False) -> bool:
    ok_all = True
    print(f"Checking dataset prerequisites under: {root}")
    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return False
    for source in sources:
        if source not in IMAGE_DATASETS:
            print(f"WARNING: {source!r} is not a built-in image dataset key. It may be a custom registered dataset.")
        ok, reports = marker_status(root, source)
        if ok:
            print(f"OK: {source}: expected local markers found")
        elif allow_unchecked:
            print(f"UNCHECKED: {source}: proceeding by request despite missing/unknown markers")
            for report in reports:
                print(f"  missing/unknown marker group: {report}")
        else:
            ok_all = False
            print(f"MISSING: {source}: local prerequisite markers not found")
            for report in reports:
                print(f"  missing marker group: {report}")
    return ok_all


def compute_stats(args: argparse.Namespace) -> int:
    try:
        import torch  # type: ignore
        import torchreid  # type: ignore
    except Exception as exc:
        print("ERROR: --compute requires torch and torchreid to be importable in this environment.", file=sys.stderr)
        print(f"Import error: {exc}", file=sys.stderr)
        return 2

    print("Constructing ImageDataManager for local training data only ...")
    try:
        datamanager = torchreid.data.ImageDataManager(
            root=args.root,
            sources=args.sources if len(args.sources) > 1 else args.sources[0],
            targets=None,
            height=args.height,
            width=args.width,
            batch_size_train=args.batch_size,
            batch_size_test=args.batch_size,
            workers=args.workers,
            transforms=None,
            norm_mean=[0.0, 0.0, 0.0],
            norm_std=[1.0, 1.0, 1.0],
            train_sampler="SequentialSampler",
            use_gpu=False,
        )
    except Exception as exc:
        print("ERROR: failed to construct ImageDataManager. Check dataset layout and registration.", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        return 3

    train_loader = datamanager.train_loader
    mean = torch.zeros(3)
    std = torch.zeros(3)
    n_samples = 0
    n_batches = 0
    print("Computing mean and std over training images ...")
    try:
        for batch in train_loader:
            data = batch["img"]
            batch_size = data.size(0)
            data = data.view(batch_size, data.size(1), -1)
            mean += data.mean(2).sum(0)
            std += data.std(2).sum(0)
            n_samples += batch_size
            n_batches += 1
            if args.max_batches and n_batches >= args.max_batches:
                print(f"Stopped early after --max-batches={args.max_batches}; results are approximate.")
                break
    except Exception as exc:
        print("ERROR: failed while iterating dataset. Try --workers 0 for clearer errors.", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        return 4

    if n_samples == 0:
        print("ERROR: no samples were read from the training loader.", file=sys.stderr)
        return 5

    mean /= n_samples
    std /= n_samples
    print(f"Samples: {n_samples}")
    print(f"Batches: {n_batches}")
    print("Mean: [{}]".format(", ".join(f"{x:.6f}" for x in mean.tolist())))
    print("Std:  [{}]".format(", ".join(f"{x:.6f}" for x in std.tolist())))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_datasets:
        print("Built-in image dataset keys:")
        for key in IMAGE_DATASETS:
            print(f"  - {key}")
        return 0
    require_args(parser, args)

    root = Path(os.path.expanduser(args.root)).resolve()
    prereq_ok = check_prereqs(root, args.sources, allow_unchecked=args.allow_unchecked)
    if not args.compute:
        print("Check-only mode complete. Add --compute to iterate over local training images.")
        return 0 if prereq_ok else 2
    if not prereq_ok and not args.allow_unchecked:
        print("Refusing to compute because prerequisites are missing. Use --allow-unchecked only for known registered/custom local datasets.", file=sys.stderr)
        return 2
    return compute_stats(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
