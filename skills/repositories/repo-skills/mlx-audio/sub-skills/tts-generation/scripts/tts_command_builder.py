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
    if args.save and not args.stream:
        raise SystemExit("--save requires --stream")
    if args.ref_text and len(args.ref_text) != len(args.ref_audio):
        raise SystemExit("--ref_audio and --ref_text must have the same length")
    if args.text is None or not str(args.text).strip():
        raise SystemExit("--text is required")

    parts = ["mlx_audio.tts.generate"]
    _append_option(parts, "--model", args.model)
    _append_option(parts, "--text", args.text)
    _append_option(parts, "--voice", args.voice)
    _append_option(parts, "--prompt", args.prompt)
    _append_option(parts, "--instruct", args.instruct)
    _append_option(parts, "--speed", args.speed)
    _append_option(parts, "--lang_code", args.lang_code)
    _append_option(parts, "--cfg_scale", args.cfg_scale)
    _append_option(parts, "--ddpm_steps", args.ddpm_steps)
    _append_option(parts, "--sigma", args.sigma)
    _append_option(parts, "--stt_model", args.stt_model)
    _append_option(parts, "--output_path", args.output_path)
    _append_option(parts, "--file_prefix", args.file_prefix)
    _append_option(parts, "--audio_format", args.audio_format)
    _append_option(parts, "--temperature", args.temperature)
    _append_option(parts, "--streaming_interval", args.streaming_interval)
    _append_option(parts, "--max_tokens", args.max_tokens)
    _append_option(parts, "--top_p", args.top_p)
    _append_option(parts, "--top_k", args.top_k)
    _append_option(parts, "--min_p", args.min_p)
    _append_option(parts, "--repetition_penalty", args.repetition_penalty)
    _append_option(parts, "--gen_duration", args.gen_duration)
    _append_option(parts, "--duration_multiplier", args.duration_multiplier)
    _append_option(parts, "--steps", args.steps)
    _append_option(parts, "--stg_scale", args.stg_scale)
    _append_option(parts, "--stg_block", args.stg_block)
    _append_option(parts, "--rescale_scale", args.rescale_scale)
    _append_option(parts, "--pitch", args.pitch)
    _append_option(parts, "--gender", args.gender)
    _append_option(parts, "--exaggeration", args.exaggeration)

    for ref_audio in args.ref_audio:
        _append_option(parts, "--ref_audio", ref_audio)
    for ref_text in args.ref_text:
        _append_option(parts, "--ref_text", ref_text)

    _append_flag(parts, "--join_audio", args.join_audio)
    _append_flag(parts, "--play", args.play or args.stream)
    _append_flag(parts, "--verbose", args.verbose)
    _append_flag(parts, "--stream", args.stream)
    _append_flag(parts, "--save", args.save)
    _append_flag(parts, "--use_zero_spk_emb", args.use_zero_spk_emb)
    return parts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a safe MLX Audio TTS command")
    parser.add_argument("--model", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--voice")
    parser.add_argument("--prompt")
    parser.add_argument("--instruct")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--lang_code", default="en")
    parser.add_argument("--cfg_scale", type=float)
    parser.add_argument("--ddpm_steps", type=int)
    parser.add_argument("--sigma", type=float)
    parser.add_argument("--stt_model", default="mlx-community/whisper-large-v3-turbo-asr-fp16")
    parser.add_argument("--output_path")
    parser.add_argument("--file_prefix", default="audio")
    parser.add_argument("--audio_format", default="wav")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--streaming_interval", type=float, default=2.0)
    parser.add_argument("--max_tokens", type=int)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--top_k", type=int, default=50)
    parser.add_argument("--min_p", type=float)
    parser.add_argument("--repetition_penalty", type=float, default=1.1)
    parser.add_argument("--gen_duration", type=float)
    parser.add_argument("--duration_multiplier", type=float)
    parser.add_argument("--steps", type=int)
    parser.add_argument("--stg_scale", type=float)
    parser.add_argument("--stg_block", type=int)
    parser.add_argument("--rescale_scale")
    parser.add_argument("--pitch", type=float, default=1.0)
    parser.add_argument("--gender", default="male")
    parser.add_argument("--exaggeration", type=float, default=0.5)
    parser.add_argument("--ref_audio", action="append", default=[])
    parser.add_argument("--ref_text", action="append", default=[])
    parser.add_argument("--join_audio", action="store_true")
    parser.add_argument("--play", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--use_zero_spk_emb", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    command = build_command(args)
    print(" ".join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
