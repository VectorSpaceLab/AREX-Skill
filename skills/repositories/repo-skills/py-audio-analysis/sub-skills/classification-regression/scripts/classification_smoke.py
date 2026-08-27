#!/usr/bin/env python3
"""Bounded pyAudioAnalysis classifier smoke test on synthetic WAV tones.

The script intentionally keeps heavy package imports out of module import time so
`--help` works even before pyAudioAnalysis dependencies are installed.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import shutil
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create two synthetic WAV tone class folders, train a bounded "
            "pyAudioAnalysis classifier, classify a held-out tone, and print JSON."
        )
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help=(
            "Directory for generated WAVs and model artifacts. If omitted, a "
            "temporary directory is created and removed unless --keep-work-dir is set."
        ),
    )
    parser.add_argument(
        "--keep-work-dir",
        action="store_true",
        help="Keep the auto-created temporary work directory for inspection.",
    )
    parser.add_argument(
        "--classifier",
        choices=["knn", "svm", "svm_rbf"],
        default="knn",
        help="Classifier family to smoke-test. Default: knn.",
    )
    parser.add_argument(
        "--files-per-class",
        type=int,
        default=6,
        help="Synthetic training WAVs per class. Must be at least 2. Default: 6.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=1.2,
        help="Duration of each synthetic WAV in seconds. Default: 1.2.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Synthetic WAV sample rate. Default: 16000.",
    )
    parser.add_argument(
        "--mid-window",
        type=float,
        default=0.5,
        help="Mid-term window in seconds. Default: 0.5.",
    )
    parser.add_argument(
        "--mid-step",
        type=float,
        default=0.5,
        help="Mid-term step in seconds. Default: 0.5.",
    )
    parser.add_argument(
        "--short-window",
        type=float,
        default=0.05,
        help="Short-term window in seconds. Default: 0.05.",
    )
    parser.add_argument(
        "--short-step",
        type=float,
        default=0.05,
        help="Short-term step in seconds. Default: 0.05.",
    )
    parser.add_argument(
        "--target-class",
        choices=["tone_low", "tone_high"],
        default="tone_high",
        help="Class to synthesize for the held-out file. Default: tone_high.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=13,
        help="Random seed for deterministic tone variation. Default: 13.",
    )
    parser.add_argument(
        "--full-search",
        action="store_true",
        help=(
            "Use pyAudioAnalysis' unmodified hyperparameter search. This can be "
            "slow on tiny synthetic datasets; the default is a fixed bounded selector."
        ),
    )
    args = parser.parse_args()
    if args.files_per_class < 2:
        parser.error("--files-per-class must be at least 2")
    if args.duration <= 0.25:
        parser.error("--duration must be greater than 0.25 seconds")
    if args.mid_window <= 0 or args.mid_step <= 0:
        parser.error("mid-term window and step must be positive")
    if args.short_window <= 0 or args.short_step <= 0:
        parser.error("short-term window and step must be positive")
    return args


def write_wav(np: Any, path: Path, samples: Any, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(samples, -0.95, 0.95)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def synth_tone(np: Any, rng: Any, frequency: float, duration: float, sample_rate: int) -> Any:
    n_samples = int(round(duration * sample_rate))
    t = np.arange(n_samples, dtype=float) / float(sample_rate)
    phase = float(rng.uniform(0.0, 2.0 * math.pi))
    amplitude_mod = 1.0 + 0.02 * np.sin(2.0 * math.pi * 3.0 * t)
    signal = 0.55 * amplitude_mod * np.sin(2.0 * math.pi * frequency * t + phase)
    signal += 0.03 * np.sin(2.0 * math.pi * 2.0 * frequency * t + 0.5 * phase)
    signal += 0.002 * rng.normal(size=n_samples)
    fade_len = min(max(int(0.02 * sample_rate), 1), max(n_samples // 10, 1))
    if fade_len > 1:
        fade = np.linspace(0.0, 1.0, fade_len)
        signal[:fade_len] *= fade
        signal[-fade_len:] *= fade[::-1]
    return signal


def create_dataset(np: Any, work_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    rng = np.random.default_rng(args.seed)
    train_root = work_dir / "train"
    heldout_dir = work_dir / "heldout"
    classes = {"tone_low": 440.0, "tone_high": 880.0}
    class_dirs: list[str] = []

    for class_name, base_freq in classes.items():
        class_dir = train_root / class_name
        class_dirs.append(str(class_dir))
        class_dir.mkdir(parents=True, exist_ok=True)
        for idx in range(args.files_per_class):
            jitter = rng.normal(loc=0.0, scale=2.0)
            freq = base_freq + jitter + (idx - args.files_per_class / 2.0) * 0.5
            samples = synth_tone(np, rng, freq, args.duration, args.sample_rate)
            write_wav(np, class_dir / f"{class_name}_{idx:02d}.wav", samples, args.sample_rate)

    heldout_dir.mkdir(parents=True, exist_ok=True)
    heldout_freq = classes[args.target_class] + 1.5
    heldout_path = heldout_dir / f"{args.target_class}_heldout.wav"
    write_wav(
        np,
        heldout_path,
        synth_tone(np, rng, heldout_freq, args.duration, args.sample_rate),
        args.sample_rate,
    )

    return {
        "class_dirs": class_dirs,
        "heldout_path": str(heldout_path),
        "expected_class": args.target_class,
    }


def install_bounded_selector(aT: Any) -> Any:
    original = aT.evaluate_classifier
    preferred = {"knn": 1, "svm": 1.0, "svm_rbf": 1.0}

    def bounded_evaluate_classifier(
        features: Any,
        class_names: Any,
        classifier_name: str,
        params: Any,
        parameter_mode: int,
        list_of_ids: Any = None,
        n_exp: int = -1,
        train_percentage: float = 0.90,
        smote: bool = False,
    ) -> Any:
        del features, class_names, parameter_mode, list_of_ids, n_exp, train_percentage, smote
        candidates = list(params)
        wanted = preferred.get(classifier_name, candidates[0])
        selected = candidates[0]
        for candidate in candidates:
            if float(candidate) == float(wanted):
                selected = candidate
                break
        print(
            f"[classification_smoke] bounded parameter selector: "
            f"{classifier_name} -> {selected}",
            file=sys.stderr,
        )
        return selected

    aT.evaluate_classifier = bounded_evaluate_classifier
    return original


def relpath(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def run_smoke(args: argparse.Namespace, work_dir: Path) -> tuple[dict[str, Any], int]:
    start = time.time()
    try:
        import numpy as np
        from pyAudioAnalysis import audioTrainTest as aT
    except Exception as exc:  # pragma: no cover - depends on host environment
        return (
            {
                "ok": False,
                "stage": "import",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "hint": (
                    "Install pyAudioAnalysis with its CPU dependencies, including "
                    "numpy, scipy, scikit-learn, imblearn, and plotly."
                ),
            },
            2,
        )

    work_dir.mkdir(parents=True, exist_ok=True)
    dataset = create_dataset(np, work_dir, args)
    model_dir = work_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_prefix = model_dir / f"smoke_{args.classifier}"

    original_evaluator = None
    if args.full_search:
        print(
            "[classification_smoke] using full pyAudioAnalysis hyperparameter search; "
            "this may be slow on synthetic data",
            file=sys.stderr,
        )
    else:
        original_evaluator = install_bounded_selector(aT)

    try:
        with contextlib.redirect_stdout(sys.stderr):
            aT.extract_features_and_train(
                dataset["class_dirs"],
                args.mid_window,
                args.mid_step,
                args.short_window,
                args.short_step,
                args.classifier,
                str(model_prefix),
                compute_beat=False,
                train_percentage=0.75,
                dict_of_ids=None,
                use_smote=False,
            )
            class_id, probabilities, class_names = aT.file_classification(
                dataset["heldout_path"],
                str(model_prefix),
                args.classifier,
            )
    except Exception as exc:
        return (
            {
                "ok": False,
                "stage": "train_or_classify",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "classifier": args.classifier,
            },
            1,
        )
    finally:
        if original_evaluator is not None:
            aT.evaluate_classifier = original_evaluator

    if class_id == -1:
        return (
            {
                "ok": False,
                "stage": "classification",
                "error": "pyAudioAnalysis returned class_id=-1",
                "classifier": args.classifier,
            },
            1,
        )

    if args.classifier == "knn":
        expected_model_files = [model_prefix]
    else:
        expected_model_files = [model_prefix, Path(str(model_prefix) + "MEANS")]
    missing = [relpath(p, work_dir) for p in expected_model_files if not p.exists()]

    names = [str(c) for c in list(class_names)]
    probs = [float(p) for p in list(probabilities)]
    predicted = names[int(class_id)]
    ok = (predicted == dataset["expected_class"]) and not missing

    return (
        {
            "ok": bool(ok),
            "classifier": args.classifier,
            "expected_class": dataset["expected_class"],
            "predicted_class": predicted,
            "class_id": int(class_id),
            "class_names": names,
            "probabilities": probs,
            "heldout_file": relpath(Path(dataset["heldout_path"]), work_dir),
            "model_prefix": relpath(model_prefix, work_dir),
            "model_files": [relpath(p, work_dir) for p in expected_model_files if p.exists()],
            "missing_model_files": missing,
            "files_per_class": args.files_per_class,
            "duration_seconds": args.duration,
            "sample_rate": args.sample_rate,
            "bounded_parameter_search": not args.full_search,
            "elapsed_seconds": round(time.time() - start, 3),
        },
        0 if ok else 1,
    )


def main() -> int:
    args = parse_args()
    if args.work_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="paa-classification-smoke-"))
        cleanup = not args.keep_work_dir
    else:
        work_dir = args.work_dir
        cleanup = False

    try:
        result, exit_code = run_smoke(args, work_dir)
    except Exception as exc:  # pragma: no cover - defensive JSON envelope
        result = {
            "ok": False,
            "stage": "unexpected",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        exit_code = 2
    finally:
        if cleanup:
            shutil.rmtree(work_dir, ignore_errors=True)

    result["work_dir"] = str(work_dir)
    result["work_dir_kept"] = not cleanup
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
