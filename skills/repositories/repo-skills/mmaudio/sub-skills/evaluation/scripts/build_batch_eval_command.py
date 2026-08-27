#!/usr/bin/env python3
"""Build a safe MMAudio batch-eval command without running inference.

This helper validates the command shape and prints a shell-quoted
`torchrun ... batch_eval.py ...` command to stdout. It does not import MMAudio,
download weights, launch CUDA work, or create evaluation outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

SUPPORTED_MODELS = (
    "small_16k",
    "small_44k",
    "medium_44k",
    "large_44k",
    "large_44k_v2",
)
SUPPORTED_PREFIXES = (
    "audiocaps_full",
    "audiocaps",
    "moviegen",
    "vggsound",
)

DEFAULT_OMP_NUM_THREADS = 4
DEFAULT_DURATION_S = 8.0
DEFAULT_BATCH_SIZE = 4
DEFAULT_NUM_WORKERS = 2
DEFAULT_SEED = 14159265
DEFAULT_CFG_STRENGTH = 4.5
DEFAULT_NUM_STEPS = 25
DEFAULT_SAMPLING_METHOD = "euler"
DEFAULT_OUTPUT_NAME = None

AUDIO_SUFFIXES = {".flac", ".wav"}
VIDEO_SUFFIX = ".mp4"
JSONL_SUFFIX = ".jsonl"


@dataclass(frozen=True)
class DatasetKind:
    prefix: str
    path_help: tuple[str, str]
    override_prefix: str


DATASET_KINDS = (
    DatasetKind(
        prefix="audiocaps_full",
        path_help=("--audio-path", "--csv-path"),
        override_prefix="AudioCaps_full",
    ),
    DatasetKind(
        prefix="audiocaps",
        path_help=("--audio-path", "--csv-path"),
        override_prefix="AudioCaps",
    ),
    DatasetKind(
        prefix="moviegen",
        path_help=("--moviegen-video-path", "--moviegen-jsonl-path"),
        override_prefix="MovieGen",
    ),
    DatasetKind(
        prefix="vggsound",
        path_help=("--vgg-video-path", "--vgg-csv-path"),
        override_prefix="VGGSound",
    ),
)


def _fail(message: str) -> None:
    raise ValueError(message)


def _validate_name_token(value: str, field: str) -> str:
    if value is None:
        _fail(f"{field} is required")
    value = value.strip()
    if not value:
        _fail(f"{field} must be non-empty")
    if any(ch.isspace() for ch in value):
        _fail(f"{field} must not contain whitespace")
    if any(sep in value for sep in ("/", "\\")):
        _fail(f"{field} must not contain path separators")
    if any(ch in value for ch in ("\x00", "\n", "\r", "\t")):
        _fail(f"{field} must not contain control characters")
    return value


def _validate_dataset_name(dataset: str) -> str:
    dataset = _validate_name_token(dataset, "dataset")
    for prefix in SUPPORTED_PREFIXES:
        if dataset.startswith(prefix):
            return dataset
    _fail(
        "dataset must start with one of: " + ", ".join(SUPPORTED_PREFIXES)
        + " (custom suffixes after the prefix are allowed)"
    )
    return dataset


def _validate_model(model: str) -> str:
    model = _validate_name_token(model, "model")
    if model not in SUPPORTED_MODELS:
        _fail(f"unsupported model: {model}. Choose one of: {', '.join(SUPPORTED_MODELS)}")
    return model


def _validate_output_name(output_name: str | None) -> str | None:
    if output_name is None:
        return None
    return _validate_name_token(output_name, "output_name")


def _validate_positive_int(value: int, field: str) -> int:
    if value <= 0:
        _fail(f"{field} must be a positive integer")
    return value


def _validate_positive_float(value: float, field: str) -> float:
    if value <= 0:
        _fail(f"{field} must be > 0")
    return value


def _validate_nonnegative_float(value: float, field: str) -> float:
    if value < 0:
        _fail(f"{field} must be >= 0")
    return value


def _resolve_dataset_kind(dataset: str) -> DatasetKind:
    for kind in DATASET_KINDS:
        if dataset.startswith(kind.prefix):
            return kind
    _fail(
        f"unsupported dataset: {dataset}. Supported prefixes: "
        + ", ".join(SUPPORTED_PREFIXES)
    )
    raise AssertionError("unreachable")


def _expand_path(value: str | None, field: str) -> Path:
    if value is None:
        _fail(f"{field} is required for this dataset")
    value = value.strip()
    if not value:
        _fail(f"{field} must be non-empty")
    if any(ch in value for ch in ("\x00", "\n", "\r")):
        _fail(f"{field} must not contain control characters")
    return Path(value).expanduser()


def _iter_files(path: Path, suffix: str) -> list[Path]:
    return [item for item in sorted(path.iterdir()) if item.is_file() and item.suffix.lower() == suffix]


def _iter_media_files(path: Path, suffixes: set[str]) -> list[Path]:
    return [item for item in sorted(path.iterdir()) if item.is_file() and item.suffix.lower() in suffixes]


def _duplicate_values(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for value in values:
        if value in seen and value not in dupes:
            dupes.append(value)
        seen.add(value)
    return dupes


def _warn(message: str) -> None:
    print(f"WARN: {message}", file=sys.stderr)


def _validate_audio_caps(audio_path: Path, csv_path: Path, *, strict: bool) -> None:
    if not audio_path.exists():
        _fail(f"audio_path does not exist: {audio_path}")
    if not audio_path.is_dir():
        _fail(f"audio_path must be a directory: {audio_path}")
    if not csv_path.exists():
        _fail(f"csv_path does not exist: {csv_path}")
    if not csv_path.is_file():
        _fail(f"csv_path must be a file: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            _fail(f"AudioCaps CSV has no header row: {csv_path}")
        required = {"name", "caption"}
        missing = sorted(required - set(reader.fieldnames))
        if missing:
            _fail(f"AudioCaps CSV is missing required columns: {', '.join(missing)}")
        rows = [row for row in reader]

    if not rows:
        _fail(f"AudioCaps CSV is empty: {csv_path}")

    names: list[str] = []
    blank_captions: list[int] = []
    for idx, row in enumerate(rows, start=2):
        name = (row.get("name") or "").strip()
        caption = (row.get("caption") or "").strip()
        if not name:
            _fail(f"AudioCaps row {idx} has an empty name")
        if any(ch.isspace() for ch in name) or any(sep in name for sep in ("/", "\\")):
            _fail(f"AudioCaps row {idx} has an unsafe name: {name}")
        if not caption:
            blank_captions.append(idx)
        names.append(name)

    duplicates = _duplicate_values(names)
    if duplicates:
        _fail("AudioCaps CSV has duplicate output names: " + ", ".join(duplicates[:8]))

    audio_files = _iter_media_files(audio_path, AUDIO_SUFFIXES)
    if not audio_files:
        _warn(f"audio_path contains no .wav or .flac files: {audio_path}")

    if blank_captions:
        message = f"AudioCaps CSV has empty captions on rows: {', '.join(map(str, blank_captions[:8]))}"
        if strict:
            _fail(message)
        _warn(message)


def _validate_vggsound(video_path: Path, csv_path: Path, *, strict: bool) -> None:
    if not video_path.exists():
        _fail(f"vgg video path does not exist: {video_path}")
    if not video_path.is_dir():
        _fail(f"vgg video path must be a directory: {video_path}")
    if not csv_path.exists():
        _fail(f"vgg csv path does not exist: {csv_path}")
    if not csv_path.is_file():
        _fail(f"vgg csv path must be a file: {csv_path}")

    video_files = _iter_files(video_path, VIDEO_SUFFIX)
    if not video_files:
        _fail(f"no .mp4 files found in video_path: {video_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        _fail(f"VGGSound CSV is empty: {csv_path}")

    video_names = {item.name for item in video_files}
    expected_names: list[str] = []
    missing: list[str] = []
    duplicate_names: list[str] = []
    seen_names: set[str] = set()

    for idx, row in enumerate(rows, start=1):
        if len(row) != 4:
            _fail(f"VGGSound CSV row {idx} must have exactly 4 columns: id, sec, caption, split")
        video_id, sec_text, caption, split = (cell.strip() for cell in row)
        if not video_id:
            _fail(f"VGGSound CSV row {idx} has an empty id")
        if not caption:
            _fail(f"VGGSound CSV row {idx} has an empty caption")
        if split != "test":
            continue
        try:
            start_sec = int(sec_text)
        except ValueError as exc:
            raise ValueError(f"VGGSound row {idx} has a non-integer sec value: {sec_text}") from exc
        name = f"{video_id}_{start_sec:06d}"
        if name in seen_names:
            duplicate_names.append(name)
        seen_names.add(name)
        expected_names.append(name)
        filename = f"{name}.mp4"
        if filename not in video_names:
            missing.append(filename)

    if not expected_names:
        _fail(f"VGGSound CSV has no test rows: {csv_path}")
    if duplicate_names:
        _fail("VGGSound CSV would overwrite generated outputs: " + ", ".join(duplicate_names[:8]))
    if missing:
        message = f"{len(missing)} expected VGGSound videos are missing; first few: {', '.join(missing[:8])}"
        if len(missing) == len(expected_names):
            _fail(message)
        if strict:
            _fail(message)
        _warn(message)


def _validate_moviegen(video_path: Path, jsonl_path: Path, *, strict: bool) -> None:
    if not video_path.exists():
        _fail(f"moviegen video path does not exist: {video_path}")
    if not video_path.is_dir():
        _fail(f"moviegen video path must be a directory: {video_path}")
    if not jsonl_path.exists():
        _fail(f"moviegen jsonl path does not exist: {jsonl_path}")
    if not jsonl_path.is_dir():
        _fail(f"moviegen jsonl path must be a directory: {jsonl_path}")

    video_files = _iter_files(video_path, VIDEO_SUFFIX)
    jsonl_files = _iter_files(jsonl_path, JSONL_SUFFIX)
    if not video_files:
        _fail(f"no .mp4 files found in video_path: {video_path}")
    if not jsonl_files:
        _fail(f"no .jsonl files found in jsonl_path: {jsonl_path}")

    jsonl_map = {item.stem: item for item in jsonl_files}
    missing_json = [item.stem for item in video_files if item.stem not in jsonl_map]
    if missing_json:
        message = f"{len(missing_json)} MovieGen metadata files are missing; first few: {', '.join(missing_json[:8])}"
        if len(missing_json) == len(video_files):
            _fail(message)
        if strict:
            _fail(message)
        _warn(message)

    bad_json: list[str] = []
    empty_prompt: list[str] = []
    for video_file in video_files:
        json_file = jsonl_map.get(video_file.stem)
        if json_file is None:
            continue
        try:
            with json_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"MovieGen metadata is not valid JSON: {json_file}") from exc
        if not isinstance(payload, dict):
            bad_json.append(json_file.name)
            continue
        prompt = payload.get("audio_prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            empty_prompt.append(json_file.name)

    if bad_json:
        _fail("MovieGen metadata must contain a JSON object per file: " + ", ".join(bad_json[:8]))
    if empty_prompt:
        message = "MovieGen metadata files are missing a non-empty audio_prompt: " + ", ".join(empty_prompt[:8])
        if strict:
            _fail(message)
        _warn(message)


def _build_overrides(
    *,
    dataset: str,
    model: str,
    duration_s: float,
    batch_size: int,
    num_workers: int,
    compile_enabled: bool,
    amp_enabled: bool,
    seed: int,
    cfg_strength: float,
    sampling_method: str,
    sampling_num_steps: int,
    output_name: str | None,
    dataset_kind: DatasetKind,
    paths: dict[str, Path],
) -> list[str]:
    overrides = [
        f"exp_id={model}-eval",
        f"dataset={dataset}",
        f"model={model}",
        f"duration_s={duration_s:g}",
        f"batch_size={batch_size}",
        f"num_workers={num_workers}",
        f"compile={'True' if compile_enabled else 'False'}",
        f"amp={'True' if amp_enabled else 'False'}",
        f"seed={seed}",
        f"cfg_strength={cfg_strength:g}",
        f"sampling.method={sampling_method}",
        f"sampling.num_steps={sampling_num_steps}",
    ]
    if output_name is not None:
        overrides.append(f"output_name={output_name}")

    if dataset_kind.prefix.startswith("audiocaps"):
        overrides.extend(
            [
                f"eval_data.{dataset_kind.override_prefix}.audio_path={paths['audio_path']}",
                f"eval_data.{dataset_kind.override_prefix}.csv_path={paths['csv_path']}",
            ]
        )
    elif dataset_kind.prefix == "vggsound":
        overrides.extend(
            [
                f"eval_data.VGGSound.video_path={paths['video_path']}",
                f"eval_data.VGGSound.csv_path={paths['csv_path']}",
            ]
        )
    elif dataset_kind.prefix == "moviegen":
        overrides.extend(
            [
                f"eval_data.MovieGen.video_path={paths['video_path']}",
                f"eval_data.MovieGen.jsonl_path={paths['jsonl_path']}",
            ]
        )
    else:
        raise AssertionError(f"Unexpected dataset kind: {dataset_kind.prefix}")

    return overrides


def build_command(
    *,
    omp_num_threads: int,
    nproc_per_node: int,
    dataset: str,
    model: str,
    duration_s: float,
    batch_size: int,
    num_workers: int,
    compile_enabled: bool,
    amp_enabled: bool,
    seed: int,
    cfg_strength: float,
    sampling_method: str,
    sampling_num_steps: int,
    output_name: str | None,
    paths: dict[str, Path],
) -> str:
    dataset_kind = _resolve_dataset_kind(dataset)
    overrides = _build_overrides(
        dataset=dataset,
        model=model,
        duration_s=duration_s,
        batch_size=batch_size,
        num_workers=num_workers,
        compile_enabled=compile_enabled,
        amp_enabled=amp_enabled,
        seed=seed,
        cfg_strength=cfg_strength,
        sampling_method=sampling_method,
        sampling_num_steps=sampling_num_steps,
        output_name=output_name,
        dataset_kind=dataset_kind,
        paths=paths,
    )
    parts = [
        f"OMP_NUM_THREADS={omp_num_threads}",
        "torchrun",
        "--standalone",
        f"--nproc_per_node={nproc_per_node}",
        "batch_eval.py",
        *overrides,
    ]
    return shlex.join(parts)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and print a safe MMAudio batch-evaluation command."
    )
    parser.add_argument("--dataset", required=True, help="Dataset selector passed to batch_eval.py")
    parser.add_argument("--model", default="small_16k", choices=SUPPORTED_MODELS)
    parser.add_argument("--duration-s", type=float, default=DEFAULT_DURATION_S)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--num-workers", type=int, default=DEFAULT_NUM_WORKERS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--cfg-strength", type=float, default=DEFAULT_CFG_STRENGTH)
    parser.add_argument("--sampling-method", default=DEFAULT_SAMPLING_METHOD)
    parser.add_argument("--sampling-num-steps", type=int, default=DEFAULT_NUM_STEPS)
    parser.add_argument("--omp-num-threads", type=int, default=DEFAULT_OMP_NUM_THREADS)
    parser.add_argument("--nproc-per-node", type=int, default=1)
    parser.add_argument("--output-name", default=DEFAULT_OUTPUT_NAME)
    parser.add_argument(
        "--compile",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable or disable torch compile in the rendered command.",
    )
    parser.add_argument(
        "--amp",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable bfloat16 autocast in the rendered command.",
    )
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Validate local dataset paths and metadata before printing the command.",
    )

    # Dataset-specific path inputs.
    parser.add_argument("--audio-path", default=None, help="AudioCaps or AudioCaps_full audio directory")
    parser.add_argument("--csv-path", default=None, help="AudioCaps or AudioCaps_full CSV path")
    parser.add_argument("--vgg-video-path", default=None, help="VGGSound video directory")
    parser.add_argument("--vgg-csv-path", default=None, help="VGGSound CSV path")
    parser.add_argument("--moviegen-video-path", default=None, help="MovieGen video directory")
    parser.add_argument("--moviegen-jsonl-path", default=None, help="MovieGen metadata directory")
    return parser.parse_args(argv)


def _collect_paths(args: argparse.Namespace, kind: DatasetKind) -> dict[str, Path]:
    if kind.prefix.startswith("audiocaps"):
        return {
            "audio_path": _expand_path(args.audio_path, "--audio-path"),
            "csv_path": _expand_path(args.csv_path, "--csv-path"),
        }
    if kind.prefix == "vggsound":
        return {
            "video_path": _expand_path(args.vgg_video_path, "--vgg-video-path"),
            "csv_path": _expand_path(args.vgg_csv_path, "--vgg-csv-path"),
        }
    if kind.prefix == "moviegen":
        return {
            "video_path": _expand_path(args.moviegen_video_path, "--moviegen-video-path"),
            "jsonl_path": _expand_path(args.moviegen_jsonl_path, "--moviegen-jsonl-path"),
        }
    raise AssertionError(f"Unexpected dataset kind: {kind.prefix}")


def _validate_paths(kind: DatasetKind, paths: dict[str, Path]) -> None:
    if kind.prefix.startswith("audiocaps"):
        _validate_audio_caps(paths["audio_path"], paths["csv_path"], strict=False)
    elif kind.prefix == "vggsound":
        _validate_vggsound(paths["video_path"], paths["csv_path"], strict=False)
    elif kind.prefix == "moviegen":
        _validate_moviegen(paths["video_path"], paths["jsonl_path"], strict=False)
    else:
        raise AssertionError(f"Unexpected dataset kind: {kind.prefix}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        dataset = _validate_dataset_name(args.dataset)
        model = _validate_model(args.model)
        output_name = _validate_output_name(args.output_name)
        duration_s = _validate_positive_float(args.duration_s, "duration-s")
        batch_size = _validate_positive_int(args.batch_size, "batch-size")
        num_workers = _validate_nonnegative_float(args.num_workers, "num-workers")
        if int(num_workers) != num_workers:
            _fail("num-workers must be an integer")
        num_workers = int(num_workers)
        seed = _validate_nonnegative_float(args.seed, "seed")
        if int(seed) != seed:
            _fail("seed must be an integer")
        seed = int(seed)
        cfg_strength = _validate_positive_float(args.cfg_strength, "cfg-strength")
        sampling_method = _validate_name_token(args.sampling_method, "sampling-method")
        sampling_num_steps = _validate_positive_int(args.sampling_num_steps, "sampling-num-steps")
        omp_num_threads = _validate_positive_int(args.omp_num_threads, "omp-num-threads")
        nproc_per_node = _validate_positive_int(args.nproc_per_node, "nproc-per-node")
        dataset_kind = _resolve_dataset_kind(dataset)
        paths = _collect_paths(args, dataset_kind)

        if args.check_paths:
            _validate_paths(dataset_kind, paths)

        command = build_command(
            omp_num_threads=omp_num_threads,
            nproc_per_node=nproc_per_node,
            dataset=dataset,
            model=model,
            duration_s=duration_s,
            batch_size=batch_size,
            num_workers=num_workers,
            compile_enabled=bool(args.compile),
            amp_enabled=bool(args.amp),
            seed=seed,
            cfg_strength=cfg_strength,
            sampling_method=sampling_method,
            sampling_num_steps=sampling_num_steps,
            output_name=output_name,
            paths=paths,
        )
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
