#!/usr/bin/env python3
"""Build safe InternImage detection command lines.

This helper is intentionally standalone: it imports only Python standard-library
modules, never imports InternImage/MMDetection/SAM, and never launches training,
evaluation, inference, downloads, or CUDA builds. It prints shell templates for a
user to inspect, edit, and run in an explicitly prepared checkout.
"""

from __future__ import annotations

import argparse
import json
import shlex
from typing import Dict, Iterable, List, Optional

CONFIGS: Dict[str, str] = {
    "coco/cascade_internimage_l_fpn_1x_coco": "configs/coco/cascade_internimage_l_fpn_1x_coco.py",
    "coco/cascade_internimage_l_fpn_3x_coco": "configs/coco/cascade_internimage_l_fpn_3x_coco.py",
    "coco/cascade_internimage_xl_fpn_1x_coco": "configs/coco/cascade_internimage_xl_fpn_1x_coco.py",
    "coco/cascade_internimage_xl_fpn_3x_coco": "configs/coco/cascade_internimage_xl_fpn_3x_coco.py",
    "coco/dino_4scale_cbinternimage_h_objects365_coco_ss": "configs/coco/dino_4scale_cbinternimage_h_objects365_coco_ss.py",
    "coco/dino_4scale_internimage_g_objects365_coco_ss": "configs/coco/dino_4scale_internimage_g_objects365_coco_ss.py",
    "coco/dino_4scale_internimage_h_objects365_coco_ss": "configs/coco/dino_4scale_internimage_h_objects365_coco_ss.py",
    "coco/dino_4scale_internimage_l_1x_coco_0.1x_backbone_lr": "configs/coco/dino_4scale_internimage_l_1x_coco_0.1x_backbone_lr.py",
    "coco/dino_4scale_internimage_l_1x_coco_layer_wise_lr": "configs/coco/dino_4scale_internimage_l_1x_coco_layer_wise_lr.py",
    "coco/dino_4scale_internimage_t_1x_coco_layer_wise_lr": "configs/coco/dino_4scale_internimage_t_1x_coco_layer_wise_lr.py",
    "coco/mask_rcnn_internimage_b_fpn_1x_coco": "configs/coco/mask_rcnn_internimage_b_fpn_1x_coco.py",
    "coco/mask_rcnn_internimage_b_fpn_3x_coco": "configs/coco/mask_rcnn_internimage_b_fpn_3x_coco.py",
    "coco/mask_rcnn_internimage_s_fpn_1x_coco": "configs/coco/mask_rcnn_internimage_s_fpn_1x_coco.py",
    "coco/mask_rcnn_internimage_s_fpn_3x_coco": "configs/coco/mask_rcnn_internimage_s_fpn_3x_coco.py",
    "coco/mask_rcnn_internimage_t_fpn_1x_coco": "configs/coco/mask_rcnn_internimage_t_fpn_1x_coco.py",
    "coco/mask_rcnn_internimage_t_fpn_1x_coco_with_dcnv4": "configs/coco/mask_rcnn_internimage_t_fpn_1x_coco_with_dcnv4.py",
    "coco/mask_rcnn_internimage_t_fpn_3x_coco": "configs/coco/mask_rcnn_internimage_t_fpn_3x_coco.py",
    "crowd_human/cascade_internimage_xl_fpn_3x_crowd_human": "configs/crowd_human/cascade_internimage_xl_fpn_3x_crowd_human.py",
    "lvis/dino_4scale_cbinternimage_h_objects365_lvis_minival_ss": "configs/lvis/dino_4scale_cbinternimage_h_objects365_lvis_minival_ss.py",
    "lvis/dino_4scale_cbinternimage_h_objects365_lvis_val_ss": "configs/lvis/dino_4scale_cbinternimage_h_objects365_lvis_val_ss.py",
    "openimages/dino_4scale_cbinternimage_h_objects365_openimages_ss": "configs/openimages/dino_4scale_cbinternimage_h_objects365_openimages_ss.py",
    "voc/dino_4scale_cbinternimage_h_objects365_voc07": "configs/voc/dino_4scale_cbinternimage_h_objects365_voc07.py",
    "voc/dino_4scale_cbinternimage_h_objects365_voc12": "configs/voc/dino_4scale_cbinternimage_h_objects365_voc12.py",
}

# Accept bare config stems when unambiguous and preserve canonical keys for listing.
for _key, _path in list(CONFIGS.items()):
    CONFIGS.setdefault(_key.rsplit("/", 1)[-1], _path)

PALETTES = ("coco", "voc", "citys", "random")
DEFAULT_CHECKPOINT = "CHANGE_ME/checkpoint.pth"
DEFAULT_IMAGE = "CHANGE_ME/image.jpg"
DEFAULT_SAM_CHECKPOINT = "CHANGE_ME/sam_vit_b.pth"


def shell_join(parts: Iterable[object]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def command_prefix(repo_root: Optional[str]) -> str:
    if repo_root:
        return f"REPO_ROOT={shlex.quote(repo_root)}; "
    return 'REPO_ROOT="${REPO_ROOT:-$(pwd)}"; '


def wrap_detection_command(repo_root: Optional[str], argv: List[str]) -> str:
    return (
        command_prefix(repo_root)
        + 'cd "$REPO_ROOT/detection" && '
        + 'PYTHONPATH="$REPO_ROOT:$REPO_ROOT/detection:${PYTHONPATH:-}" '
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
    if config:
        return config
    parser.error("one of --config or --config-key is required")
    raise AssertionError("unreachable")


def add_if_value(argv: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None and value != "":
        argv.extend([flag, str(value)])


def add_bool(argv: List[str], flag: str, enabled: bool) -> None:
    if enabled:
        argv.append(flag)


def add_many(argv: List[str], flag: str, values: Optional[List[object]]) -> None:
    if values:
        argv.append(flag)
        argv.extend(str(value) for value in values)


def add_repeated_extra(argv: List[str], values: Optional[List[str]]) -> None:
    if values:
        argv.extend(values)


def default_eval_metrics(config: str) -> List[str]:
    stem = config.rsplit("/", 1)[-1]
    if "crowd_human" in config:
        return ["bbox"]
    if "mask_rcnn" in stem or ("cascade" in stem and "coco" in config):
        return ["bbox", "segm"]
    return ["bbox"]


def has_test_action(args: argparse.Namespace) -> bool:
    return any([args.out, args.eval, args.format_only, args.show, args.show_dir])


def validate_common_test_action(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    *,
    default_metrics: List[str],
    mode_label: str,
) -> List[str]:
    notes: List[str] = []
    if args.eval and args.format_only:
        parser.error("--eval and --format-only cannot be combined")
    if args.out and not args.out.endswith((".pkl", ".pickle")):
        parser.error("--out must end with .pkl or .pickle for the source parser")
    if not has_test_action(args):
        args.eval = default_metrics
        notes.append(
            f"No {mode_label} output/eval/show action was supplied; defaulted to --eval {' '.join(default_metrics)} to satisfy the source parser."
        )
    return notes


def train_args(args: argparse.Namespace, config: str) -> List[str]:
    argv = [args.python, "-u", "train.py", config]
    add_if_value(argv, "--work-dir", args.work_dir)
    add_if_value(argv, "--resume-from", args.resume_from)
    add_bool(argv, "--auto-resume", args.auto_resume)
    add_bool(argv, "--no-validate", args.no_validate)
    add_if_value(argv, "--gpu-id", args.gpu_id)
    add_if_value(argv, "--seed", args.seed)
    add_bool(argv, "--diff-seed", args.diff_seed)
    add_bool(argv, "--deterministic", args.deterministic)
    add_many(argv, "--cfg-options", args.cfg_options)
    add_bool(argv, "--auto-scale-lr", args.auto_scale_lr)
    add_repeated_extra(argv, args.extra_arg)
    return argv


def distributed_train_args(args: argparse.Namespace, config: str) -> List[str]:
    argv = [
        args.python,
        "-m",
        "torch.distributed.launch",
        f"--nproc_per_node={args.gpus}",
        f"--master_port={args.port}",
        "train.py",
        config,
        "--launcher",
        "pytorch",
    ]
    tail_args = train_args(args, config)[4:]
    argv.extend(tail_args)
    return argv


def test_args(args: argparse.Namespace, config: str, parser: argparse.ArgumentParser) -> List[str]:
    notes = validate_common_test_action(
        args,
        parser,
        default_metrics=default_eval_metrics(config),
        mode_label="test",
    )
    setattr(args, "_notes", list(getattr(args, "_notes", [])) + notes)

    argv = [args.python, "test.py", config, args.checkpoint]
    add_if_value(argv, "--work-dir", args.work_dir)
    add_if_value(argv, "--out", args.out)
    add_bool(argv, "--fuse-conv-bn", args.fuse_conv_bn)
    add_many(argv, "--gpu-ids", args.gpu_ids)
    add_bool(argv, "--format-only", args.format_only)
    add_many(argv, "--eval", args.eval)
    add_bool(argv, "--show", args.show)
    add_if_value(argv, "--show-dir", args.show_dir)
    add_if_value(argv, "--show-score-thr", args.show_score_thr)
    add_bool(argv, "--gpu-collect", args.gpu_collect)
    add_if_value(argv, "--tmpdir", args.tmpdir)
    add_many(argv, "--cfg-options", args.cfg_options)
    add_many(argv, "--eval-options", args.eval_options)
    add_repeated_extra(argv, args.extra_arg)
    return argv


def distributed_test_args(args: argparse.Namespace, config: str, parser: argparse.ArgumentParser) -> List[str]:
    argv = [
        args.python,
        "-m",
        "torch.distributed.launch",
        f"--nproc_per_node={args.gpus}",
        f"--master_port={args.port}",
        "test.py",
        config,
        args.checkpoint,
        "--launcher",
        "pytorch",
    ]
    tail_args = test_args(args, config, parser)[4:]
    argv.extend(tail_args)
    return argv


def image_demo_args(args: argparse.Namespace, config: str) -> List[str]:
    argv = [args.python, "image_demo.py", args.image, config, args.checkpoint]
    add_if_value(argv, "--out", args.out)
    add_if_value(argv, "--device", args.device)
    add_if_value(argv, "--palette", args.palette)
    add_if_value(argv, "--score-thr", args.score_thr)
    add_bool(argv, "--async-test", args.async_test)
    add_repeated_extra(argv, args.extra_arg)
    return argv


def sam_args(args: argparse.Namespace, config: str, parser: argparse.ArgumentParser) -> List[str]:
    notes = validate_common_test_action(
        args,
        parser,
        default_metrics=["segm"],
        mode_label="SAM",
    )
    stem = config.rsplit("/", 1)[-1]
    if "dino" in stem or "crowd_human" in config:
        notes.append(
            "SAM source evidence expects a detector with a mask-capable model object; DINO or CrowdHuman bbox-only configs may need code changes before SAM prompting works."
        )
    notes.append("SAM source evidence is single-process only; do not add --launcher pytorch/slurm because the distributed branch raises NotImplementedError.")
    setattr(args, "_notes", list(getattr(args, "_notes", [])) + notes)

    argv = [args.python, "../sam/main_zero_shot_instance_seg.py", config, args.checkpoint, args.sam_checkpoint]
    add_if_value(argv, "--sam_type", args.sam_type)
    add_if_value(argv, "--data_type", args.data_type)
    add_if_value(argv, "--work-dir", args.work_dir)
    add_if_value(argv, "--out", args.out)
    add_bool(argv, "--fuse-conv-bn", args.fuse_conv_bn)
    add_many(argv, "--gpu-ids", args.gpu_ids)
    add_bool(argv, "--format-only", args.format_only)
    add_many(argv, "--eval", args.eval)
    add_bool(argv, "--show", args.show)
    add_if_value(argv, "--show-dir", args.show_dir)
    add_if_value(argv, "--show-score-thr", args.show_score_thr)
    add_bool(argv, "--gpu-collect", args.gpu_collect)
    add_if_value(argv, "--tmpdir", args.tmpdir)
    add_many(argv, "--cfg-options", args.cfg_options)
    add_many(argv, "--eval-options", args.eval_options)
    add_repeated_extra(argv, args.extra_arg)
    return argv


def emit(args: argparse.Namespace, command: str) -> None:
    notes = list(getattr(args, "_notes", []))
    notes.append("The command is printed only; review OpenMMLab versions, dataset roots, checkpoints, GPU/DCNv3 readiness, and SAM assets before executing it.")
    if args.as_json:
        print(json.dumps({"mode": args.mode, "command": command, "notes": notes}, indent=2))
    else:
        for note in notes:
            print(f"# {note}")
        print(command)


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", help="Path to an InternImage checkout. If omitted, emitted command uses REPO_ROOT=${REPO_ROOT:-$(pwd)} and should be run from the checkout root.")
    parser.add_argument("--python", default="python", help="Python executable name/path to place in the emitted command.")
    parser.add_argument("--as-json", action="store_true", help="Print JSON with command and notes instead of shell text.")
    parser.add_argument("--config", help="Relative config path from the detection tree, e.g. configs/coco/mask_rcnn_internimage_t_fpn_1x_coco.py.")
    parser.add_argument("--config-key", help="Catalog key from --list-configs, e.g. coco/mask_rcnn_internimage_t_fpn_1x_coco.")
    parser.add_argument("--cfg-options", nargs="+", metavar="KEY=VALUE", help="MMDetection config overrides appended as --cfg-options KEY=VALUE ...")
    parser.add_argument("--extra-arg", action="append", default=[], help="Append one already-tokenized extra argument to the source entrypoint; repeat as needed.")


def add_train_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--work-dir", help="Directory for logs/checkpoints; source default is ./work_dirs/<config-stem> from the detection working directory.")
    parser.add_argument("--resume-from", help="Checkpoint to resume training from.")
    parser.add_argument("--auto-resume", action="store_true", help="Resume from the latest checkpoint automatically.")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation during training.")
    parser.add_argument("--gpu-id", type=int, default=None, help="Single GPU id for non-distributed training.")
    parser.add_argument("--seed", type=int, help="Random seed.")
    parser.add_argument("--diff-seed", action="store_true", help="Use different seeds per distributed rank.")
    parser.add_argument("--deterministic", action="store_true", help="Set deterministic CUDNN behavior in the source entrypoint.")
    parser.add_argument("--auto-scale-lr", action="store_true", help="Enable source auto-scale-lr config support when the config defines auto_scale_lr.")


def add_test_options(parser: argparse.ArgumentParser, *, checkpoint_required: bool = True) -> None:
    parser.add_argument("--checkpoint", default=None if checkpoint_required else DEFAULT_CHECKPOINT, required=checkpoint_required, help="Detection checkpoint path.")
    parser.add_argument("--work-dir", help="Directory where evaluation metric JSON is written.")
    parser.add_argument("--out", help="Pickle output path; must end with .pkl or .pickle.")
    parser.add_argument("--fuse-conv-bn", action="store_true", help="Append --fuse-conv-bn for a small inference-speed optimization.")
    parser.add_argument("--gpu-ids", nargs="+", type=int, help="GPU ids for non-distributed testing/SAM execution.")
    parser.add_argument("--format-only", action="store_true", help="Format outputs without metric evaluation.")
    parser.add_argument("--eval", nargs="+", help="Evaluation metrics such as bbox, segm, mAP, or recall.")
    parser.add_argument("--show", action="store_true", help="Show painted results interactively if supported.")
    parser.add_argument("--show-dir", help="Directory for painted result images.")
    parser.add_argument("--show-score-thr", type=float, default=0.3, help="Visualization score threshold.")
    parser.add_argument("--gpu-collect", action="store_true", help="Use GPU collection for distributed results.")
    parser.add_argument("--tmpdir", help="Temporary directory for CPU collection in distributed evaluation.")
    parser.add_argument("--eval-options", nargs="+", metavar="KEY=VALUE", help="Evaluation options appended as --eval-options KEY=VALUE ...")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build dry-run InternImage detection commands.")
    parser.add_argument("--list-configs", action="store_true", help="List built-in config keys and exit.")
    subparsers = parser.add_subparsers(dest="mode", metavar="MODE")

    train = subparsers.add_parser("train", help="Build a single-process training command.")
    add_common_options(train)
    add_train_options(train)

    dist_train = subparsers.add_parser("dist-train", help="Build a torch.distributed.launch training command.")
    add_common_options(dist_train)
    add_train_options(dist_train)
    dist_train.add_argument("--gpus", type=int, default=8, help="Processes/GPUs per node for torch.distributed.launch.")
    dist_train.add_argument("--port", default="63667", help="Master port; distilled source train launcher used 63667.")

    test = subparsers.add_parser("test", help="Build a single-process evaluation/test command.")
    add_common_options(test)
    add_test_options(test)

    dist_test = subparsers.add_parser("dist-test", help="Build a torch.distributed.launch evaluation/test command.")
    add_common_options(dist_test)
    add_test_options(dist_test)
    dist_test.add_argument("--gpus", type=int, default=8, help="Processes/GPUs per node for torch.distributed.launch.")
    dist_test.add_argument("--port", default="29511", help="Master port; distilled source test launcher default is 29511.")

    demo = subparsers.add_parser("image-demo", help="Build a single-image detection demo command.")
    add_common_options(demo)
    demo.add_argument("--image", required=True, help="Input image file.")
    demo.add_argument("--checkpoint", required=True, help="Detection checkpoint path.")
    demo.add_argument("--out", default="demo", help="Output directory for painted image; source default is demo.")
    demo.add_argument("--device", default="cuda:0", help="Inference device, e.g. cuda:0 or cpu if the runtime supports it.")
    demo.add_argument("--palette", choices=PALETTES, default="coco", help="Visualization palette accepted by the source parser.")
    demo.add_argument("--score-thr", type=float, default=0.3, help="BBox score threshold.")
    demo.add_argument("--async-test", action="store_true", help="Append the parsed --async-test flag; observed source main path is synchronous.")

    sam = subparsers.add_parser("sam", help="Build a SAM-prompted instance segmentation command.")
    add_common_options(sam)
    add_test_options(sam)
    sam.add_argument("--sam-checkpoint", default=DEFAULT_SAM_CHECKPOINT, help="Segment Anything checkpoint path.")
    sam.add_argument("--sam-type", default="vit_b", help="Segment Anything model registry key, commonly vit_b, vit_l, or vit_h.")
    sam.add_argument("--data-type", choices=["val", "test"], default="test", help="Forwarded as --data_type; source parses it but observed code does not use it to rewrite the config split.")

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

    if getattr(args, "gpus", 1) is not None and getattr(args, "gpus", 1) < 1:
        parser.error("--gpus must be >= 1")

    config = resolve_config(args, parser)

    if args.mode == "train":
        command = wrap_detection_command(args.repo_root, train_args(args, config))
    elif args.mode == "dist-train":
        command = wrap_detection_command(args.repo_root, distributed_train_args(args, config))
    elif args.mode == "test":
        command = wrap_detection_command(args.repo_root, test_args(args, config, parser))
    elif args.mode == "dist-test":
        command = wrap_detection_command(args.repo_root, distributed_test_args(args, config, parser))
    elif args.mode == "image-demo":
        command = wrap_detection_command(args.repo_root, image_demo_args(args, config))
    elif args.mode == "sam":
        command = wrap_detection_command(args.repo_root, sam_args(args, config, parser))
    else:
        parser.error(f"unsupported mode {args.mode!r}")
        return 2

    emit(args, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
