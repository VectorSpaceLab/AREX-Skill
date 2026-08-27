#!/usr/bin/env python3
"""Safe SpeechScore recipe.

Dry-run is the default: validate metric names, reference requirements, and
source-layout import hints without reading audio. Pass --run to execute
SpeechScore against user-provided files or matching directories.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from pprint import pprint
from typing import Iterable

SUPPORTED_METRICS = {
    "SRMR": {"intrusive": False, "notes": "reference-free modulation/reverberation metric"},
    "PESQ": {"intrusive": True, "notes": "reference-required perceptual quality"},
    "NB_PESQ": {"intrusive": True, "notes": "reference-required narrow-band PESQ"},
    "STOI": {"intrusive": True, "notes": "reference-required intelligibility"},
    "SISDR": {"intrusive": True, "notes": "reference-required scale-invariant SDR"},
    "FWSEGSNR": {"intrusive": True, "notes": "reference-required frequency-weighted segmental SNR"},
    "LSD": {"intrusive": True, "notes": "reference-required log spectral distance"},
    "BSSEval": {"intrusive": True, "notes": "reference-required ISR/SAR/SDR"},
    "DNSMOS": {"intrusive": False, "notes": "reference-free model-backed MOS scores"},
    "SNR": {"intrusive": True, "notes": "reference-required signal-to-noise ratio"},
    "SSNR": {"intrusive": True, "notes": "reference-required segmental SNR"},
    "LLR": {"intrusive": True, "notes": "reference-required log likelihood ratio"},
    "CSIG": {"intrusive": True, "notes": "reference-required MOS predictor"},
    "CBAK": {"intrusive": True, "notes": "reference-required background MOS predictor"},
    "COVL": {"intrusive": True, "notes": "reference-required overall MOS predictor"},
    "MCD": {"intrusive": True, "notes": "reference-required mel-cepstral distortion"},
    "NISQA": {"intrusive": False, "notes": "reference-free model-backed speech quality"},
    "DISTILL_MOS": {"intrusive": False, "notes": "reference-free model-backed MOS"},
}
ALIASES = {name.lower().replace("_", ""): name for name in SUPPORTED_METRICS}
ALIASES.update({name.lower(): name for name in SUPPORTED_METRICS})
ALIASES.update({name.lower().replace("_", "-"): name for name in SUPPORTED_METRICS})


def canonical_metric_name(raw: str) -> str:
    token = raw.strip()
    if not token:
        raise ValueError("empty metric name")
    key = token.lower().replace(" ", "")
    normalized_key = key.replace("-", "_")
    compact_key = normalized_key.replace("_", "")
    if key in ALIASES:
        return ALIASES[key]
    if normalized_key in ALIASES:
        return ALIASES[normalized_key]
    if compact_key in ALIASES:
        return ALIASES[compact_key]
    raise ValueError(f"unsupported metric '{token}'")


def parse_metrics(raw: str | None) -> list[str]:
    if raw is None or not raw.strip():
        return list(SUPPORTED_METRICS)
    selected: list[str] = []
    seen: set[str] = set()
    for token in raw.split(","):
        name = canonical_metric_name(token)
        if name not in seen:
            selected.append(name)
            seen.add(name)
    return selected


def intrusive_metrics(metrics: Iterable[str]) -> list[str]:
    return [name for name in metrics if SUPPORTED_METRICS[name]["intrusive"]]


def add_source_layout(path: Path | None) -> None:
    if path is None:
        return
    path = path.resolve()
    if not (path / "speechscore.py").exists():
        raise SystemExit(
            f"--speechscore-dir must point to the component directory containing speechscore.py; got {path}"
        )
    sys.path.insert(0, str(path))
    # The repository's source-layout imports modules such as `scores.*` and
    # `basis` relative to the speechscore component directory.
    os.chdir(path)


def import_speechscore(speechscore_dir: Path | None):
    old_cwd = Path.cwd()
    try:
        add_source_layout(speechscore_dir)
        from speechscore import SpeechScore  # type: ignore
        return SpeechScore
    except ImportError as exc:
        message = [
            "Unable to import SpeechScore.",
            "If you are using the repository source layout, pass --speechscore-dir pointing at the component directory that contains speechscore.py.",
            "Install the repository runtime requirements for metric dependencies such as resampy, pesq, pystoi, pyworld/pysptk, onnxruntime, gammatone, and xls_r_sqa.",
            "If the failure mentions pkg_resources while importing pyworld, use a setuptools version that still provides pkg_resources (for example setuptools<81).",
            f"Original import error: {exc}",
        ]
        raise SystemExit("\n".join(message)) from exc
    finally:
        os.chdir(old_cwd)


def validate_paths_for_run(test_path: Path | None, reference_path: Path | None, metrics: list[str]) -> None:
    if test_path is None:
        raise SystemExit("--run requires --test-path")
    if not test_path.exists():
        raise SystemExit(f"--test-path does not exist: {test_path}")
    if intrusive_metrics(metrics):
        if reference_path is None:
            raise SystemExit(
                "Selected intrusive metrics require --reference-path. "
                f"Intrusive metrics selected: {', '.join(intrusive_metrics(metrics))}"
            )
        if not reference_path.exists():
            raise SystemExit(f"--reference-path does not exist: {reference_path}")
    if reference_path is not None and test_path.is_dir() != reference_path.is_dir():
        raise SystemExit("For directory scoring, --test-path and --reference-path must both be directories.")


def dry_run_summary(args: argparse.Namespace, metrics: list[str]) -> dict[str, object]:
    intrusive = intrusive_metrics(metrics)
    if intrusive and args.reference_path is None:
        reference_status = "missing-reference-for-intrusive-metrics"
    elif intrusive:
        reference_status = "reference-provided"
    else:
        reference_status = "not-required-for-selected-metrics"
    return {
        "mode": "dry-run",
        "metrics": metrics,
        "intrusive_metrics": intrusive,
        "non_intrusive_metrics": [name for name in metrics if name not in intrusive],
        "reference_status": reference_status,
        "test_path": str(args.test_path) if args.test_path else None,
        "reference_path": str(args.reference_path) if args.reference_path else None,
        "window": args.window,
        "score_rate": args.score_rate,
        "return_mean": args.return_mean,
        "speechscore_dir_hint": str(args.speechscore_dir) if args.speechscore_dir else None,
        "next_step": "Pass --run after paths, dependencies, and source-layout import are ready.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate or run a SpeechScore metric request.")
    parser.add_argument("--metrics", help="Comma-separated metric names. Defaults to all supported metrics.")
    parser.add_argument("--test-path", type=Path, help="Test/degraded audio file or directory.")
    parser.add_argument("--reference-path", type=Path, help="Clean/reference audio file or matching directory for intrusive metrics.")
    parser.add_argument("--window", type=float, default=None, help="Optional scoring window in seconds.")
    parser.add_argument("--score-rate", type=int, default=None, help="Optional scoring sample rate.")
    parser.add_argument("--return-mean", action="store_true", help="Ask SpeechScore to add Mean_Score for directory scoring.")
    parser.add_argument("--speechscore-dir", type=Path, help="Source-layout component directory containing speechscore.py.")
    parser.add_argument("--run", action="store_true", help="Actually import SpeechScore and score the supplied audio.")
    parser.add_argument("--dry-run", action="store_true", help="Validate only. This is the default unless --run is passed.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of pprint output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        metrics = parse_metrics(args.metrics)
    except ValueError as exc:
        parser.error(str(exc))

    if not args.run:
        summary = dry_run_summary(args, metrics)
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            pprint(summary)
        return 0

    validate_paths_for_run(args.test_path, args.reference_path, metrics)
    SpeechScore = import_speechscore(args.speechscore_dir)
    scorer = SpeechScore(metrics)
    results = scorer(
        test_path=str(args.test_path),
        reference_path=str(args.reference_path) if args.reference_path else None,
        window=args.window,
        score_rate=args.score_rate,
        return_mean=args.return_mean,
    )
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        pprint(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
