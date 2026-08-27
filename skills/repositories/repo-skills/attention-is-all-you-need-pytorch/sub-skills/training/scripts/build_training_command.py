#!/usr/bin/env python3
"""Build a safe train.py command for attention-is-all-you-need-pytorch.

The script prints a command and never executes training. It can optionally check
that user-supplied data paths exist before a long run.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import List


PRESET_HELP = {
    "safe-cpu": "Short CPU-oriented command for inspection; epoch defaults to 1 and -no_cuda is emitted.",
    "readme-shared": "README-style shared-vocabulary command: embedding sharing, projection sharing, label smoothing, batch 256, warmup 128000, epoch 400 unless overridden.",
    "shell-multi30k": "train_multi30k_de_en.sh-style command: projection sharing, label smoothing, batch 256, warmup 4000, epoch 200, seed 1, TensorBoard, lr_mul 0.5, scale=emb unless overridden.",
    "custom": "Use explicit options and train.py defaults where values are not provided.",
}


def positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return ivalue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print, but do not run, a train.py command with validated training flags.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional checkout root; if supplied, validate train.py and print its path in the command.")
    parser.add_argument("--python", default="python", help="Python executable token to place in the printed command.")
    parser.add_argument("--data-pkl", default=None, help="Pickle used by train.py. Required for both normal and BPE modes.")
    parser.add_argument("--bpe-train-prefix", default=None, help="BPE train prefix; .src and .trg are appended by torchtext.")
    parser.add_argument("--bpe-val-prefix", default=None, help="BPE validation prefix; .src and .trg are appended by torchtext.")
    parser.add_argument("--output-dir", default=None, help="Training output directory. Defaults depend on preset.")
    parser.add_argument("--preset", choices=sorted(PRESET_HELP), default="safe-cpu", help="Command preset. Use --describe-presets for details.")
    parser.add_argument("--describe-presets", action="store_true", help="Print preset descriptions and exit.")
    parser.add_argument("--epochs", type=positive_int, default=None, help="Override -epoch.")
    parser.add_argument("--batch-size", type=positive_int, default=None, help="Override -b/--batch_size.")
    parser.add_argument("--warmup", type=positive_int, default=None, help="Override -warmup/--n_warmup_steps.")
    parser.add_argument("--lr-mul", type=float, default=None, help="Override -lr_mul.")
    parser.add_argument("--seed", type=int, default=None, help="Set -seed.")
    parser.add_argument("--dropout", type=float, default=None, help="Set -dropout.")
    parser.add_argument("--d-model", type=positive_int, default=None, help="Set -d_model.")
    parser.add_argument("--d-inner-hid", type=positive_int, default=None, help="Set -d_inner_hid.")
    parser.add_argument("--d-k", type=positive_int, default=None, help="Set -d_k.")
    parser.add_argument("--d-v", type=positive_int, default=None, help="Set -d_v.")
    parser.add_argument("--n-head", type=positive_int, default=None, help="Set -n_head.")
    parser.add_argument("--n-layers", type=positive_int, default=None, help="Set -n_layers.")
    parser.add_argument("--scale-emb-or-prj", choices=["emb", "prj", "none"], default=None, help="Set -scale_emb_or_prj.")
    parser.add_argument("--save-mode", choices=["best", "all"], default=None, help="Set -save_mode.")

    emb_group = parser.add_mutually_exclusive_group()
    emb_group.add_argument("--embs-share-weight", action="store_true", help="Emit -embs_share_weight.")
    emb_group.add_argument("--no-embs-share-weight", action="store_true", help="Do not emit -embs_share_weight, even if preset would.")

    proj_group = parser.add_mutually_exclusive_group()
    proj_group.add_argument("--proj-share-weight", action="store_true", help="Emit -proj_share_weight.")
    proj_group.add_argument("--no-proj-share-weight", action="store_true", help="Do not emit -proj_share_weight, even if preset would.")

    smooth_group = parser.add_mutually_exclusive_group()
    smooth_group.add_argument("--label-smoothing", action="store_true", help="Emit -label_smoothing.")
    smooth_group.add_argument("--no-label-smoothing", action="store_true", help="Do not emit -label_smoothing, even if preset would.")

    tb_group = parser.add_mutually_exclusive_group()
    tb_group.add_argument("--use-tb", action="store_true", help="Emit -use_tb.")
    tb_group.add_argument("--no-use-tb", action="store_true", help="Do not emit -use_tb, even if preset would.")

    device_group = parser.add_mutually_exclusive_group()
    device_group.add_argument("--cpu", action="store_true", help="Emit -no_cuda.")
    device_group.add_argument("--gpu", action="store_true", help="Do not emit -no_cuda. Check CUDA separately before running.")

    parser.add_argument("--cuda-visible-devices", default=None, help="Optional CUDA_VISIBLE_DEVICES value to prefix the printed command with.")
    parser.add_argument("--check-paths", action="store_true", help="Validate data pickle and BPE prefix files exist. Does not create output directories.")
    parser.add_argument("--as-list", action="store_true", help="Print one shell-escaped token per line instead of a single command line.")

    args = parser.parse_args()
    if args.describe_presets:
        for name in sorted(PRESET_HELP):
            print(f"{name}: {PRESET_HELP[name]}")
        raise SystemExit(0)
    return args


def preset_defaults(preset: str) -> dict:
    if preset == "safe-cpu":
        return {
            "epoch": 1,
            "batch_size": 256,
            "warmup": 4000,
            "lr_mul": None,
            "scale": None,
            "output_dir": "output/cpu-dry-run",
            "embs": False,
            "proj": False,
            "smoothing": False,
            "use_tb": False,
            "cpu": True,
            "seed": None,
        }
    if preset == "readme-shared":
        return {
            "epoch": 400,
            "batch_size": 256,
            "warmup": 128000,
            "lr_mul": None,
            "scale": None,
            "output_dir": "output/readme-shared",
            "embs": True,
            "proj": True,
            "smoothing": True,
            "use_tb": False,
            "cpu": True,
            "seed": None,
        }
    if preset == "shell-multi30k":
        return {
            "epoch": 200,
            "batch_size": 256,
            "warmup": 4000,
            "lr_mul": 0.5,
            "scale": "emb",
            "output_dir": "output/lr_mul_0.5-scale_emb",
            "embs": False,
            "proj": True,
            "smoothing": True,
            "use_tb": True,
            "cpu": False,
            "seed": 1,
        }
    return {
        "epoch": None,
        "batch_size": None,
        "warmup": None,
        "lr_mul": None,
        "scale": None,
        "output_dir": None,
        "embs": False,
        "proj": False,
        "smoothing": False,
        "use_tb": False,
        "cpu": True,
        "seed": None,
    }


def choose_bool(default: bool, force_true: bool, force_false: bool) -> bool:
    if force_true:
        return True
    if force_false:
        return False
    return default


def resolve_for_check(path_text: str, repo_root: Path | None) -> Path:
    path = Path(path_text)
    if path.is_absolute() or repo_root is None:
        return path
    return repo_root / path


def validate(args: argparse.Namespace, embs_share: bool) -> None:
    bpe_train = args.bpe_train_prefix
    bpe_val = args.bpe_val_prefix
    if not args.data_pkl:
        raise SystemExit("ERROR: --data-pkl is required because train.py needs -data_pkl for both normal and BPE modes.")
    if bool(bpe_train) != bool(bpe_val):
        raise SystemExit("ERROR: supply both --bpe-train-prefix and --bpe-val-prefix, or neither.")
    if (bpe_train and bpe_val) and not embs_share:
        raise SystemExit("ERROR: BPE training requires --embs-share-weight because train.py raises when it is absent.")
    if args.repo_root is not None:
        train_py = args.repo_root / "train.py"
        if not train_py.is_file():
            raise SystemExit("ERROR: --repo-root does not contain train.py.")
    if args.check_paths:
        missing: List[str] = []
        data_pkl = resolve_for_check(args.data_pkl, args.repo_root)
        if not data_pkl.is_file():
            missing.append(str(data_pkl))
        if bpe_train and bpe_val:
            for prefix in (bpe_train, bpe_val):
                for suffix in (".src", ".trg"):
                    candidate = resolve_for_check(prefix + suffix, args.repo_root)
                    if not candidate.is_file():
                        missing.append(str(candidate))
        if missing:
            raise SystemExit("ERROR: missing required input path(s):\n  " + "\n  ".join(missing))


def append_option(command: List[str], flag: str, value) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def build_command(args: argparse.Namespace) -> List[str]:
    defaults = preset_defaults(args.preset)

    embs_share = choose_bool(defaults["embs"], args.embs_share_weight, args.no_embs_share_weight)
    proj_share = choose_bool(defaults["proj"], args.proj_share_weight, args.no_proj_share_weight)
    smoothing = choose_bool(defaults["smoothing"], args.label_smoothing, args.no_label_smoothing)
    use_tb = choose_bool(defaults["use_tb"], args.use_tb, args.no_use_tb)
    cpu = True if args.cpu else False if args.gpu else defaults["cpu"]

    validate(args, embs_share)

    train_token = str(args.repo_root / "train.py") if args.repo_root is not None else "train.py"
    command: List[str] = [args.python, train_token, "-data_pkl", args.data_pkl]

    if args.bpe_train_prefix and args.bpe_val_prefix:
        command.extend(["-train_path", args.bpe_train_prefix, "-val_path", args.bpe_val_prefix])

    output_dir = args.output_dir if args.output_dir is not None else defaults["output_dir"]
    if not output_dir:
        raise SystemExit("ERROR: --output-dir is required for custom preset because train.py raises without -output_dir.")
    command.extend(["-output_dir", output_dir])

    append_option(command, "-epoch", args.epochs if args.epochs is not None else defaults["epoch"])
    append_option(command, "-b", args.batch_size if args.batch_size is not None else defaults["batch_size"])
    append_option(command, "-warmup", args.warmup if args.warmup is not None else defaults["warmup"])
    append_option(command, "-lr_mul", args.lr_mul if args.lr_mul is not None else defaults["lr_mul"])
    append_option(command, "-seed", args.seed if args.seed is not None else defaults["seed"])
    append_option(command, "-dropout", args.dropout)
    append_option(command, "-d_model", args.d_model)
    append_option(command, "-d_inner_hid", args.d_inner_hid)
    append_option(command, "-d_k", args.d_k)
    append_option(command, "-d_v", args.d_v)
    append_option(command, "-n_head", args.n_head)
    append_option(command, "-n_layers", args.n_layers)
    append_option(command, "-scale_emb_or_prj", args.scale_emb_or_prj if args.scale_emb_or_prj is not None else defaults["scale"])
    append_option(command, "-save_mode", args.save_mode)

    if embs_share:
        command.append("-embs_share_weight")
    if proj_share:
        command.append("-proj_share_weight")
    if smoothing:
        command.append("-label_smoothing")
    if use_tb:
        command.append("-use_tb")
    if cpu:
        command.append("-no_cuda")

    if args.cuda_visible_devices is not None:
        command = [f"CUDA_VISIBLE_DEVICES={args.cuda_visible_devices}"] + command
    return command


def main() -> int:
    args = parse_args()
    command = build_command(args)
    if args.as_list:
        for token in command:
            print(shlex.quote(token))
    else:
        print(" ".join(shlex.quote(token) for token in command))
    return 0


if __name__ == "__main__":
    sys.exit(main())
