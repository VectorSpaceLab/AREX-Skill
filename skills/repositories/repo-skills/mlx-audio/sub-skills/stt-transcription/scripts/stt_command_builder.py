from __future__ import annotations

import argparse
import json
import shlex
import sys


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
    if not args.audio:
        raise SystemExit("--audio is required")
    if not args.model:
        raise SystemExit("--model is required")

    parts = ["python", "-m", "mlx_audio.stt.generate"]
    _append_option(parts, "--model", args.model)
    _append_option(parts, "--audio", args.audio)
    _append_option(parts, "--output-path", args.output_path)
    _append_option(parts, "--format", args.format)
    _append_option(parts, "--language", args.language)
    _append_option(parts, "--chunk-duration", args.chunk_duration)
    _append_option(parts, "--frame-threshold", args.frame_threshold)
    _append_option(parts, "--max-tokens", args.max_tokens)
    _append_option(parts, "--max-parallel-segments", args.max_parallel_segments)
    _append_option(parts, "--prefill-step-size", args.prefill_step_size)
    _append_option(parts, "--prompt", args.prompt)
    _append_option(parts, "--text", args.text if args.text else None)
    _append_option(parts, "--context", args.context)
    if args.gen_kwargs is not None:
        _append_option(parts, "--gen-kwargs", json.dumps(args.gen_kwargs, ensure_ascii=False))
    _append_flag(parts, "--stream", args.stream)
    _append_flag(parts, "--verbose", args.verbose)
    return parts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a safe MLX Audio STT command")
    parser.add_argument("--model", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--format", default="txt", choices=["txt", "srt", "vtt", "json"])
    parser.add_argument("--language", default="en")
    parser.add_argument("--chunk-duration", type=float, default=30.0)
    parser.add_argument("--frame-threshold", type=int, default=25)
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--max-parallel-segments", type=int, dest="max_parallel_segments")
    parser.add_argument("--prefill-step-size", type=int, default=2048)
    parser.add_argument("--prompt")
    parser.add_argument("--text", default="")
    parser.add_argument("--context")
    parser.add_argument("--gen-kwargs", type=json.loads, default=None)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(" ".join(build_command(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
