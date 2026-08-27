#!/usr/bin/env python3
"""Print safe SSD.PyTorch training command templates without executing training."""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable


def bool_token(value: str) -> str:
    text = str(value).strip().lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return "true"
    if text in {"0", "false", "f", "no", "n"}:
        return "false"
    raise argparse.ArgumentTypeError("expected true or false")


def quote_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan an ssd.pytorch train.py command without executing it")
    parser.add_argument("--dataset", choices=("VOC", "COCO"), default="VOC")
    parser.add_argument("--dataset-root", required=True, help="VOCdevkit root or COCO root")
    parser.add_argument("--save-folder", default="weights/", help="folder containing base weights and receiving checkpoints")
    parser.add_argument("--basenet", default="vgg16_reducedfc.pth", help="fresh-training VGG base weights filename")
    parser.add_argument("--resume", default=None, help="optional SSD checkpoint path for resume")
    parser.add_argument("--start-iter", type=int, default=0, help="resume iteration")
    parser.add_argument("--cuda", type=bool_token, default="false", help="true or false")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--momentum", type=float, default=0.9)
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    parser.add_argument("--gamma", type=float, default=0.1)
    parser.add_argument("--visdom", type=bool_token, default="false", help="true or false")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cmd = [
        "python",
        "train.py",
        "--dataset",
        args.dataset,
        "--dataset_root",
        args.dataset_root,
        "--save_folder",
        args.save_folder,
        "--batch_size",
        str(args.batch_size),
        "--num_workers",
        str(args.num_workers),
        "--cuda",
        args.cuda,
        "--lr",
        str(args.lr),
        "--momentum",
        str(args.momentum),
        "--weight_decay",
        str(args.weight_decay),
        "--gamma",
        str(args.gamma),
        "--visdom",
        args.visdom,
    ]
    if args.resume:
        cmd.extend(["--resume", args.resume, "--start_iter", str(args.start_iter)])
    else:
        cmd.extend(["--basenet", args.basenet])

    print("Command template:")
    print("  " + quote_join(cmd))
    print("\nBefore execution check:")
    if args.dataset == "VOC":
        print("  - VOC root contains VOC2007 and VOC2012 trainval layout for default training.")
    else:
        print("  - COCO root contains images/trainval35k, annotations/instances_trainval35k.json, and coco_labels.txt.")
        print("  - pycocotools is importable or COCO_ROOT/PythonAPI exists.")
    if args.resume:
        print(f"  - Resume checkpoint exists and matches {args.dataset} model heads: {args.resume}")
        print(f"  - start_iter={args.start_iter} is consistent with the checkpoint and LR schedule.")
    else:
        print(f"  - Fresh-training base weights exist at save_folder/basenet: {args.save_folder.rstrip('/')}/{args.basenet}")
    print("  - The repository modules import without the coco_labels import-time failure.")
    print("  - CUDA choice is intentional; full training is long-running and data-heavy.")
    if args.num_workers == 0:
        print("  - num_workers=0 is useful for debugging dataset exceptions in the main process.")
    if args.visdom == "true":
        print("  - visdom is installed and a visdom server is already running.")
    print("\nNo training was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
