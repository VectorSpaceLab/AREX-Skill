from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


def _quote(value: object) -> str:
    return shlex.quote(str(value))


def _append_option(parts: list[str], flag: str, value: object | None) -> None:
    if value is None:
        return
    parts.extend([flag, _quote(value)])


def _append_flag(parts: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        parts.append(flag)


def build_command(args: argparse.Namespace) -> list[str]:
    if not args.model:
        raise SystemExit("--model is required")
    if not args.audio:
        raise SystemExit("--audio is required")

    parts = ["python", "-m", "mlx_audio.sts.generate"]
    _append_option(parts, "--model", args.model)
    _append_option(parts, "--audio", args.audio)
    _append_option(parts, "--output-path", args.output_path)
    _append_flag(parts, "--verbose", args.verbose)
    if args.version is not None:
        _append_option(parts, "--version", args.version)
    elif args.subfolder is not None:
        _append_option(parts, "--subfolder", args.subfolder)
    _append_flag(parts, "--stream", args.stream)
    return parts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a safe MLX Audio STS command")
    parser.add_argument("--model", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output-path")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--version", type=int, choices=[1, 2, 3])
    parser.add_argument("--subfolder")
    parser.add_argument("--stream", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.version is not None and args.subfolder is not None:
        print("[warn] --version takes precedence over --subfolder", file=sys.stderr)
    if args.output_path is None:
        inferred = Path(args.audio).with_stem(Path(args.audio).stem + "_enhanced")
        args.output_path = str(inferred)
    print(" ".join(build_command(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
