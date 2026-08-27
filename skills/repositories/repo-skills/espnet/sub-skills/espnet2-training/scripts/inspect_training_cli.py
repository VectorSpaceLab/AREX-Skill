#!/usr/bin/env python3
"""Safely inspect ESPnet2 training module help or printed config."""
from __future__ import annotations
import argparse
import subprocess
import sys

ALLOWED = [
    "espnet2.bin.asr_train", "espnet2.bin.asr_transducer_train", "espnet2.bin.tts_train", "espnet2.bin.tts2_train",
    "espnet2.bin.enh_train", "espnet2.bin.enh_tse_train", "espnet2.bin.enh_s2t_train", "espnet2.bin.st_train",
    "espnet2.bin.s2t_train", "espnet2.bin.s2st_train", "espnet2.bin.lm_train", "espnet2.bin.mt_train",
    "espnet2.bin.slu_train", "espnet2.bin.lid_train", "espnet2.bin.spk_train", "espnet2.bin.diar_train",
    "espnet2.bin.svs_train", "espnet2.bin.ssl_train", "espnet2.bin.hubert_train", "espnet2.bin.uasr_train",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect ESPnet2 training CLI help or --print_config safely.")
    parser.add_argument("--module", choices=ALLOWED)
    parser.add_argument("--mode", choices=["help", "print-config"], default="help")
    parser.add_argument("--extra-arg", action="append", default=[])
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--list-modules", action="store_true")
    args = parser.parse_args()
    if args.list_modules:
        print(chr(10).join(ALLOWED))
        return 0
    if not args.module:
        parser.error("--module is required unless --list-modules is used")
    cmd = [sys.executable, "-m", args.module, "--help" if args.mode == "help" else "--print_config", *args.extra_arg]
    completed = subprocess.run(cmd, text=True, capture_output=True, timeout=args.timeout)
    print(completed.stdout, end="")
    print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
