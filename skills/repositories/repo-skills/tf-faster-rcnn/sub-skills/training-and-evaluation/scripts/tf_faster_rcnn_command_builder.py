#!/usr/bin/env python3
"""Dry-run command builder for tf-faster-rcnn train/test/reval/convert workflows.

This script is bundled with the generated DisCo repo skill. It only prints
commands and metadata. It never imports the original repository, never touches
outputs, and never launches training or evaluation.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from typing import Dict, Iterable, List, Optional, Tuple

DATASETS: Dict[str, Dict[str, object]] = {
    "pascal_voc": {
        "train_imdb": "voc_2007_trainval",
        "test_imdb": "voc_2007_test",
        "iters": 70000,
        "stepsize": "[50000]",
        "anchors": "[8,16,32]",
        "ratios": "[0.5,1,2]",
    },
    "pascal_voc_0712": {
        "train_imdb": "voc_2007_trainval+voc_2012_trainval",
        "test_imdb": "voc_2007_test",
        "iters": 110000,
        "stepsize": "[80000]",
        "anchors": "[8,16,32]",
        "ratios": "[0.5,1,2]",
    },
    "coco": {
        "train_imdb": "coco_2014_train+coco_2014_valminusminival",
        "test_imdb": "coco_2014_minival",
        "iters": 490000,
        "stepsize": "[350000]",
        "anchors": "[4,8,16,32]",
        "ratios": "[0.5,1,2]",
    },
}

NETS = ("vgg16", "res50", "res101", "res152", "mobile")

CONFIG_FACTS: Dict[str, Dict[str, str]] = {
    "vgg16": {"exp_dir": "vgg16", "snapshot_prefix": "vgg16_faster_rcnn"},
    "res50": {"exp_dir": "res50", "snapshot_prefix": "res50_faster_rcnn"},
    "res101": {"exp_dir": "res101", "snapshot_prefix": "res101_faster_rcnn"},
    "res101-lg": {"exp_dir": "res101-lg", "snapshot_prefix": "res101_faster_rcnn"},
    "mobile": {"exp_dir": "mobile", "snapshot_prefix": "mobile_faster_rcnn"},
    # The source CLIs accept res152 and README reports it, but the observed
    # checkout did not include experiments/cfgs/res152.yml.
    "res152": {"exp_dir": "res152", "snapshot_prefix": "res152_faster_rcnn"},
}


def shell_join(parts: Iterable[object]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def flatten_pairs(pairs: Optional[List[List[str]]]) -> List[str]:
    tokens: List[str] = []
    for key, value in pairs or []:
        tokens.extend([key, value])
    return tokens


def slug_from_tokens(tokens: List[str]) -> str:
    if not tokens:
        return ""
    return re.sub(r"\s+", "_", " ".join(tokens)).strip("_")


def resolve_cfg_path(net: str, cfg: Optional[str]) -> str:
    return cfg if cfg else f"experiments/cfgs/{net}.yml"


def _read_config_fact(path: str, key: str, section: Optional[str] = None) -> Optional[str]:
    """Tiny YAML-ish scalar reader for this repo's simple config files."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            active_section: Optional[str] = None
            for raw_line in handle:
                line = raw_line.rstrip("\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                top_match = re.match(r"^([A-Za-z0-9_]+):\s*(.*?)\s*$", line)
                if top_match and not raw_line.startswith((" ", "\t")):
                    active_section = top_match.group(1)
                    if section is None and active_section == key:
                        value = top_match.group(2)
                        return value.strip("'\"") if value else None
                    continue
                if section is not None and active_section == section:
                    nested = re.match(r"^\s+([A-Za-z0-9_]+):\s*(.*?)\s*$", line)
                    if nested and nested.group(1) == key:
                        value = nested.group(2)
                        return value.strip("'\"") if value else None
    except OSError:
        return None
    return None


def infer_config_facts(net: str, cfg_path: str, repo_root: str) -> Dict[str, str]:
    stem = os.path.splitext(os.path.basename(cfg_path))[0]
    facts = dict(CONFIG_FACTS.get(stem, CONFIG_FACTS.get(net, {})))
    if "exp_dir" not in facts:
        facts["exp_dir"] = net
    if "snapshot_prefix" not in facts:
        facts["snapshot_prefix"] = f"{net}_faster_rcnn"

    candidate = cfg_path if os.path.isabs(cfg_path) else os.path.join(repo_root, cfg_path)
    exp_dir = _read_config_fact(candidate, "EXP_DIR")
    snapshot_prefix = _read_config_fact(candidate, "SNAPSHOT_PREFIX", section="TRAIN")
    if exp_dir:
        facts["exp_dir"] = exp_dir
    if snapshot_prefix:
        facts["snapshot_prefix"] = snapshot_prefix
    return facts


def render_shell_command(argv: List[str], gpu_id: Optional[str] = None, use_time: bool = False) -> str:
    prefix: List[str] = []
    if gpu_id is not None:
        prefix.append(f"CUDA_VISIBLE_DEVICES={shlex.quote(str(gpu_id))}")
    if use_time:
        prefix.append("time")
    prefix.append(shell_join(argv))
    return " ".join(prefix)


def checkpoint_prefix(exp_dir: str, train_imdb: str, tag: str, snapshot_prefix_value: str, iters: int) -> str:
    return os.path.join(
        "output",
        exp_dir,
        train_imdb,
        tag or "default",
        f"{snapshot_prefix_value}_iter_{iters}.ckpt",
    )


def snapshot_stem_from_model(model: str, snapshot_prefix_value: str, iters: int) -> str:
    if model:
        base = os.path.basename(model)
        if base.endswith(".ckpt"):
            base = base[:-5]
        return os.path.splitext(base)[0]
    return f"{snapshot_prefix_value}_iter_{iters}"


def default_reval_output_dir(exp_dir: str, test_imdb: str, tag: str, model: str, snapshot_prefix_value: str, iters: int) -> str:
    return os.path.join(
        "output",
        exp_dir,
        test_imdb,
        tag or "default",
        snapshot_stem_from_model(model, snapshot_prefix_value, iters),
    )


def command_record(label: str, argv: List[str], gpu_id: Optional[str] = None, use_time: bool = False, note: str = "") -> Dict[str, object]:
    return {
        "label": label,
        "argv": argv,
        "env": ({"CUDA_VISIBLE_DEVICES": str(gpu_id)} if gpu_id is not None else {}),
        "uses_time_prefix": bool(use_time),
        "shell": render_shell_command(argv, gpu_id=gpu_id, use_time=use_time),
        "note": note,
    }


def build_plan(args: argparse.Namespace) -> Dict[str, object]:
    warnings: List[str] = []
    notes: List[str] = [
        "Dry-run only: this script never launches training, testing, re-evaluation, conversion, TensorFlow, or dataset code."
    ]

    action = args.action
    net = args.net
    if action == "convert" and net != "vgg16":
        warnings.append("Deprecated conversion is VGG16-only; forcing net to vgg16 for the generated command.")
        net = "vgg16"

    mapping = dict(DATASETS[args.dataset])
    train_imdb = args.train_imdb or str(mapping["train_imdb"])
    test_imdb = args.test_imdb or str(mapping["test_imdb"])
    iters = int(args.iters if args.iters is not None else mapping["iters"])
    anchors = args.anchor_scales or str(mapping["anchors"])
    ratios = args.anchor_ratios or str(mapping["ratios"])
    stepsize = args.stepsize or str(mapping["stepsize"])
    cfg_path = resolve_cfg_path(net, args.cfg)
    config_facts = infer_config_facts(net, cfg_path, args.repo_root)
    exp_dir = config_facts["exp_dir"]
    snapshot_prefix_value = args.snapshot_prefix or config_facts["snapshot_prefix"]

    cfg_candidate = cfg_path if os.path.isabs(cfg_path) else os.path.join(args.repo_root, cfg_path)
    if not os.path.exists(cfg_candidate):
        warnings.append(
            f"Config file {cfg_path!r} was not found under --repo-root {args.repo_root!r}; pass --cfg/--repo-root or create the config before a real run."
        )
    if net == "res152" and args.cfg is None:
        warnings.append(
            "The source CLIs accept res152, but the observed checkout did not include experiments/cfgs/res152.yml; use --cfg for a verified real run."
        )

    user_set_tokens = flatten_pairs(args.set_pairs)
    auto_slug = slug_from_tokens(user_set_tokens)
    tag = args.tag if args.tag is not None else (auto_slug if auto_slug else "default")
    if auto_slug and args.tag is None:
        warnings.append(f"Extra --set pairs imply launcher-style tag slug {auto_slug!r}; pass --tag to override.")

    base_set = ["ANCHOR_SCALES", anchors, "ANCHOR_RATIOS", ratios]
    train_set = base_set + ["TRAIN.STEPSIZE", stepsize] + user_set_tokens
    eval_set = base_set + user_set_tokens

    model = args.model or checkpoint_prefix(exp_dir, train_imdb, tag, snapshot_prefix_value, iters)
    weight = args.weight or f"data/imagenet_weights/{net}.ckpt"
    snapshot = args.snapshot or f"{snapshot_prefix_value}_iter_{iters}"
    output_dir = args.output_dir or default_reval_output_dir(exp_dir, test_imdb, tag, model, snapshot_prefix_value, iters)

    commands: List[Dict[str, object]] = []

    if action == "train":
        warnings.append("A real train command is expensive and writes checkpoints/TensorBoard data; get explicit approval before running it.")
        train_argv = [
            "python",
            "./tools/trainval_net.py",
            "--weight",
            weight,
            "--imdb",
            train_imdb,
            "--imdbval",
            test_imdb,
            "--iters",
            str(iters),
            "--cfg",
            cfg_path,
        ]
        if tag != "default":
            train_argv.extend(["--tag", tag])
        train_argv.extend(["--net", net, "--set"] + train_set)
        commands.append(
            command_record(
                "train_if_expected_final_checkpoint_index_is_missing",
                train_argv,
                gpu_id=str(args.gpu_id),
                use_time=True,
                note=f"Original launcher skips this training step if {model}.index already exists.",
            )
        )

        test_argv = [
            "python",
            "./tools/test_net.py",
            "--imdb",
            test_imdb,
            "--model",
            model,
            "--cfg",
            cfg_path,
        ]
        if tag != "default":
            test_argv.extend(["--tag", tag])
        if args.comp:
            test_argv.append("--comp")
        if args.num_dets is not None:
            test_argv.extend(["--num_dets", str(args.num_dets)])
        test_argv.extend(["--net", net, "--set"] + eval_set)
        commands.append(
            command_record(
                "post_train_test_command_from_original_launcher",
                test_argv,
                gpu_id=str(args.gpu_id),
                use_time=True,
                note="The original train shell launcher calls the test launcher after the training block.",
            )
        )

    elif action == "test":
        warnings.append("A real test command runs dataset-wide inference/evaluation and writes detections.pkl; do not run it as a smoke test.")
        test_argv = [
            "python",
            "./tools/test_net.py",
            "--imdb",
            test_imdb,
            "--model",
            model,
            "--cfg",
            cfg_path,
        ]
        if tag != "default":
            test_argv.extend(["--tag", tag])
        if args.comp:
            test_argv.append("--comp")
        if args.num_dets is not None:
            test_argv.extend(["--num_dets", str(args.num_dets)])
        test_argv.extend(["--net", net, "--set"] + eval_set)
        commands.append(command_record("test_command", test_argv, gpu_id=str(args.gpu_id), use_time=True))

    elif action == "reval":
        notes.append("Reval requires an existing detections.pkl in output_dir and the matching dataset annotations; it performs no model inference.")
        reval_argv = ["python", "./tools/reval.py", output_dir, "--imdb", test_imdb]
        if args.matlab:
            reval_argv.append("--matlab")
        if args.comp:
            reval_argv.append("--comp")
        if args.reval_nms:
            reval_argv.append("--nms")
        commands.append(command_record("reval_command", reval_argv))

    elif action == "convert":
        warnings.append("Deprecated VGG16 conversion reads/writes checkpoint files; verify old vgg16_depre snapshot layout before running manually.")
        convert_argv = [
            "python",
            "./tools/convert_from_depre.py",
            "--snapshot",
            snapshot,
            "--imdb",
            train_imdb,
            "--iters",
            str(iters),
            "--cfg",
            cfg_path,
        ]
        if tag != "default":
            convert_argv.extend(["--tag", tag])
        convert_argv.extend(["--set"] + eval_set)
        commands.append(command_record("convert_vgg16_deprecated_snapshot_command", convert_argv, gpu_id=str(args.gpu_id), use_time=True))

    plan = {
        "schema_version": 1,
        "action": action,
        "dry_run_only": True,
        "dataset": args.dataset,
        "net": net,
        "mapping": {
            "train_imdb": train_imdb,
            "test_imdb": test_imdb,
            "iters": iters,
            "stepsize": stepsize,
            "anchor_scales": anchors,
            "anchor_ratios": ratios,
        },
        "config": {
            "cfg_path": cfg_path,
            "exp_dir": exp_dir,
            "snapshot_prefix": snapshot_prefix_value,
        },
        "tag": tag,
        "model_prefix": model,
        "weight_prefix": weight,
        "reval_output_dir": output_dir,
        "commands": commands,
        "warnings": warnings,
        "notes": notes,
    }
    return plan


def print_shell(plan: Dict[str, object]) -> None:
    print("# tf-faster-rcnn dry-run command plan")
    print(f"# action: {plan['action']}")
    print(f"# dataset: {plan['dataset']}  net: {plan['net']}  tag: {plan['tag']}")
    mapping = plan["mapping"]
    print(
        "# mapping: train_imdb={train_imdb} test_imdb={test_imdb} iters={iters} stepsize={stepsize} anchors={anchor_scales} ratios={anchor_ratios}".format(
            **mapping
        )
    )
    config = plan["config"]
    print(
        "# config: cfg_path={cfg_path} exp_dir={exp_dir} snapshot_prefix={snapshot_prefix}".format(
            **config
        )
    )
    print("# dry-run only: nothing has been executed")
    for warning in plan.get("warnings", []):
        print(f"# WARNING: {warning}")
    for note in plan.get("notes", []):
        print(f"# NOTE: {note}")
    print()
    for command in plan["commands"]:
        print(f"# {command['label']}")
        if command.get("note"):
            print(f"# {command['note']}")
        print(command["shell"])
        print()


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely generate dry-run tf-faster-rcnn train/test/reval/convert commands "
            "from dataset, net, and config options. The script never executes them."
        )
    )
    parser.add_argument("action", choices=("train", "test", "reval", "convert"), help="Workflow command to construct.")
    parser.add_argument("--dataset", choices=tuple(DATASETS.keys()), default="pascal_voc", help="Launcher dataset alias.")
    parser.add_argument("--net", choices=NETS, default="vgg16", help="Network selector. Convert is always forced to vgg16.")
    parser.add_argument("--gpu-id", default="0", help="Value for CUDA_VISIBLE_DEVICES in generated train/test/convert commands.")
    parser.add_argument("--cfg", help="Config path to pass to --cfg. Defaults to experiments/cfgs/<net>.yml.")
    parser.add_argument("--iters", type=int, help="Override mapped iteration count.")
    parser.add_argument("--stepsize", help="Override mapped TRAIN.STEPSIZE value, e.g. '[80000]'.")
    parser.add_argument("--anchor-scales", help="Override mapped ANCHOR_SCALES value, e.g. '[8,16,32]'.")
    parser.add_argument("--anchor-ratios", help="Override mapped ANCHOR_RATIOS value, e.g. '[0.5,1,2]'.")
    parser.add_argument("--train-imdb", help="Override mapped training imdb name.")
    parser.add_argument("--test-imdb", help="Override mapped test/validation imdb name.")
    parser.add_argument("--weight", help="Override training initialization checkpoint prefix.")
    parser.add_argument("--model", help="Override test checkpoint prefix, also used to infer default reval output dir.")
    parser.add_argument("--snapshot", help="Override deprecated VGG16 conversion snapshot prefix.")
    parser.add_argument("--snapshot-prefix", help="Override snapshot prefix used for default model/snapshot names.")
    parser.add_argument("--output-dir", help="Output directory for reval; defaults to predicted test output directory.")
    parser.add_argument("--tag", help="Explicit output tag. Without this, user --set pairs derive a launcher-style slug.")
    parser.add_argument(
        "--set",
        dest="set_pairs",
        metavar=("KEY", "VALUE"),
        nargs=2,
        action="append",
        default=[],
        help="Append one config override pair. Repeat for multiple pairs; generated repo command uses one --set list.",
    )
    parser.add_argument("--comp", action="store_true", help="Add competition mode to test or reval commands.")
    parser.add_argument("--num-dets", type=int, help="Add --num_dets to test commands.")
    parser.add_argument("--matlab", action="store_true", help="Add --matlab to reval commands.")
    parser.add_argument("--reval-nms", action="store_true", help="Add --nms to reval commands.")
    parser.add_argument("--format", choices=("shell", "json"), default="shell", help="Output format.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used only for config-existence warnings and simple config fact parsing.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    plan = build_plan(args)
    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print_shell(plan)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through CLI checks
    sys.exit(main())
