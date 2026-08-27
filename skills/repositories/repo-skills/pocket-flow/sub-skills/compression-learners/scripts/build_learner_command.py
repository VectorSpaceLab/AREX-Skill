#!/usr/bin/env python3
"""Build a safe PocketFlow learner command preview.

This helper validates PocketFlow's learner id and prints an abstract launcher or
Direct Python command pattern. It never imports TensorFlow, reads path.conf,
launches training, downloads data, edits files, starts Docker, or writes
checkpoints.
"""

import argparse
from pathlib import PurePosixPath
import shlex
import sys

LEARNERS = {
    "full-prec": {
        "class": "FullPrecLearner",
        "family": "baseline",
        "notes": ["default learner; no compression is applied"],
    },
    "weight-sparse": {
        "class": "WeightSparseLearner",
        "family": "weight sparsification",
        "notes": ["use ws_* flags", "ws_prune_ratio_prtl=optimal invokes RL search"],
    },
    "channel": {
        "class": "ChannelPrunedLearner",
        "family": "original channel pruning",
        "notes": ["use cp_* flags", "cp_prune_option=auto invokes RL search"],
    },
    "chn-pruned-gpu": {
        "class": "ChannelPrunedGpuLearner",
        "family": "GPU-based channel pruning",
        "notes": ["use cpg_* flags", "less documented; treat as GPU/data dependent"],
    },
    "chn-pruned-rmt": {
        "class": "ChannelPrunedRmtLearner",
        "family": "remastered channel pruning",
        "notes": ["use cpr_* flags", "official docs say RL is not ready for this learner"],
    },
    "dis-chn-pruned": {
        "class": "DisChnPrunedLearner",
        "family": "discrimination-aware channel pruning",
        "notes": ["use dcp_* flags", "staged fine-tuning is long-running"],
    },
    "uniform": {
        "class": "UniformQuantLearner",
        "family": "self-developed uniform quantization",
        "notes": ["use uql_* flags", "uql_enbl_rl_agent=True invokes RL bit search"],
    },
    "uniform-tf": {
        "class": "UniformQuantTFLearner",
        "family": "TensorFlow quantization-aware training",
        "notes": ["use uqtf_* flags", "TFLite export is a deployment-conversion task"],
    },
    "non-uniform": {
        "class": "NonUniformQuantLearner",
        "family": "non-uniform quantization",
        "notes": ["use nuql_* flags", "nuql_enbl_rl_agent=True invokes RL bit search"],
    },
}

DISALLOWED_CONTROL_TOKENS = {";", "&&", "||", "|", ">", ">>", "<", "`"}


def validate_run_script(value):
    if not value:
        raise argparse.ArgumentTypeError("run script must be non-empty")
    if "\x00" in value or "\n" in value or "\r" in value:
        raise argparse.ArgumentTypeError("run script must not contain control characters")
    if value.startswith("-"):
        raise argparse.ArgumentTypeError("run script must be a relative Python path, not an option")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise argparse.ArgumentTypeError("run script must be relative to an active PocketFlow checkout")
    if ".." in path.parts:
        raise argparse.ArgumentTypeError("run script must not contain '..'")
    if path.suffix != ".py":
        raise argparse.ArgumentTypeError("run script should end with .py")
    return str(path)


def clean_extra_args(tokens):
    cleaned = []
    for token in tokens:
        if token == "--":
            continue
        if "\x00" in token or "\n" in token or "\r" in token:
            raise SystemExit("extra arguments must not contain control characters")
        if token in DISALLOWED_CONTROL_TOKENS:
            raise SystemExit("refusing shell control token in extra arguments: %r" % token)
        cleaned.append(token)
    return cleaned


def render_command(tokens):
    return " ".join(shlex.quote(str(token)) for token in tokens)


def build_command(args, extra):
    learner_flag = "--learner=%s" % args.learner
    if args.mode == "direct":
        return ["python", args.run_script, "--exec_mode=%s" % args.exec_mode, learner_flag] + extra

    if args.mode == "local":
        cmd = ["./scripts/run_local.sh", args.run_script]
    elif args.mode == "docker":
        cmd = ["./scripts/run_docker.sh", args.run_script]
    elif args.mode == "seven":
        cmd = ["./scripts/run_seven.sh", args.run_script]
    else:  # argparse choices should prevent this
        raise SystemExit("unsupported mode: %s" % args.mode)

    if args.nb_gpus != 1 or args.mode in {"docker", "seven"}:
        cmd.append("-n=%d" % args.nb_gpus)
    cmd.append(learner_flag)
    cmd.extend(extra)
    return cmd


def print_catalog():
    print("Valid PocketFlow learner ids:")
    for key in sorted(LEARNERS):
        meta = LEARNERS[key]
        print("  %-15s -> %-26s (%s)" % (key, meta["class"], meta["family"]))


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Validate a PocketFlow learner id and print a non-executing command preview.",
        epilog=(
            "Pass learner-specific flags after '--', for example:\n"
            "  build_learner_command.py --learner channel -- --cp_prune_option uniform"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--list", action="store_true", help="list valid learner ids and exit")
    parser.add_argument("--learner", choices=sorted(LEARNERS), help="PocketFlow learner id")
    parser.add_argument(
        "--run-script",
        type=validate_run_script,
        default="nets/resnet_at_cifar10_run.py",
        help="relative PocketFlow *_run.py script path (default: %(default)s)",
    )
    parser.add_argument(
        "--mode",
        choices=["local", "docker", "seven", "direct"],
        default="local",
        help="command pattern to preview (default: %(default)s)",
    )
    parser.add_argument(
        "--exec-mode",
        choices=["train", "eval"],
        default="train",
        help="direct Python exec_mode value (used only with --mode direct)",
    )
    parser.add_argument(
        "--nb-gpus",
        type=int,
        default=1,
        help="GPU count to include in local/docker/seven preview (default: %(default)s)",
    )
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="learner/model flags after '--'",
    )
    args, unknown = parser.parse_known_args(argv)
    if args.nb_gpus < 1:
        parser.error("--nb-gpus must be >= 1")
    if args.list:
        return args, []
    if not args.learner:
        parser.error("--learner is required unless --list is used")
    extra = clean_extra_args(unknown + args.extra)
    return args, extra


def main(argv=None):
    args, extra = parse_args(argv)
    if args.list:
        print_catalog()
        return 0

    meta = LEARNERS[args.learner]
    command = build_command(args, extra)

    print("PocketFlow learner command preview")
    print("==================================")
    print("Learner id : %s" % args.learner)
    print("Class      : %s" % meta["class"])
    print("Family     : %s" % meta["family"])
    print("Mode       : %s" % args.mode)
    print("")
    print("Command pattern (not executed):")
    print(render_command(command))
    print("")
    print("Notes:")
    for note in meta["notes"]:
        print("- " + note)
    if args.mode != "direct":
        print("- official launchers require setup/path.conf/GPU checks and may mutate logs or staging files")
    else:
        print("- direct mode bypasses path.conf argument injection; provide all required data/model path flags")
    print("- full training, performance, downloads, Docker/Seven, and GPU runs are not performed by this helper")
    return 0


if __name__ == "__main__":
    sys.exit(main())
