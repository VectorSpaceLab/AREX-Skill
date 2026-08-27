#!/usr/bin/env python3
"""Safe checks for the installed Coqui TTS `tts` console command.

The script runs only parser/registry/metadata commands by default:
`--help`, `--list_models`, and `--model_info_by_name`. It never passes
`--text`, `--source_wav`, or other synthesis/download-loading flags.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Iterable, List, Sequence

HELP_FLAGS = [
    "--list_models",
    "--model_info_by_idx",
    "--model_info_by_name",
    "--text",
    "--model_name",
    "--vocoder_name",
    "--config_path",
    "--model_path",
    "--out_path",
    "--use_cuda",
    "--device",
    "--vocoder_path",
    "--vocoder_config_path",
    "--encoder_path",
    "--encoder_config_path",
    "--pipe_out",
    "--speakers_file_path",
    "--language_ids_file_path",
    "--speaker_idx",
    "--language_idx",
    "--speaker_wav",
    "--list_speaker_idxs",
    "--list_language_idxs",
    "--reference_wav",
    "--reference_speaker_idx",
    "--source_wav",
    "--target_wav",
    "--voice_dir",
]

MODEL_NAME_PREFIXES = ("tts_models", "vocoder_models", "voice_conversion_models")


@dataclass
class CheckResult:
    name: str
    command: List[str]
    returncode: int | None
    ok: bool
    message: str
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""


def excerpt(text: str, limit: int = 20000) -> str:
    text = text.replace("\r\n", "\n")
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def parse_command(command: str) -> List[str]:
    parts = shlex.split(command)
    if not parts:
        raise ValueError("--command must not be empty")
    return parts


def validate_model_info_name(name: str) -> None:
    parts = name.split("/")
    if len(parts) < 4 or parts[0] not in MODEL_NAME_PREFIXES:
        raise ValueError(
            "model info name must look like "
            "tts_models/<language>/<dataset>/<model_name>, "
            "vocoder_models/<language>/<dataset>/<model_name>, or "
            "voice_conversion_models/<language>/<dataset>/<model_name>"
        )


def run_command(name: str, command: Sequence[str], timeout: float) -> CheckResult:
    try:
        proc = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return CheckResult(
            name=name,
            command=list(command),
            returncode=proc.returncode,
            ok=proc.returncode == 0,
            message="exited 0" if proc.returncode == 0 else f"exited {proc.returncode}",
            stdout_excerpt=excerpt(proc.stdout),
            stderr_excerpt=excerpt(proc.stderr),
        )
    except FileNotFoundError as exc:
        return CheckResult(name, list(command), None, False, f"command not found: {exc.filename}")
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            name,
            list(command),
            None,
            False,
            f"timed out after {timeout:g}s",
            stdout_excerpt=excerpt(exc.stdout or ""),
            stderr_excerpt=excerpt(exc.stderr or ""),
        )


def require_terms(result: CheckResult, terms: Iterable[str], where: str = "combined output") -> None:
    output = f"{result.stdout_excerpt}\n{result.stderr_excerpt}"
    missing = [term for term in terms if term not in output]
    if missing:
        result.ok = False
        result.message += f"; missing in {where}: {', '.join(missing)}"


def build_checks(base: Sequence[str], checks: Sequence[str], model_name: str) -> List[tuple[str, List[str], List[str]]]:
    planned: List[tuple[str, List[str], List[str]]] = []
    if "help" in checks:
        planned.append(("help", list(base) + ["--help"], HELP_FLAGS))
    if "list" in checks:
        planned.append(("list", list(base) + ["--list_models"], ["tts_models", "vocoder_models", "voice_conversion_models"]))
    if "model-info" in checks:
        validate_model_info_name(model_name)
        planned.append(("model-info", list(base) + ["--model_info_by_name", model_name], [model_name.split("/")[-1]]))
    return planned


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run safe no-synthesis checks for the installed `tts` CLI.")
    parser.add_argument("--command", default="tts", help="Command used to invoke the CLI, for example `tts`.")
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=["help", "list", "model-info"],
        default=["help", "list", "model-info"],
        help="Safe checks to run. None performs synthesis.",
    )
    parser.add_argument(
        "--model-name",
        default="tts_models/en/ljspeech/tacotron2-DDC",
        help="Released model name for the metadata-only model-info check.",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout per subprocess in seconds.")
    parser.add_argument("--show-output", action="store_true", help="Print captured output excerpts for each check.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON results.")
    args = parser.parse_args(argv)

    try:
        base = parse_command(args.command)
        planned = build_checks(base, args.checks, args.model_name)
    except ValueError as exc:
        parser.error(str(exc))

    results: List[CheckResult] = []
    for name, cmd, required_terms in planned:
        result = run_command(name, cmd, args.timeout)
        if result.ok:
            require_terms(result, required_terms)
        results.append(result)

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            status = "ok" if result.ok else "FAIL"
            print(f"[{status}] {result.name}: {shlex.join(result.command)} ({result.message})")
            if args.show_output:
                if result.stdout_excerpt:
                    print("--- stdout ---")
                    print(result.stdout_excerpt.rstrip())
                if result.stderr_excerpt:
                    print("--- stderr ---", file=sys.stderr)
                    print(result.stderr_excerpt.rstrip(), file=sys.stderr)

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
