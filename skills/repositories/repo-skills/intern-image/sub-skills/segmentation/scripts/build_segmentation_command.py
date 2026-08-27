#!/usr/bin/env python3
"""Build safe InternImage segmentation command lines.

The script prints shell commands only. It never launches training, evaluation,
or inference. Commands are built from distilled evidence for InternImage's
MMSegmentation 0.x segmentation entrypoints.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Dict, Iterable, List, Optional

CONFIGS: Dict[str, str] = {
    "ade20k/upernet_internimage_t_512_160k_ade20k": "configs/ade20k/upernet_internimage_t_512_160k_ade20k.py",
    "ade20k/upernet_internimage_s_512_160k_ade20k": "configs/ade20k/upernet_internimage_s_512_160k_ade20k.py",
    "ade20k/upernet_internimage_b_512_160k_ade20k": "configs/ade20k/upernet_internimage_b_512_160k_ade20k.py",
    "ade20k/upernet_internimage_l_640_160k_ade20k": "configs/ade20k/upernet_internimage_l_640_160k_ade20k.py",
    "ade20k/upernet_internimage_xl_640_160k_ade20k": "configs/ade20k/upernet_internimage_xl_640_160k_ade20k.py",
    "ade20k/upernet_internimage_h_896_160k_ade20k": "configs/ade20k/upernet_internimage_h_896_160k_ade20k.py",
    "ade20k/upernet_internimage_g_896_160k_ade20k": "configs/ade20k/upernet_internimage_g_896_160k_ade20k.py",
    "ade20k/mask2former_internimage_h_896_80k_cocostuff2ade20k_ss": "configs/ade20k/mask2former_internimage_h_896_80k_cocostuff2ade20k_ss.py",
    "ade20k/mask2former_internimage_h_896_80k_cocostuff2ade20k_ms": "configs/ade20k/mask2former_internimage_h_896_80k_cocostuff2ade20k_ms.py",
    "cityscapes/upernet_internimage_t_512x1024_160k_cityscapes": "configs/cityscapes/upernet_internimage_t_512x1024_160k_cityscapes.py",
    "cityscapes/upernet_internimage_s_512x1024_160k_cityscapes": "configs/cityscapes/upernet_internimage_s_512x1024_160k_cityscapes.py",
    "cityscapes/upernet_internimage_b_512x1024_160k_cityscapes": "configs/cityscapes/upernet_internimage_b_512x1024_160k_cityscapes.py",
    "cityscapes/upernet_internimage_l_512x1024_160k_cityscapes": "configs/cityscapes/upernet_internimage_l_512x1024_160k_cityscapes.py",
    "cityscapes/upernet_internimage_xl_512x1024_160k_cityscapes": "configs/cityscapes/upernet_internimage_xl_512x1024_160k_cityscapes.py",
    "cityscapes/upernet_internimage_l_512x1024_160k_mapillary2cityscapes": "configs/cityscapes/upernet_internimage_l_512x1024_160k_mapillary2cityscapes.py",
    "cityscapes/upernet_internimage_xl_512x1024_160k_mapillary2cityscapes": "configs/cityscapes/upernet_internimage_xl_512x1024_160k_mapillary2cityscapes.py",
    "cityscapes/segformer_internimage_l_512x1024_160k_mapillary2cityscapes": "configs/cityscapes/segformer_internimage_l_512x1024_160k_mapillary2cityscapes.py",
    "cityscapes/segformer_internimage_xl_512x1024_160k_mapillary2cityscapes": "configs/cityscapes/segformer_internimage_xl_512x1024_160k_mapillary2cityscapes.py",
    "cityscapes/mask2former_internimage_h_1024x1024_80k_mapillary2cityscapes": "configs/cityscapes/mask2former_internimage_h_1024x1024_80k_mapillary2cityscapes.py",
    "coco_stuff164k/mask2former_internimage_h_896_80k_cocostuff164k": "configs/coco_stuff164k/mask2former_internimage_h_896_80k_cocostuff164k.py",
    "coco_stuff10k/mask2former_internimage_h_512_40k_cocostuff164k_to_10k": "configs/coco_stuff10k/mask2former_internimage_h_512_40k_cocostuff164k_to_10k.py",
    "mapillary/upernet_internimage_l_512x1024_80k_mapillary": "configs/mapillary/upernet_internimage_l_512x1024_80k_mapillary.py",
    "mapillary/upernet_internimage_xl_512x1024_80k_mapillary": "configs/mapillary/upernet_internimage_xl_512x1024_80k_mapillary.py",
    "mapillary/segformer_internimage_l_512x1024_80k_mapillary": "configs/mapillary/segformer_internimage_l_512x1024_80k_mapillary.py",
    "mapillary/segformer_internimage_xl_512x1024_80k_mapillary": "configs/mapillary/segformer_internimage_xl_512x1024_80k_mapillary.py",
    "mapillary/mask2former_internimage_h_896x896_80k_mapillary": "configs/mapillary/mask2former_internimage_h_896x896_80k_mapillary.py",
    "nyu_depth_v2/mask2former_internimage_h_480_40k_nyu": "configs/nyu_depth_v2/mask2former_internimage_h_480_40k_nyu.py",
    "pascal_context/mask2former_internimage_h_480_40k_pascal_context_59": "configs/pascal_context/mask2former_internimage_h_480_40k_pascal_context_59.py",
}

# Also accept bare config stems when unambiguous.
for _key, _path in list(CONFIGS.items()):
    CONFIGS.setdefault(_key.rsplit("/", 1)[-1], _path)

PALETTES = ("ade20k", "cityscapes", "cocostuff")


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def command_prefix(repo_root: Optional[str]) -> str:
    if repo_root:
        return f"REPO_ROOT={shlex.quote(repo_root)}; "
    return "REPO_ROOT=${REPO_ROOT:-.}; "


def wrap_command(repo_root: Optional[str], argv: List[str]) -> str:
    return (
        command_prefix(repo_root)
        + 'cd "$REPO_ROOT/segmentation" && '
        + 'PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}" '
        + shell_join(argv)
    )


def resolve_config(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    config = getattr(args, "config", None)
    config_key = getattr(args, "config_key", None)
    if config and config_key:
        parser.error("use only one of --config or --config-key")
    if config_key:
        if config_key not in CONFIGS:
            parser.error(f"unknown --config-key {config_key!r}; run --list-configs")
        return CONFIGS[config_key]
    if not config:
        parser.error("one of --config or --config-key is required")
    return config


def add_if_value(argv: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None:
        argv.extend([flag, str(value)])


def add_bool(argv: List[str], flag: str, enabled: bool) -> None:
    if enabled:
        argv.append(flag)


def add_many(argv: List[str], flag: str, values: Optional[List[str]]) -> None:
    if values:
        argv.append(flag)
        argv.extend(values)


def add_repeated_extra(argv: List[str], values: Optional[List[str]]) -> None:
    if values:
        argv.extend(values)


def validate_opacity(parser: argparse.ArgumentParser, opacity: float) -> None:
    if not (0.0 < opacity <= 1.0):
        parser.error("--opacity must be in the (0, 1] range")


def train_args(args: argparse.Namespace, config: str) -> List[str]:
    argv = [args.python, "-u", "train.py", config]
    add_if_value(argv, "--work-dir", args.work_dir)
    add_if_value(argv, "--load-from", args.load_from)
    add_if_value(argv, "--resume-from", args.resume_from)
    add_bool(argv, "--no-validate", args.no_validate)
    add_if_value(argv, "--gpu-id", args.gpu_id)
    add_if_value(argv, "--seed", args.seed)
    add_bool(argv, "--diff_seed", args.diff_seed)
    add_bool(argv, "--deterministic", args.deterministic)
    add_bool(argv, "--auto-resume", args.auto_resume)
    add_many(argv, "--cfg-options", args.cfg_options)
    add_repeated_extra(argv, args.extra_arg)
    return argv


def test_args(args: argparse.Namespace, config: str, parser: argparse.ArgumentParser) -> List[str]:
    validate_opacity(parser, args.opacity)
    if args.eval and args.format_only:
        parser.error("--eval and --format-only cannot be combined")
    if args.out and not args.out.endswith((".pkl", ".pickle")):
        parser.error("--out must end with .pkl or .pickle for segmentation/test.py")

    eval_values = args.eval
    notes = getattr(args, "_notes", [])
    if not any([args.out, eval_values, args.format_only, args.show, args.show_dir]):
        eval_values = ["mIoU"]
        notes.append("No test output/eval/show action was supplied; defaulted to --eval mIoU to satisfy the source parser.")
    args._notes = notes

    argv = [args.python, "test.py", config, args.checkpoint]
    add_if_value(argv, "--work-dir", args.work_dir)
    add_bool(argv, "--aug-test", args.aug_test)
    add_if_value(argv, "--out", args.out)
    add_if_value(argv, "--dir-name", args.dir_name)
    add_bool(argv, "--format-only", args.format_only)
    add_many(argv, "--eval", eval_values)
    add_bool(argv, "--show", args.show)
    add_if_value(argv, "--show-dir", args.show_dir)
    add_bool(argv, "--gpu-collect", args.gpu_collect)
    add_if_value(argv, "--tmpdir", args.tmpdir)
    add_many(argv, "--cfg-options", args.cfg_options)
    add_many(argv, "--eval-options", args.eval_options)
    add_if_value(argv, "--opacity", args.opacity)
    add_repeated_extra(argv, args.extra_arg)
    return argv


def image_demo_args(args: argparse.Namespace, config: str, parser: argparse.ArgumentParser) -> List[str]:
    validate_opacity(parser, args.opacity)
    argv = [args.python, "image_demo.py", args.image, config, args.checkpoint]
    add_if_value(argv, "--out", args.out)
    add_if_value(argv, "--device", args.device)
    add_if_value(argv, "--palette", args.palette)
    add_if_value(argv, "--opacity", args.opacity)
    add_repeated_extra(argv, args.extra_arg)
    return argv


def emit(args: argparse.Namespace, command: str) -> None:
    notes = list(getattr(args, "_notes", []))
    notes.append("The command is printed only; review environment, dataset, checkpoint, and GPU readiness before executing it.")
    if args.as_json:
        print(json.dumps({"mode": args.mode, "command": command, "notes": notes}, indent=2))
    else:
        for note in notes:
            print(f"# {note}")
        print(command)


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", help="Path to the InternImage checkout. If omitted, emitted command uses REPO_ROOT=${REPO_ROOT:-.}.")
    parser.add_argument("--python", default="python", help="Python executable name/path to place in the emitted command.")
    parser.add_argument("--as-json", action="store_true", help="Print JSON with command and notes instead of shell text.")
    parser.add_argument("--config", help="Relative or absolute segmentation config path to pass to the source entrypoint.")
    parser.add_argument("--config-key", help="Catalog key from --list-configs, e.g. ade20k/upernet_internimage_t_512_160k_ade20k.")
    parser.add_argument("--cfg-options", nargs="+", metavar="KEY=VALUE", help="MMSeg config overrides appended as --cfg-options KEY=VALUE ...")
    parser.add_argument("--extra-arg", action="append", default=[], help="Append one already-tokenized extra argument to the source entrypoint; repeat as needed.")


def add_train_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--work-dir", help="Directory for logs/checkpoints.")
    parser.add_argument("--load-from", help="Checkpoint to load weights from.")
    parser.add_argument("--resume-from", help="Checkpoint to resume training from.")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation during training.")
    parser.add_argument("--gpu-id", type=int, default=None, help="Single-GPU id for non-distributed training.")
    parser.add_argument("--seed", type=int, help="Random seed.")
    parser.add_argument("--diff_seed", action="store_true", help="Use different seeds per distributed rank.")
    parser.add_argument("--deterministic", action="store_true", help="Set deterministic CUDNN behavior in the source entrypoint.")
    parser.add_argument("--auto-resume", action="store_true", help="Resume from the latest checkpoint automatically.")


def add_test_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint", required=True, help="Segmentation checkpoint path.")
    parser.add_argument("--work-dir", help="Directory where eval JSON is written.")
    parser.add_argument("--aug-test", action="store_true", help="Use fixed multi-scale + flip augmentation.")
    parser.add_argument("--out", help="Pickle output path; must end with .pkl or .pickle.")
    parser.add_argument("--dir-name", help="Directory name forwarded to the source test parser.")
    parser.add_argument("--format-only", action="store_true", help="Format outputs without metric evaluation.")
    parser.add_argument("--eval", nargs="+", help="Evaluation metrics, e.g. mIoU or cityscapes.")
    parser.add_argument("--show", action="store_true", help="Show painted results interactively if supported.")
    parser.add_argument("--show-dir", help="Directory for painted result images.")
    parser.add_argument("--gpu-collect", action="store_true", help="Use GPU collection for distributed results.")
    parser.add_argument("--tmpdir", help="Temporary directory for CPU collection in distributed evaluation.")
    parser.add_argument("--eval-options", nargs="+", metavar="KEY=VALUE", help="Evaluation options appended as --eval-options KEY=VALUE ...")
    parser.add_argument("--opacity", type=float, default=0.5, help="Painted segmentation opacity in (0, 1].")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build dry-run InternImage segmentation commands.")
    parser.add_argument("--list-configs", action="store_true", help="List built-in config keys and exit.")
    subparsers = parser.add_subparsers(dest="mode", metavar="MODE")

    train = subparsers.add_parser("train", help="Build a single-process training command.")
    add_common_options(train)
    add_train_options(train)

    dist_train = subparsers.add_parser("dist-train", help="Build a torch.distributed.launch training command.")
    add_common_options(dist_train)
    add_train_options(dist_train)
    dist_train.add_argument("--gpus", type=int, default=8, help="Processes/GPUs per node for torch.distributed.launch.")
    dist_train.add_argument("--port", default="29300", help="Master port; source dist_train.sh default is 29300.")

    test = subparsers.add_parser("test", help="Build a single-process evaluation/test command.")
    add_common_options(test)
    add_test_options(test)

    dist_test = subparsers.add_parser("dist-test", help="Build a torch.distributed.launch evaluation/test command.")
    add_common_options(dist_test)
    add_test_options(dist_test)
    dist_test.add_argument("--gpus", type=int, default=8, help="Processes/GPUs per node for torch.distributed.launch.")
    dist_test.add_argument("--port", default="29510", help="Master port; source dist_test.sh default is 29510.")

    demo = subparsers.add_parser("image-demo", help="Build a single/multi-image demo command.")
    add_common_options(demo)
    demo.add_argument("--image", required=True, help="Input image or directory of images.")
    demo.add_argument("--checkpoint", required=True, help="Segmentation checkpoint path.")
    demo.add_argument("--out", default="demo", help="Output directory for painted images.")
    demo.add_argument("--device", default="cuda:0", help="Inference device, e.g. cuda:0 or cpu if the runtime supports it.")
    demo.add_argument("--palette", choices=PALETTES, default="ade20k", help="Color palette used by the source demo parser.")
    demo.add_argument("--opacity", type=float, default=0.5, help="Painted segmentation opacity in (0, 1].")

    return parser


def print_configs() -> None:
    for key in sorted(k for k in CONFIGS if "/" in k):
        print(f"{key}\t{CONFIGS[key]}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_configs:
        print_configs()
        return 0
    if not args.mode:
        parser.error("MODE is required unless --list-configs is used")

    config = resolve_config(args, parser)

    if args.mode == "train":
        command = wrap_command(args.repo_root, train_args(args, config))
    elif args.mode == "dist-train":
        inner = train_args(args, config)
        # Replace python -u train.py ... with python -m torch.distributed.launch ... train.py ... --launcher pytorch.
        inner = [args.python, "-m", "torch.distributed.launch", f"--nproc_per_node={args.gpus}", f"--master_port={args.port}", "train.py", config] + inner[4:] + ["--launcher", "pytorch"]
        command = wrap_command(args.repo_root, inner)
    elif args.mode == "test":
        command = wrap_command(args.repo_root, test_args(args, config, parser))
    elif args.mode == "dist-test":
        inner = test_args(args, config, parser)
        inner = [args.python, "-m", "torch.distributed.launch", f"--nproc_per_node={args.gpus}", f"--master_port={args.port}", "test.py", config, args.checkpoint] + inner[4:] + ["--launcher", "pytorch"]
        command = wrap_command(args.repo_root, inner)
    elif args.mode == "image-demo":
        command = wrap_command(args.repo_root, image_demo_args(args, config, parser))
    else:
        parser.error(f"unsupported mode {args.mode!r}")
        return 2

    emit(args, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
