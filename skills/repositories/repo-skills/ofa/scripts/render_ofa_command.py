#!/usr/bin/env python3
"""Render a copyable OFA training or evaluation command.

This helper does not execute training. It only emits a shell command string
using the supplied repo root and common OFA launch flags.

Example:
  python render_ofa_command.py --mode evaluate --repo-root /path/to/OFA \
    --data data/vqa.tsv --task vqa_gen --path checkpoints/vqa.pt \
    --results-path results/vqa --selected-cols 0,5,2,3,4 --beam 5
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import List, Optional


def _quote(value: str) -> str:
    return shlex.quote(str(value))


def _flag(name: str, value: Optional[object]) -> List[str]:
    if value is None or value is False:
        return []
    if value is True:
        return [f"--{name}"]
    return [f"--{name}={_quote(value)}"]


def _build_command(args: argparse.Namespace) -> str:
    repo_root = args.repo_root.resolve()
    script = "train.py" if args.mode == "train" else "evaluate.py"

    parts: List[str] = [f"cd {_quote(repo_root)} &&"]
    if args.cuda_visible_devices:
        parts.extend([f"CUDA_VISIBLE_DEVICES={_quote(args.cuda_visible_devices)}"])
    parts.extend([
        _quote(args.python),
        "-m",
        args.launcher,
        f"--nproc_per_node={int(args.nproc_per_node)}",
        f"--master_port={int(args.master_port)}",
        _quote(repo_root / script),
    ])

    if args.data:
        parts.append(_quote(args.data))

    common_flags = [
        ("task", args.task),
        ("user-dir", args.user_dir),
        ("bpe-dir", args.bpe_dir),
        ("selected-cols", args.selected_cols),
        ("path", args.path),
        ("save-dir", args.save_dir),
        ("results-path", args.results_path),
        ("gen-subset", args.gen_subset),
        ("seed", args.seed),
        ("batch-size", args.batch_size),
        ("beam", args.beam),
        ("max-len-b", args.max_len_b),
        ("max-len-a", args.max_len_a),
        ("lenpen", args.lenpen),
        ("temperature", args.temperature),
        ("no-repeat-ngram-size", args.no_repeat_ngram_size),
        ("criterion", args.criterion),
        ("arch", args.arch),
        ("lr", args.lr),
        ("max-epoch", args.max_epoch),
        ("update-freq", args.update_freq),
        ("restore-file", args.restore_file),
        ("model-overrides", args.model_overrides_json),
    ]
    for name, value in common_flags:
        parts.extend(_flag(name, value))

    if args.fp16:
        parts.append("--fp16")
    if args.ema_eval:
        parts.append("--ema-eval")
    if args.beam_search_vqa_eval:
        parts.append("--beam-search-vqa-eval")
    if args.unnormalized:
        parts.append("--unnormalized")
    if args.disable_validation:
        parts.append("--disable-validation")
    if args.log_format:
        parts.append(f"--log-format={_quote(args.log_format)}")
    if args.log_interval is not None:
        parts.append(f"--log-interval={int(args.log_interval)}")
    if args.extra_args:
        parts.append(args.extra_args)

    return " ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["train", "evaluate"], required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--launcher", default="torch.distributed.launch")
    parser.add_argument("--cuda-visible-devices", default=None)
    parser.add_argument("--nproc-per-node", type=int, default=1)
    parser.add_argument("--master-port", type=int, default=29500)

    parser.add_argument("--data", default=None)
    parser.add_argument("--task", default=None)
    parser.add_argument("--user-dir", default="ofa_module")
    parser.add_argument("--bpe-dir", default="utils/BPE")
    parser.add_argument("--selected-cols", default=None)
    parser.add_argument("--path", default=None)
    parser.add_argument("--save-dir", default=None)
    parser.add_argument("--results-path", default=None)
    parser.add_argument("--gen-subset", default=None)
    parser.add_argument("--restore-file", default=None)

    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--beam", type=int, default=None)
    parser.add_argument("--max-len-b", type=int, default=None)
    parser.add_argument("--max-len-a", type=int, default=None)
    parser.add_argument("--lenpen", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--no-repeat-ngram-size", type=int, default=None)

    parser.add_argument("--criterion", default=None)
    parser.add_argument("--arch", default=None)
    parser.add_argument("--lr", default=None)
    parser.add_argument("--max-epoch", type=int, default=None)
    parser.add_argument("--update-freq", type=int, default=None)

    parser.add_argument("--model-overrides-json", default=None)
    parser.add_argument("--log-format", default="simple")
    parser.add_argument("--log-interval", type=int, default=None)

    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--ema-eval", action="store_true")
    parser.add_argument("--beam-search-vqa-eval", action="store_true")
    parser.add_argument("--unnormalized", action="store_true")
    parser.add_argument("--disable-validation", action="store_true")
    parser.add_argument("--extra-args", default=None, help="Raw shell fragment appended verbatim.")
    args = parser.parse_args()

    if args.model_overrides_json is not None:
        try:
            json.loads(args.model_overrides_json)
        except json.JSONDecodeError as exc:
            print(f"error: --model-overrides-json must be valid JSON: {exc}", file=sys.stderr)
            return 2

    print(_build_command(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
