#!/usr/bin/env python3
"""Build and validate a tf-faster-rcnn demo command without running inference.

The helper is read-only: it checks the expected checkpoint files and prints the
command that would run tools/demo.py from the requested repository root.
"""

import argparse
import shlex
import sys
from pathlib import Path

DATASET_TO_TRAIN_IMDB = {
    "pascal_voc": "voc_2007_trainval",
    "pascal_voc_0712": "voc_2007_trainval+voc_2012_trainval",
}
NETWORKS = {
    "vgg16": "vgg16_faster_rcnn_iter_70000.ckpt",
    "res101": "res101_faster_rcnn_iter_110000.ckpt",
}
DEMO_IMAGES = (
    "000456.jpg",
    "000542.jpg",
    "001150.jpg",
    "001763.jpg",
    "004545.jpg",
)


def _non_negative_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


def _build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Print a shell command for tf-faster-rcnn demo inference and validate "
            "the bundled demo images plus the expected TensorFlow checkpoint."
        ),
        formatter_class=HelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/demo_command_builder.py --repo-root /path/to/tf-faster-rcnn "
            "--net res101 --dataset pascal_voc_0712\n"
            "  python scripts/demo_command_builder.py --repo-root . --net vgg16 "
            "--dataset pascal_voc --cpu --validate-only"
        ),
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to the tf-faster-rcnn repository root.",
    )
    parser.add_argument(
        "--net",
        choices=tuple(NETWORKS.keys()),
        default="res101",
        help="Backbone selector used by tools/demo.py.",
    )
    parser.add_argument(
        "--dataset",
        choices=tuple(DATASET_TO_TRAIN_IMDB.keys()),
        default="pascal_voc_0712",
        help="Checkpoint folder selector used by tools/demo.py.",
    )
    parser.add_argument(
        "--gpu-id",
        type=_non_negative_int,
        default=0,
        help="GPU id to place in CUDA_VISIBLE_DEVICES when --cpu is not set.",
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Unset CUDA_VISIBLE_DEVICES in the printed command.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Mark the output as validation-only; the helper never runs inference.",
    )
    return parser


def _resolve_repo_root(repo_root):
    resolved = Path(repo_root).expanduser().resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"--repo-root is not an existing directory: {resolved}")
    return resolved


def _checkpoint_prefix(repo_root, net, dataset):
    train_imdb = DATASET_TO_TRAIN_IMDB[dataset]
    snapshot = NETWORKS[net]
    return repo_root / "output" / net / train_imdb / "default" / snapshot


def _checkpoint_status(prefix):
    meta = Path(str(prefix) + ".meta")
    index = Path(str(prefix) + ".index")
    data_files = sorted(prefix.parent.glob(prefix.name + ".data-*"))

    missing = []
    if not meta.is_file():
        missing.append(".meta")
    if not index.is_file():
        missing.append(".index")
    if not data_files:
        missing.append(".data-*")

    if missing:
        return False, "missing " + ", ".join(missing), meta, index, data_files

    shard_names = ", ".join(path.name for path in data_files)
    return True, f"found {meta.name}, {index.name}, {shard_names}", meta, index, data_files


def _demo_images_status(repo_root):
    demo_dir = repo_root / "data" / "demo"
    missing = [name for name in DEMO_IMAGES if not (demo_dir / name).is_file()]
    if missing:
        return False, "missing demo images: " + ", ".join(missing)
    return True, f"found {len(DEMO_IMAGES)} bundled demo images"


def _demo_command(repo_root, net, dataset, gpu_id, cpu):
    runtime_prefix = "unset CUDA_VISIBLE_DEVICES &&" if cpu else f"CUDA_VISIBLE_DEVICES={gpu_id}"
    return (
        "cd {} && {} python ./tools/demo.py --net {} --dataset {}".format(
            shlex.quote(str(repo_root)),
            runtime_prefix,
            net,
            dataset,
        )
    )


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        repo_root = _resolve_repo_root(args.repo_root)
        demo_script = repo_root / "tools" / "demo.py"
        if not demo_script.is_file():
            raise FileNotFoundError(f"demo script not found: {demo_script}")
        checkpoint_prefix = _checkpoint_prefix(repo_root, args.net, args.dataset)
        checkpoint_ok, checkpoint_detail, _, _, _ = _checkpoint_status(checkpoint_prefix)
        images_ok, images_detail = _demo_images_status(repo_root)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    mode = "validate-only" if args.validate_only else "plan"
    runtime = "cpu (CUDA_VISIBLE_DEVICES unset)" if args.cpu else f"gpu {args.gpu_id}"

    print(f"MODE: {mode}")
    print(f"REPO_ROOT: {repo_root}")
    print(f"DEMO_SCRIPT: {demo_script}")
    print(f"CHECKPOINT_PREFIX: {checkpoint_prefix}")
    print(f"CHECKPOINT_VALIDATION: {'OK' if checkpoint_ok else 'MISSING'} ({checkpoint_detail})")
    print(f"DEMO_IMAGE_VALIDATION: {'OK' if images_ok else 'MISSING'} ({images_detail})")
    print(f"RUNTIME: {runtime}")
    print(f"COMMAND: {_demo_command(repo_root, args.net, args.dataset, args.gpu_id, args.cpu)}")

    if not checkpoint_ok or not images_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
