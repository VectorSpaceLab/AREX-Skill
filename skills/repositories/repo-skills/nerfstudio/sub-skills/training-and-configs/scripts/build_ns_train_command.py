#!/usr/bin/env python3
"""Build a Nerfstudio ns-train command without running it.

Examples:
    python build_ns_train_command.py --method nerfacto --data data/poster
    python build_ns_train_command.py --method splatfacto --method-arg=--vis --method-arg=viewer --dataparser nerfstudio-data --dataparser-arg=--eval-mode --dataparser-arg=filename --data data/poster
"""

from __future__ import annotations

import argparse
import shlex


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Construct a correctly ordered ns-train command string.")
    parser.add_argument("--method", required=True, help="Nerfstudio method name, e.g. nerfacto or splatfacto.")
    parser.add_argument("--data", help="Dataset directory passed via method-level --data alias.")
    parser.add_argument("--dataparser", help="Optional dataparser subcommand, e.g. nerfstudio-data or blender-data.")
    parser.add_argument("--method-arg", action="append", default=[], help="Append one method-level token; repeat for flag and value.")
    parser.add_argument("--dataparser-arg", action="append", default=[], help="Append one dataparser-level token; repeat for flag and value.")
    parser.add_argument("--cuda-visible-devices", help="Optional CUDA_VISIBLE_DEVICES prefix value.")
    parser.add_argument("--dry-run-prefix", action="store_true", help="Prefix with 'echo' for copy-safe shell testing.")
    args = parser.parse_args()

    cmd: list[str] = []
    if args.cuda_visible_devices:
        cmd.append(f"CUDA_VISIBLE_DEVICES={args.cuda_visible_devices}")
    if args.dry_run_prefix:
        cmd.append("echo")
    cmd.extend(["ns-train", args.method])
    cmd.extend(args.method_arg)
    if args.data:
        cmd.extend(["--data", args.data])
    if args.dataparser:
        cmd.append(args.dataparser)
        cmd.extend(args.dataparser_arg)
    elif args.dataparser_arg:
        parser.error("--dataparser-arg requires --dataparser so dataparser flags have an owner")

    print(shell_join(cmd))
    if args.dataparser_arg and not args.dataparser:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
