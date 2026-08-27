#!/usr/bin/env python3
"""Check StyleTTS2 pretrained inference assets without downloading or synthesizing."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

CORE_HELPER_FILES = [
    "Utils/ASR/config.yml",
    "Utils/ASR/epoch_00080.pth",
    "Utils/JDC/bst.t7",
    "Utils/PLBERT/config.yml",
    "Utils/PLBERT/step_1000000.t7",
]

MODEL_FILES = {
    "ljspeech": [
        "Models/LJSpeech/config.yml",
        "Models/LJSpeech/epoch_2nd_00100.pth",
    ],
    "libritts": [
        "Models/LibriTTS/config.yml",
        "Models/LibriTTS/epochs_2nd_00020.pth",
    ],
}

REFERENCE_AUDIO_DIR = "Demo/reference_audio"
REFERENCE_AUDIO_ARCHIVE = "Demo/reference_audio.zip"
REFERENCE_AUDIO_EXAMPLES = [
    "Demo/reference_audio/696_92939_000016_000006.wav",
    "Demo/reference_audio/1789_142896_000022_000005.wav",
    "Demo/reference_audio/1221-135767-0014.wav",
    "Demo/reference_audio/5639-40744-0020.wav",
    "Demo/reference_audio/908-157963-0027.wav",
    "Demo/reference_audio/4077-13754-0000.wav",
    "Demo/reference_audio/3.wav",
    "Demo/reference_audio/4.wav",
    "Demo/reference_audio/5.wav",
    "Demo/reference_audio/anger.wav",
    "Demo/reference_audio/sleepy.wav",
    "Demo/reference_audio/amused.wav",
    "Demo/reference_audio/disgusted.wav",
    "Demo/reference_audio/Yinghao.wav",
    "Demo/reference_audio/Gavin.wav",
    "Demo/reference_audio/Vinay.wav",
    "Demo/reference_audio/Nima.wav",
]


def add_issue(issues: List[Dict[str, Any]], severity: str, scope: str, message: str, path: str | None = None) -> None:
    issue: Dict[str, Any] = {"severity": severity, "scope": scope, "message": message}
    if path is not None:
        issue["path"] = path
    issues.append(issue)


def check_required_files(root: Path, files: List[str], scope: str, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    present: List[str] = []
    missing: List[str] = []
    for rel_path in files:
        abs_path = root / rel_path
        if abs_path.is_file():
            present.append(rel_path)
        else:
            missing.append(rel_path)
            add_issue(issues, "error", scope, "missing required file", rel_path)
    return {
        "scope": scope,
        "required": files,
        "present": present,
        "missing": missing,
        "status": "ok" if not missing else "missing",
    }


def check_reference_audio(root: Path, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    dir_path = root / REFERENCE_AUDIO_DIR
    archive_path = root / REFERENCE_AUDIO_ARCHIVE
    result: Dict[str, Any] = {
        "scope": "reference-audio",
        "directory": REFERENCE_AUDIO_DIR,
        "archive": REFERENCE_AUDIO_ARCHIVE,
        "directory_present": dir_path.is_dir(),
        "archive_present": archive_path.is_file(),
        "wav_count": 0,
        "example_files_present": [],
        "example_files_missing": [],
        "status": "ok",
    }

    if dir_path.is_dir():
        wavs = sorted(p for p in dir_path.rglob("*.wav") if p.is_file())
        result["wav_count"] = len(wavs)
        if not wavs:
            add_issue(issues, "error", "reference-audio", "reference-audio directory exists but contains no wav files", REFERENCE_AUDIO_DIR)
            result["status"] = "missing"
    else:
        add_issue(issues, "error", "reference-audio", "reference-audio directory is missing; extract the archive under Demo/reference_audio/", REFERENCE_AUDIO_DIR)
        result["status"] = "missing"

    if archive_path.is_file() and not dir_path.is_dir():
        add_issue(
            issues,
            "error",
            "reference-audio",
            "archive is present but the extracted reference-audio directory is still missing",
            REFERENCE_AUDIO_ARCHIVE,
        )

    for rel_path in REFERENCE_AUDIO_EXAMPLES:
        if (root / rel_path).is_file():
            result["example_files_present"].append(rel_path)
        else:
            result["example_files_missing"].append(rel_path)

    if result["example_files_missing"] and result["status"] == "ok":
        add_issue(
            issues,
            "warning",
            "reference-audio",
            "some notebook example clips are missing from Demo/reference_audio/",
            ", ".join(result["example_files_missing"]),
        )
        result["status"] = "warning"

    return result


def check_phonemizer() -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    result: Dict[str, Any] = {
        "scope": "phonemizer",
        "phonemizer_importable": False,
        "espeak_binary": None,
        "backend_instantiable": False,
        "nltk_word_tokenize_ready": False,
        "status": "ok",
        "issues": issues,
    }

    phonemizer_mod = None
    EspeakBackend = None
    try:
        import phonemizer as phonemizer_mod  # type: ignore
        from phonemizer.backend import EspeakBackend as _EspeakBackend  # type: ignore
        EspeakBackend = _EspeakBackend
    except Exception as exc:  # pragma: no cover - runtime probe
        add_issue(issues, "error", "phonemizer", f"phonemizer import failed: {exc}")
        result["status"] = "missing"

    if phonemizer_mod is not None:
        result["phonemizer_importable"] = True

    espeak_binary = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak_binary:
        result["espeak_binary"] = espeak_binary
        if EspeakBackend is not None:
            try:
                backend = EspeakBackend(
                    language="en-us",
                    preserve_punctuation=True,
                    with_stress=True,
                )
                _ = backend
                result["backend_instantiable"] = True
            except Exception as exc:  # pragma: no cover - runtime probe
                add_issue(issues, "error", "phonemizer", f"EspeakBackend construction failed: {exc}")
                result["status"] = "missing"
    else:
        add_issue(issues, "error", "phonemizer", "no espeak-ng or espeak binary found on PATH")
        result["status"] = "missing"

    try:
        from nltk.tokenize import word_tokenize

        _ = word_tokenize("StyleTTS2 inference check.")
        result["nltk_word_tokenize_ready"] = True
    except Exception as exc:  # pragma: no cover - runtime probe
        add_issue(issues, "warning", "phonemizer", f"NLTK word_tokenize is not ready: {exc}")
        if result["status"] == "ok":
            result["status"] = "warning"

    return result


def summarize_status(results: List[Dict[str, Any]]) -> str:
    severities = {issue["severity"] for result in results for issue in result.get("issues", [])}
    if "error" in severities:
        return "missing"
    if "warning" in severities:
        return "warning"
    return "ok"


def build_report(repo_root: Path, model_family: str, check_phonemizer_flag: bool, check_reference_audio_flag: bool) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    core = check_required_files(repo_root, CORE_HELPER_FILES, "core-helpers", issues)

    families: Dict[str, Any] = {}
    if model_family in {"ljspeech", "both"}:
        families["ljspeech"] = check_required_files(repo_root, MODEL_FILES["ljspeech"], "ljspeech", issues)
    if model_family in {"libritts", "both"}:
        families["libritts"] = check_required_files(repo_root, MODEL_FILES["libritts"], "libritts", issues)

    reference_audio = None
    if check_reference_audio_flag:
        reference_audio = check_reference_audio(repo_root, issues)

    phonemizer = None
    if check_phonemizer_flag:
        phonemizer = check_phonemizer()
        issues.extend(phonemizer.get("issues", []))

    summary = {
        "repo_root": repo_root.as_posix(),
        "model_family": model_family,
        "status": summarize_status([{"issues": issues}]),
        "core_helpers": core,
        "families": families,
        "reference_audio": reference_audio,
        "phonemizer": phonemizer,
        "issues": issues,
        "notes": [
            "No downloads were attempted.",
            "No speech was synthesized.",
        ],
    }
    return summary


def print_human(report: Dict[str, Any]) -> None:
    print(f"status: {report['status']}")
    print(f"model-family: {report['model_family']}")
    print()

    def show_block(title: str, block: Dict[str, Any] | None) -> None:
        if not block:
            return
        print(f"[{title}] {block.get('status', 'ok')}")
        for key in ("missing", "example_files_missing"):
            values = block.get(key) or []
            if values:
                label = "missing files" if key == "missing" else "missing examples"
                print(f"  {label}:")
                for item in values:
                    print(f"    - {item}")
        if title == "reference-audio":
            print(f"  wav_count: {block.get('wav_count', 0)}")
            if block.get("archive_present"):
                print("  archive_present: true")
        if title == "phonemizer":
            print(f"  phonemizer_importable: {block.get('phonemizer_importable', False)}")
            print(f"  espeak_binary: {block.get('espeak_binary') or 'missing'}")
            print(f"  backend_instantiable: {block.get('backend_instantiable', False)}")
            print(f"  nltk_word_tokenize_ready: {block.get('nltk_word_tokenize_ready', False)}")
        print()

    show_block("core-helpers", report.get("core_helpers"))
    for family_name, block in report.get("families", {}).items():
        show_block(family_name, block)
    show_block("reference-audio", report.get("reference_audio"))
    show_block("phonemizer", report.get("phonemizer"))

    if report.get("issues"):
        print("issues:")
        for issue in report["issues"]:
            path = f" [{issue['path']}]" if issue.get("path") else ""
            print(f"  - {issue['severity']}:{issue['scope']}{path}: {issue['message']}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check StyleTTS2 pretrained inference assets without downloading or synthesizing.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository checkout to inspect (defaults to the current directory).",
    )
    parser.add_argument(
        "--model-family",
        choices=("ljspeech", "libritts", "both"),
        default="both",
        help="Which pretrained model family to verify.",
    )
    parser.add_argument(
        "--check-phonemizer",
        action="store_true",
        help="Also verify the phonemizer, espeak backend, and NLTK tokenization readiness.",
    )
    parser.add_argument(
        "--check-reference-audio",
        action="store_true",
        help="Also verify the LibriTTS reference-audio bundle under Demo/reference_audio/.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human summary.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    report = build_report(repo_root, args.model_family, args.check_phonemizer, args.check_reference_audio)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    return 1 if report["status"] == "missing" else 0


if __name__ == "__main__":
    raise SystemExit(main())
