#!/usr/bin/env python3
"""Generate ESPnet2 CPU dry-run command skeletons without executing them."""
from __future__ import annotations
import argparse
import shlex

TASKS = {
    "asr": ("espnet2.bin.asr_train", ["--iterator_type", "none", "--dry_run", "true", "--output_dir", "out", "--token_list", "dummy_token_list"]),
    "lm": ("espnet2.bin.lm_train", ["--iterator_type", "none", "--dry_run", "true", "--output_dir", "out", "--token_list", "dummy_token_list"]),
    "tts": ("espnet2.bin.tts_train", ["--iterator_type", "none", "--normalize", "none", "--dry_run", "true", "--output_dir", "out", "--token_list", "dummy_token_list"]),
    "enh": ("espnet2.bin.enh_train", ["--iterator_type", "none", "--dry_run", "true", "--output_dir", "out"]),
    "s2t": ("espnet2.bin.s2t_train", ["--iterator_type", "none", "--dry_run", "true", "--output_dir", "out", "--token_list", "dummy_token_list"]),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an ESPnet2 CPU dry-run command skeleton.")
    parser.add_argument("--task", choices=sorted(TASKS), required=True)
    parser.add_argument("--config")
    parser.add_argument("--python", default="python")
    args = parser.parse_args()
    module, flags = TASKS[args.task]
    cmd = [args.python, "-m", module]
    if args.config:
        cmd += ["--config", args.config]
    cmd += flags
    print(" ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
