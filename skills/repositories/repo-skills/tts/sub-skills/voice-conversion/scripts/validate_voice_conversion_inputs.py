#!/usr/bin/env python3
"""Validate Coqui TTS FreeVC and TTS+VC wav roles before model load.

This helper performs only local filesystem/header checks. It does not import
TTS, load models, contact the network, or write an output wav.
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

WAV_EXTENSIONS = {".wav", ".wave"}
FREEVC_INPUT_SAMPLE_RATE = 16000
FREEVC_OUTPUT_SAMPLE_RATE = 24000


@dataclass
class Issue:
    level: str
    role: str
    path: str
    message: str


@dataclass
class AudioInfo:
    role: str
    path: str
    exists: bool
    extension: str
    channels: Optional[int] = None
    sample_width_bytes: Optional[int] = None
    sample_rate: Optional[int] = None
    frames: Optional[int] = None
    duration_seconds: Optional[float] = None


@dataclass
class ValidationReport:
    ok: bool
    mode: str
    audio: List[AudioInfo]
    issues: List[Issue]
    output_path: Optional[str]
    expected_freevc_input_sample_rate: int = FREEVC_INPUT_SAMPLE_RATE
    expected_freevc_output_sample_rate: int = FREEVC_OUTPUT_SAMPLE_RATE


def _path_text(path: Optional[Path]) -> str:
    if path is None:
        return ""
    return str(path)


def _normalise_paths(values: Optional[Sequence[str]]) -> List[Path]:
    if not values:
        return []
    return [Path(value).expanduser() for value in values]


def _merge_reference_paths(args: argparse.Namespace) -> List[Path]:
    paths = []
    paths.extend(_normalise_paths(args.speaker_wav))
    paths.extend(_normalise_paths(args.reference_wav))
    return paths


def _add_missing(issues: List[Issue], role: str, message: str) -> None:
    issues.append(Issue(level="error", role=role, path="", message=message))


def _inspect_wav(role: str, path: Path, *, allow_non_wav: bool, strict_wave_header: bool, warn_sample_rate: bool) -> tuple[AudioInfo, List[Issue]]:
    issues: List[Issue] = []
    info = AudioInfo(role=role, path=str(path), exists=path.exists(), extension=path.suffix.lower())

    if not path.exists():
        issues.append(Issue("error", role, str(path), "file does not exist"))
        return info, issues
    if not path.is_file():
        issues.append(Issue("error", role, str(path), "path exists but is not a regular file"))
        return info, issues
    if path.suffix.lower() not in WAV_EXTENSIONS:
        level = "warning" if allow_non_wav else "error"
        issues.append(
            Issue(
                level,
                role,
                str(path),
                "expected a .wav file for FreeVC/TTS+VC; convert or explicitly allow non-wav inputs",
            )
        )
        if not allow_non_wav:
            return info, issues

    try:
        with wave.open(str(path), "rb") as wav_file:
            info.channels = wav_file.getnchannels()
            info.sample_width_bytes = wav_file.getsampwidth()
            info.sample_rate = wav_file.getframerate()
            info.frames = wav_file.getnframes()
            if info.sample_rate:
                info.duration_seconds = round(info.frames / float(info.sample_rate), 6)
    except (wave.Error, EOFError, OSError) as exc:
        level = "error" if strict_wave_header else "warning"
        issues.append(
            Issue(
                level,
                role,
                str(path),
                f"could not parse a standard PCM wav header ({exc}); Coqui may still read some formats through its audio stack",
            )
        )
        return info, issues

    if info.frames == 0:
        issues.append(Issue("error", role, str(path), "wav has zero audio frames"))
    if info.channels is not None and info.channels < 1:
        issues.append(Issue("error", role, str(path), "wav reports no audio channels"))
    if warn_sample_rate and info.sample_rate and info.sample_rate != FREEVC_INPUT_SAMPLE_RATE:
        issues.append(
            Issue(
                "warning",
                role,
                str(path),
                f"sample rate is {info.sample_rate} Hz; FreeVC path loading uses {FREEVC_INPUT_SAMPLE_RATE} Hz internally",
            )
        )
    return info, issues


def _validate_output_path(path_text: Optional[str], *, allow_overwrite: bool, create_output_dir: bool) -> tuple[Optional[str], List[Issue]]:
    issues: List[Issue] = []
    if not path_text:
        return None, issues
    path = Path(path_text).expanduser()
    if path.suffix.lower() not in WAV_EXTENSIONS:
        issues.append(Issue("error", "output_wav", str(path), "output path should end in .wav"))
    parent = path.parent if str(path.parent) else Path(".")
    if not parent.exists():
        if create_output_dir:
            parent.mkdir(parents=True, exist_ok=True)
        else:
            issues.append(Issue("error", "output_wav", str(path), "output parent directory does not exist"))
    elif not parent.is_dir():
        issues.append(Issue("error", "output_wav", str(path), "output parent exists but is not a directory"))
    if path.exists() and not allow_overwrite:
        issues.append(Issue("error", "output_wav", str(path), "output file already exists; pass --allow-overwrite if replacement is intended"))
    return str(path), issues


def validate_voice_conversion_request(args: argparse.Namespace) -> ValidationReport:
    issues: List[Issue] = []
    audio_infos: List[AudioInfo] = []
    mode = args.mode

    source = Path(args.source_wav).expanduser() if args.source_wav else None
    target = Path(args.target_wav).expanduser() if args.target_wav else None
    references = _merge_reference_paths(args)

    if mode == "auto":
        has_direct = source is not None or target is not None
        has_tts_vc = bool(references)
        if has_direct and has_tts_vc:
            mode = "auto:mixed"
        elif has_direct:
            mode = "voice-conversion"
        elif has_tts_vc:
            mode = "tts-with-vc"
        else:
            mode = "auto"
            _add_missing(issues, "mode", "provide source/target wavs for voice conversion or speaker/reference wav for TTS+VC")

    required: List[tuple[str, Optional[Path]]] = []
    if mode in {"voice-conversion", "auto:mixed"}:
        if source is None:
            _add_missing(issues, "source_wav", "source_wav is required for direct FreeVC conversion")
        if target is None:
            _add_missing(issues, "target_wav", "target_wav is required for direct FreeVC conversion")
        required.extend([("source_wav", source), ("target_wav", target)])
    if mode in {"tts-with-vc", "auto:mixed"}:
        if not references:
            _add_missing(issues, "speaker_wav", "speaker_wav/reference_wav is required for TTS+VC")
        required.extend(("speaker_wav", path) for path in references)

    for role, path in required:
        if path is None:
            continue
        info, role_issues = _inspect_wav(
            role,
            path,
            allow_non_wav=args.allow_non_wav,
            strict_wave_header=args.strict_wave_header,
            warn_sample_rate=not args.no_sample_rate_warning,
        )
        audio_infos.append(info)
        issues.extend(role_issues)

    output_path, output_issues = _validate_output_path(
        args.output_wav,
        allow_overwrite=args.allow_overwrite,
        create_output_dir=args.create_output_dir,
    )
    issues.extend(output_issues)

    ok = not any(issue.level == "error" for issue in issues)
    return ValidationReport(ok=ok, mode=mode, audio=audio_infos, issues=issues, output_path=output_path)


def report_to_dict(report: ValidationReport) -> dict:
    return asdict(report)


def report_has_errors(report: ValidationReport) -> bool:
    return any(issue.level == "error" for issue in report.issues)


def render_report(report: ValidationReport, *, json_output: bool = False) -> str:
    if json_output:
        return json.dumps(report_to_dict(report), indent=2, sort_keys=True)

    lines = [f"voice-conversion validation: {'OK' if report.ok else 'FAILED'}", f"mode: {report.mode}"]
    if report.audio:
        lines.append("audio inputs:")
        for info in report.audio:
            detail = f"  - {info.role}: {info.path}"
            if info.sample_rate:
                detail += f" ({info.sample_rate} Hz, {info.channels} ch, {info.duration_seconds:.3f}s)"
            lines.append(detail)
    if report.output_path:
        lines.append(f"output_wav: {report.output_path}")
    if report.issues:
        lines.append("issues:")
        for issue in report.issues:
            path = f" [{issue.path}]" if issue.path else ""
            lines.append(f"  - {issue.level.upper()} {issue.role}{path}: {issue.message}")
    lines.append(
        f"FreeVC defaults: input paths loaded at {report.expected_freevc_input_sample_rate} Hz; saved outputs use {report.expected_freevc_output_sample_rate} Hz."
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate source/target/reference wav roles for Coqui TTS FreeVC and TTS+VC before model load."
    )
    parser.add_argument("--mode", choices=["auto", "voice-conversion", "tts-with-vc"], default="auto")
    parser.add_argument("--source-wav", help="Source utterance to convert for direct FreeVC.")
    parser.add_argument("--target-wav", help="Target speaker reference for direct FreeVC.")
    parser.add_argument("--speaker-wav", nargs="+", help="Target/reference speaker wav(s) for TTS+VC validation.")
    parser.add_argument("--reference-wav", nargs="+", help="Alias for target/reference speaker wav(s) when validating TTS+VC.")
    parser.add_argument("--output-wav", help="Planned output wav path to validate.")
    parser.add_argument("--allow-overwrite", action="store_true", help="Allow an existing output wav path.")
    parser.add_argument("--create-output-dir", action="store_true", help="Create the output parent directory if it is missing.")
    parser.add_argument("--allow-non-wav", action="store_true", help="Warn instead of failing on non-.wav input extensions.")
    parser.add_argument("--strict-wave-header", action="store_true", help="Fail if Python cannot parse the wav header.")
    parser.add_argument("--no-sample-rate-warning", action="store_true", help="Suppress warnings for inputs not already at 16 kHz.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON validation report.")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = validate_voice_conversion_request(args)
    print(render_report(report, json_output=args.json))
    return 1 if report_has_errors(report) else 0


if __name__ == "__main__":
    sys.exit(main())
