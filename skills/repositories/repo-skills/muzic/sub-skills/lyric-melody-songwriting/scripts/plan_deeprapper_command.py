#!/usr/bin/env python3
"""Build a safe DeepRapper command plan without running model code."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def quote_list(items: list[str]) -> str:
    return " ".join(shlex.quote(str(x)) for x in items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a DeepRapper train or generation command skeleton and asset checks.")
    parser.add_argument("--mode", choices=["generate", "train"], default="generate")
    parser.add_argument("--workspace", default=".", help="DeepRapper project directory to validate paths against.")
    parser.add_argument("--python", default="python", help="Python executable name to show in the command.")
    parser.add_argument("--device", default="0", help="DeepRapper --device value; use cpu only if your runtime supports it.")
    parser.add_argument("--model-dir", default="model/lyrics/model_epoch30")
    parser.add_argument("--model-config", default="model/lyrics/model_epoch30/config.json")
    parser.add_argument("--prefix", default="大海", help="Generation prefix text.")
    parser.add_argument("--length", type=int, default=512)
    parser.add_argument("--nsamples", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--pattern", choices=["sample", "beam"], default="sample")
    parser.add_argument("--with-beat", action="store_true")
    parser.add_argument("--enable-final", action="store_true")
    parser.add_argument("--enable-sentence", action="store_true")
    parser.add_argument("--enable-relative-pos", action="store_true")
    parser.add_argument("--enable-beat", action="store_true")
    parser.add_argument("--save-samples", action="store_true")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser()
    checks = [
        "generate.py" if args.mode == "generate" else "train.py",
        "tokenizations/chinese_dicts.txt",
        "tokenizations/finals.txt",
        "tokenizations/sentences.txt",
        "tokenizations/beats.txt",
        args.model_config if args.mode == "generate" else "config/model_config_small.json",
    ]
    if args.mode == "generate":
        checks.append(args.model_dir)
    print("DeepRapper asset preflight:")
    missing = []
    for rel in checks:
        p = workspace / rel
        ok = p.exists()
        print(f"  {'OK' if ok else 'MISSING'} {rel}")
        if not ok:
            missing.append(rel)

    if args.mode == "generate":
        cmd = [
            args.python,
            "generate.py",
            "--device",
            args.device,
            "--length",
            str(args.length),
            "--batch_size",
            str(args.batch_size),
            "--nsamples",
            str(args.nsamples),
            "--model_dir",
            args.model_dir,
            "--model_config",
            args.model_config,
            "--prefix",
            args.prefix,
            "--pattern",
            args.pattern,
        ]
        for flag, enabled in [
            ("--with_beat", args.with_beat),
            ("--enable_final", args.enable_final),
            ("--enable_sentence", args.enable_sentence),
            ("--enable_relative_pos", args.enable_relative_pos),
            ("--enable_beat", args.enable_beat),
            ("--save_samples", args.save_samples),
        ]:
            if enabled:
                cmd.append(flag)
    else:
        cmd = [
            args.python,
            "train.py",
            "--device",
            args.device,
            "--model_config",
            "config/model_config_small.json",
        ]
    print("\nSuggested command from the DeepRapper project directory:")
    print(quote_list(cmd))
    print("\nNotes:")
    print("- This helper does not run DeepRapper or load checkpoints.")
    print("- Full generation/training requires a compatible PyTorch environment and the expected tokenizer/model assets.")
    if missing:
        print(f"- Resolve missing assets before running: {', '.join(missing)}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
