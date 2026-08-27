#!/usr/bin/env python3
"""Build validated, shell-quoted Coqui TTS `tts` commands.

The script prints a command; it does not execute it. Released-model commands
require --allow-download because loading a released model can create network,
cache, and disk side effects when weights are not already available.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

MODEL_PREFIXES = ("tts_models", "vocoder_models", "voice_conversion_models")


def split_command(command: str) -> List[str]:
    parts = shlex.split(command)
    if not parts:
        raise argparse.ArgumentTypeError("command must not be empty")
    return parts


def full_name_parts(value: str) -> List[str]:
    return [part for part in value.split("/") if part]


def validate_full_model_name(value: str, allowed_prefixes: Iterable[str], label: str) -> None:
    parts = full_name_parts(value)
    allowed = tuple(allowed_prefixes)
    if len(parts) < 4 or parts[0] not in allowed:
        allowed_text = ", ".join(f"{prefix}/<language>/<dataset>/<model_name>" for prefix in allowed)
        raise ValueError(f"{label} must be a full listed name such as {allowed_text}; got {value!r}")


def validate_idx_query(value: str) -> None:
    parts = full_name_parts(value)
    if len(parts) != 2 or parts[0] not in MODEL_PREFIXES or not parts[1].isdigit():
        raise ValueError("index query must look like tts_models/3, vocoder_models/2, or voice_conversion_models/0")


def require_allow_download(args: argparse.Namespace, reason: str) -> None:
    if not getattr(args, "allow_download", False):
        raise ValueError(f"{reason}. Re-run with --allow-download after approving model cache/network/disk side effects")


def require_existing_path(path_value: str | None, label: str, validate: bool) -> None:
    if not path_value or not validate:
        return
    if not Path(path_value).exists():
        raise ValueError(f"{label} does not exist: {path_value}")


def validate_output_path(path_value: str | None, validate: bool) -> None:
    if not path_value or not validate:
        return
    parent = Path(path_value).expanduser().parent
    if parent and not parent.exists():
        raise ValueError(f"output parent directory does not exist: {parent}")


def validate_pair(first: str | None, second: str | None, first_label: str, second_label: str) -> None:
    if bool(first) != bool(second):
        raise ValueError(f"supply {first_label} and {second_label} together")


def append_device(cmd: List[str], args: argparse.Namespace) -> None:
    device = getattr(args, "device", None)
    legacy = getattr(args, "use_cuda_legacy", False)
    if legacy and device:
        raise ValueError("do not combine --device with --use-cuda-legacy; legacy --use_cuda True overrides --device")
    if legacy:
        cmd.extend(["--use_cuda", "True"])
    elif device:
        cmd.extend(["--device", device])


def append_common_synthesis_flags(cmd: List[str], args: argparse.Namespace) -> None:
    if getattr(args, "speaker_idx", None):
        cmd.extend(["--speaker_idx", args.speaker_idx])
    if getattr(args, "language_idx", None):
        cmd.extend(["--language_idx", args.language_idx])
    speaker_wavs = getattr(args, "speaker_wav", None)
    if speaker_wavs:
        cmd.append("--speaker_wav")
        cmd.extend(speaker_wavs)
    if getattr(args, "pipe_out", False):
        cmd.append("--pipe_out")
    if getattr(args, "voice_dir", None):
        cmd.extend(["--voice_dir", args.voice_dir])
    progress_bar = getattr(args, "progress_bar", None)
    if progress_bar is not None:
        cmd.extend(["--progress_bar", progress_bar])
    append_device(cmd, args)


def validate_speaker_language_requirements(args: argparse.Namespace) -> None:
    has_speaker = bool(getattr(args, "speaker_idx", None) or getattr(args, "speaker_wav", None))
    has_language = bool(getattr(args, "language_idx", None))
    if getattr(args, "require_speaker", False) and not has_speaker:
        raise ValueError("this command was marked as requiring a speaker; add --speaker_idx or --speaker_wav")
    if getattr(args, "require_language", False) and not has_language:
        raise ValueError("this command was marked as requiring a language; add --language_idx")
    model_name = getattr(args, "model_name", "") or ""
    looks_multilingual = any(token in model_name.lower() for token in ("multilingual", "multi-dataset", "xtts", "your_tts"))
    if looks_multilingual and getattr(args, "speaker_wav", None) and not has_language:
        raise ValueError("voice-cloning multilingual model names with --speaker_wav should include --language_idx")


def validate_paths_for_common(args: argparse.Namespace) -> None:
    validate = getattr(args, "validate_paths", False)
    validate_output_path(getattr(args, "out_path", None), validate)
    for wav in getattr(args, "speaker_wav", None) or []:
        require_existing_path(wav, "speaker wav", validate)
    for attr, label in (
        ("model_path", "model checkpoint"),
        ("config_path", "model config"),
        ("vocoder_path", "vocoder checkpoint"),
        ("vocoder_config_path", "vocoder config"),
        ("encoder_path", "encoder checkpoint"),
        ("encoder_config_path", "encoder config"),
        ("speakers_file_path", "speakers file"),
        ("language_ids_file_path", "language ids file"),
        ("source_wav", "source wav"),
        ("target_wav", "target wav"),
    ):
        require_existing_path(getattr(args, attr, None), label, validate)


def build_list_models(args: argparse.Namespace) -> List[str]:
    return split_command(args.command) + ["--list_models"]


def build_model_info_name(args: argparse.Namespace) -> List[str]:
    validate_full_model_name(args.name, MODEL_PREFIXES, "model info name")
    return split_command(args.command) + ["--model_info_by_name", args.name]


def build_model_info_idx(args: argparse.Namespace) -> List[str]:
    validate_idx_query(args.query)
    return split_command(args.command) + ["--model_info_by_idx", args.query]


def build_synthesize(args: argparse.Namespace) -> List[str]:
    if not args.model_name and not args.use_default_model:
        raise ValueError("released synthesis requires --model_name or explicit --use-default-model")
    require_allow_download(args, "released-model synthesis can load or download checkpoints")
    if args.model_name:
        validate_full_model_name(args.model_name, ("tts_models",), "TTS model name")
    if args.vocoder_name:
        validate_full_model_name(args.vocoder_name, ("vocoder_models",), "vocoder name")
    validate_speaker_language_requirements(args)
    validate_paths_for_common(args)

    cmd = split_command(args.command) + ["--text", args.text, "--out_path", args.out_path]
    if args.model_name:
        cmd.extend(["--model_name", args.model_name])
    if args.vocoder_name:
        cmd.extend(["--vocoder_name", args.vocoder_name])
    append_common_synthesis_flags(cmd, args)
    return cmd


def build_custom(args: argparse.Namespace) -> List[str]:
    validate_pair(args.vocoder_path, args.vocoder_config_path, "--vocoder_path", "--vocoder_config_path")
    validate_pair(args.encoder_path, args.encoder_config_path, "--encoder_path", "--encoder_config_path")
    validate_speaker_language_requirements(args)
    validate_paths_for_common(args)

    cmd = split_command(args.command) + [
        "--text",
        args.text,
        "--out_path",
        args.out_path,
        "--model_path",
        args.model_path,
        "--config_path",
        args.config_path,
    ]
    for attr, flag in (
        ("vocoder_path", "--vocoder_path"),
        ("vocoder_config_path", "--vocoder_config_path"),
        ("encoder_path", "--encoder_path"),
        ("encoder_config_path", "--encoder_config_path"),
        ("speakers_file_path", "--speakers_file_path"),
        ("language_ids_file_path", "--language_ids_file_path"),
    ):
        value = getattr(args, attr)
        if value:
            cmd.extend([flag, value])
    append_common_synthesis_flags(cmd, args)
    return cmd


def build_voice_conversion(args: argparse.Namespace) -> List[str]:
    require_allow_download(args, "released voice-conversion model loading can download checkpoints")
    validate_full_model_name(args.model_name, ("voice_conversion_models",), "voice-conversion model name")
    validate_paths_for_common(args)
    cmd = split_command(args.command) + [
        "--model_name",
        args.model_name,
        "--source_wav",
        args.source_wav,
        "--target_wav",
        args.target_wav,
        "--out_path",
        args.out_path,
    ]
    append_device(cmd, args)
    return cmd


def build_list_speakers(args: argparse.Namespace) -> List[str]:
    require_allow_download(args, "listing speaker ids loads the selected model and may download checkpoints")
    validate_full_model_name(args.model_name, ("tts_models",), "TTS model name")
    return split_command(args.command) + ["--model_name", args.model_name, "--list_speaker_idxs"]


def build_list_languages(args: argparse.Namespace) -> List[str]:
    require_allow_download(args, "listing language ids loads the selected model and may download checkpoints")
    validate_full_model_name(args.model_name, ("tts_models",), "TTS model name")
    return split_command(args.command) + ["--model_name", args.model_name, "--list_language_idxs"]


def add_device_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device", help="Add exact CLI --device value, for example cpu, cuda, or cuda:0.")
    parser.add_argument(
        "--use-cuda-legacy",
        action="store_true",
        help="Emit legacy `--use_cuda True` instead of --device. Do not combine with --device.",
    )


def add_common_synthesis_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--speaker_idx", help="Target speaker id for multi-speaker models.")
    parser.add_argument("--language_idx", help="Target language id for multilingual models.")
    parser.add_argument("--speaker_wav", nargs="+", help="One or more speaker reference WAV files.")
    parser.add_argument("--pipe_out", action="store_true", help="Add --pipe_out; command stdout will be WAV bytes when run.")
    parser.add_argument("--voice_dir", help="Voice directory for Tortoise models.")
    parser.add_argument("--progress_bar", choices=["True", "False"], help="Set CLI --progress_bar value.")
    parser.add_argument("--require-speaker", action="store_true", help="Fail unless --speaker_idx or --speaker_wav is supplied.")
    parser.add_argument("--require-language", action="store_true", help="Fail unless --language_idx is supplied.")
    parser.add_argument("--validate-paths", action="store_true", help="Check local input paths and output parent directory before printing.")
    add_device_options(parser)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print validated shell-quoted Coqui TTS `tts` commands without running them.")
    parser.add_argument("--command", default="tts", help="Command used to invoke the CLI, normally `tts`.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    p = subparsers.add_parser("list-models", help="Print `tts --list_models`.")
    p.set_defaults(builder=build_list_models)

    p = subparsers.add_parser("model-info-name", help="Print `tts --model_info_by_name NAME`.")
    p.add_argument("name", help="Full listed model name.")
    p.set_defaults(builder=build_model_info_name)

    p = subparsers.add_parser("model-info-idx", help="Print `tts --model_info_by_idx FAMILY/INDEX`.")
    p.add_argument("query", help="Index query such as tts_models/3.")
    p.set_defaults(builder=build_model_info_idx)

    p = subparsers.add_parser("synthesize", help="Build a released-model text synthesis command.")
    p.add_argument("--text", required=True, help="Text to synthesize.")
    p.add_argument("--out_path", required=True, help="Output WAV path.")
    p.add_argument("--model_name", help="Full listed TTS model name.")
    p.add_argument("--use-default-model", action="store_true", help="Use the CLI default released model deliberately.")
    p.add_argument("--vocoder_name", help="Full listed vocoder name.")
    p.add_argument("--allow-download", action="store_true", help="Acknowledge released model cache/network/disk side effects.")
    add_common_synthesis_options(p)
    p.set_defaults(builder=build_synthesize)

    p = subparsers.add_parser("custom", help="Build a custom checkpoint synthesis command.")
    p.add_argument("--text", required=True, help="Text to synthesize.")
    p.add_argument("--out_path", required=True, help="Output WAV path.")
    p.add_argument("--model_path", required=True, help="Custom TTS checkpoint path.")
    p.add_argument("--config_path", required=True, help="Custom TTS config path.")
    p.add_argument("--vocoder_path", help="Custom vocoder checkpoint path.")
    p.add_argument("--vocoder_config_path", help="Custom vocoder config path.")
    p.add_argument("--encoder_path", help="Speaker encoder checkpoint path.")
    p.add_argument("--encoder_config_path", help="Speaker encoder config path.")
    p.add_argument("--speakers_file_path", help="Custom speakers JSON path.")
    p.add_argument("--language_ids_file_path", help="Custom language ids JSON path.")
    add_common_synthesis_options(p)
    p.set_defaults(builder=build_custom)

    p = subparsers.add_parser("voice-conversion", help="Build a released voice-conversion command.")
    p.add_argument("--source_wav", required=True, help="Audio to transform.")
    p.add_argument("--target_wav", required=True, help="Reference target voice audio.")
    p.add_argument("--out_path", required=True, help="Output WAV path.")
    p.add_argument(
        "--model_name",
        default="voice_conversion_models/multilingual/vctk/freevc24",
        help="Full listed voice-conversion model name.",
    )
    p.add_argument("--allow-download", action="store_true", help="Acknowledge model cache/network/disk side effects.")
    p.add_argument("--validate-paths", action="store_true", help="Check local WAV paths and output parent before printing.")
    add_device_options(p)
    p.set_defaults(builder=build_voice_conversion)

    p = subparsers.add_parser("list-speakers", help="Build a model speaker-id listing command.")
    p.add_argument("--model_name", required=True, help="Full listed TTS model name.")
    p.add_argument("--allow-download", action="store_true", help="Acknowledge that model loading may download checkpoints.")
    p.set_defaults(builder=build_list_speakers)

    p = subparsers.add_parser("list-languages", help="Build a model language-id listing command.")
    p.add_argument("--model_name", required=True, help="Full listed TTS model name.")
    p.add_argument("--allow-download", action="store_true", help="Acknowledge that model loading may download checkpoints.")
    p.set_defaults(builder=build_list_languages)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        cmd = args.builder(args)
    except ValueError as exc:
        parser.error(str(exc))

    print(shlex.join(cmd))
    if getattr(args, "pipe_out", False):
        print("# warning: when this command is run, stdout will contain WAV bytes because --pipe_out is set", file=sys.stderr)
    if getattr(args, "allow_download", False):
        print("# note: released-model execution may download/cache model files if they are not already present", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
