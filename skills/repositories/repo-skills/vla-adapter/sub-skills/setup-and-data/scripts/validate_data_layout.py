#!/usr/bin/env python3
"""Safe layout validator for VLA-Adapter setup and data paths.

The script only inspects local files and prints PASS/WARN/FAIL messages.
It never downloads data, mutates source files, or launches training/evaluation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple


LIBERO_SUITES: Sequence[Tuple[str, str]] = (
    ("Spatial", "libero_spatial_no_noops"),
    ("Object", "libero_object_no_noops"),
    ("Goal", "libero_goal_no_noops"),
    ("Long", "libero_10_no_noops"),
)

CHECKPOINT_REQUIRED_FILES = ("config.json", "dataset_statistics.json")
VLM_CONFIG_REQUIRED_FILES = (
    "config.json",
    "configuration_prismatic.py",
    "modeling_prismatic.py",
    "processing_prismatic.py",
    "processor_config.json",
)
VLM_CONFIG_OPTIONAL_FILES = (
    "preprocessor_config.json",
    "generation_config.json",
    "added_tokens.json",
    "merges.txt",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
)


class Reporter:
    def __init__(self) -> None:
        self.pass_count = 0
        self.warn_count = 0
        self.fail_count = 0

    def pass_(self, message: str) -> None:
        self.pass_count += 1
        print(f"PASS: {message}")

    def warn(self, message: str) -> None:
        self.warn_count += 1
        print(f"WARN: {message}")

    def fail(self, message: str) -> None:
        self.fail_count += 1
        print(f"FAIL: {message}")

    def summary(self, require_existing: bool) -> int:
        if self.pass_count or self.warn_count or self.fail_count:
            print(
                f"SUMMARY: {self.pass_count} PASS, {self.warn_count} WARN, {self.fail_count} FAIL"
            )
        if self.fail_count > 0:
            return 1
        if require_existing and self.warn_count > 0:
            return 1
        return 0


def normalize_path(path: Optional[Path]) -> Optional[Path]:
    if path is None:
        return None
    try:
        return path.expanduser()
    except Exception:
        return path


def human_join(items: Iterable[str]) -> str:
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def choose_best_root(candidates: Sequence[Path], probe_fn) -> Tuple[Optional[Path], int]:
    best_root: Optional[Path] = None
    best_score = -1
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        score = probe_fn(candidate)
        if score > best_score:
            best_root = candidate
            best_score = score
    if best_score < 0:
        return None, 0
    return best_root, best_score


def count_files(path: Path, pattern: str) -> int:
    return sum(1 for _ in path.glob(pattern))


def inspect_vlm_config_dir(path: Optional[Path], reporter: Reporter, require_existing: bool) -> None:
    if path is None:
        reporter.warn("--vlm-config-dir not provided; skipped VLM config bundle check.")
        return

    if not path.exists():
        message = f"VLM config directory is missing: {path}"
        (reporter.fail if require_existing else reporter.warn)(message)
        return
    if not path.is_dir():
        message = f"VLM config path is not a directory: {path}"
        (reporter.fail if require_existing else reporter.warn)(message)
        return

    missing_required = [name for name in VLM_CONFIG_REQUIRED_FILES if not (path / name).is_file()]
    if missing_required:
        message = (
            f"VLM config bundle is incomplete at {path}; missing {human_join(missing_required)}"
        )
        (reporter.fail if require_existing else reporter.warn)(message)
    else:
        reporter.pass_(f"VLM config bundle present at {path}")

    optional_present = [name for name in VLM_CONFIG_OPTIONAL_FILES if (path / name).is_file()]
    if optional_present:
        reporter.pass_(f"Optional VLM config files found: {human_join(optional_present)}")

    config_json = path / "config.json"
    if config_json.is_file():
        try:
            payload = json.loads(config_json.read_text())
            model_type = payload.get("model_type", "<missing>")
            llm_backbone_id = payload.get("llm_backbone_id", "<missing>")
            auto_map = payload.get("auto_map", {})
            reporter.pass_(
                f"Parsed config.json (model_type={model_type}, llm_backbone_id={llm_backbone_id}, auto_map_keys={human_join(sorted(auto_map)) if auto_map else '<none>'})"
            )
        except Exception as exc:  # pragma: no cover - defensive path
            message = f"Could not parse {config_json}: {exc}"
            (reporter.fail if require_existing else reporter.warn)(message)


def inspect_checkpoint(path: Optional[Path], reporter: Reporter, require_existing: bool) -> None:
    if path is None:
        reporter.warn("--checkpoint not provided; skipped checkpoint-layout check.")
        return

    if not path.exists():
        message = f"Checkpoint path does not exist: {path}"
        (reporter.fail if require_existing else reporter.warn)(message)
        return

    if path.is_file():
        if path.suffix != ".pt" or path.parent.name != "checkpoints":
            message = (
                f"Checkpoint file should be a .pt file under a checkpoints/ directory: {path}"
            )
            (reporter.fail if require_existing else reporter.warn)(message)
        else:
            reporter.pass_(f"Checkpoint file layout looks valid: {path}")
        run_dir = path.parents[1] if len(path.parents) >= 2 else path.parent
    else:
        run_dir = path
        reporter.pass_(f"Checkpoint directory exists: {run_dir}")

    stats_json = run_dir / "dataset_statistics.json"
    checkpoints_dir = run_dir / "checkpoints"

    for required in CHECKPOINT_REQUIRED_FILES:
        candidate = run_dir / required
        if candidate.is_file():
            reporter.pass_(f"Found checkpoint companion file: {candidate}")
        else:
            message = f"Missing checkpoint companion file: {candidate}"
            (reporter.fail if require_existing else reporter.warn)(message)

    if checkpoints_dir.is_dir():
        pt_files = sorted(checkpoints_dir.glob("*.pt"))
        if pt_files:
            reporter.pass_(
                f"Found {len(pt_files)} checkpoint file(s) under {checkpoints_dir}"
            )
        else:
            message = f"No .pt checkpoints were found under {checkpoints_dir}"
            (reporter.fail if require_existing else reporter.warn)(message)
    else:
        message = f"Missing checkpoints directory: {checkpoints_dir}"
        (reporter.fail if require_existing else reporter.warn)(message)

    if stats_json.is_file():
        try:
            stats = json.loads(stats_json.read_text())
            top_level = sorted(stats.keys())
            reporter.pass_(
                f"dataset_statistics.json parsed successfully with keys: {human_join(top_level[:6]) if top_level else '<empty>'}"
            )
        except Exception as exc:  # pragma: no cover - defensive path
            message = f"Could not parse {stats_json}: {exc}"
            (reporter.fail if require_existing else reporter.warn)(message)


def inspect_libero_root(path: Path, reporter: Reporter, require_existing: bool) -> None:
    candidates = [path]
    nested = path / "libero"
    if nested.is_dir() and nested != path:
        candidates.append(nested)

    def score(candidate: Path) -> int:
        total = 0
        for _, suite_name in LIBERO_SUITES:
            if (candidate / suite_name / "1.0.0").is_dir():
                total += 1
        return total

    best_root, best_score = choose_best_root(candidates, score)
    if best_root is None or best_score == 0:
        message = f"No recognized LIBERO TFDS suites were found under {path}"
        (reporter.fail if require_existing else reporter.warn)(message)
        return

    present = []
    for label, suite_name in LIBERO_SUITES:
        suite_dir = best_root / suite_name
        version_dir = suite_dir / "1.0.0"
        if suite_dir.is_dir() and version_dir.is_dir():
            present.append((label, version_dir))

    reporter.pass_(
        f"Using LIBERO data root for layout inspection: {best_root} ({len(present)} recognized suite(s): {human_join(label for label, _ in present) if present else '<none>'})"
    )

    if not present:
        message = f"No LIBERO suites were fully materialized under {best_root}"
        (reporter.fail if require_existing else reporter.warn)(message)
        return

    for label, version_dir in present:
        json_count = count_files(version_dir, "*.json")
        tfrecord_count = len(list(version_dir.rglob("*.tfrecord*")))
        if json_count == 0 or tfrecord_count == 0:
            message = (
                f"LIBERO {label} layout is incomplete at {version_dir} "
                f"({json_count} json file(s), {tfrecord_count} TFRecord shard(s)); "
                "this check does not establish native asset readiness"
            )
            (reporter.fail if require_existing else reporter.warn)(message)
        else:
            reporter.pass_(
                f"LIBERO {label} TFDS files observed at {version_dir} "
                f"({json_count} json file(s), {tfrecord_count} TFRecord shard(s)); "
                "this check does not establish native asset readiness"
            )


def inspect_calvin_root(path: Path, reporter: Reporter, require_existing: bool) -> None:
    candidates = [path, path / "calvin_abc", path / "calvin_abc_rlds"]

    best_root: Optional[Path] = None
    best_version_dir: Optional[Path] = None
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        if (candidate / "1.0.0").is_dir():
            best_root = candidate
            best_version_dir = candidate / "1.0.0"
            break
        for builder_name in ("calvin_abc", "calvin_abc_rlds"):
            version_dir = candidate / builder_name / "1.0.0"
            if version_dir.is_dir():
                best_root = candidate / builder_name
                best_version_dir = version_dir
                break
        if best_version_dir is not None:
            break

    if best_root is None or best_version_dir is None:
        message = f"No CALVIN TFDS builder directory was found under {path}"
        if (path / "dataset").is_dir() or (path / "calvin_models").is_dir():
            message += " (this looks like the native CALVIN checkout rather than an RLDS root)"
        (reporter.fail if require_existing else reporter.warn)(message)
        return

    if best_root.name == "calvin_abc_rlds":
        reporter.pass_(
            f"Found CALVIN archive alias for layout inspection: {best_root}; training configs usually point at calvin_abc"
        )
    else:
        reporter.pass_(f"Using CALVIN data root for layout inspection: {best_root}")

    json_count = count_files(best_version_dir, "*.json")
    tfrecord_count = len(list(best_version_dir.rglob("*.tfrecord*")))
    if json_count == 0 or tfrecord_count == 0:
        message = (
            f"CALVIN TFDS layout is incomplete at {best_version_dir} "
            f"({json_count} json file(s), {tfrecord_count} TFRecord shard(s)); "
            "this check does not establish native asset readiness"
        )
        (reporter.fail if require_existing else reporter.warn)(message)
    else:
        reporter.pass_(
            f"CALVIN TFDS files observed at {best_version_dir} "
            f"({json_count} json file(s), {tfrecord_count} TFRecord shard(s)); "
            "this check does not establish native asset readiness"
        )


def inspect_aloha_root(path: Path, reporter: Reporter, require_existing: bool) -> None:
    candidates = [path]
    nested = path / "tfds"
    if nested.is_dir() and nested != path:
        candidates.append(nested)

    def score(candidate: Path) -> int:
        return sum(1 for child in candidate.iterdir() if child.is_dir() and (child / "1.0.0").is_dir())

    best_root, best_score = choose_best_root(candidates, score)
    if best_root is None or best_score == 0:
        message = f"No TFDS-style ALOHA dataset directories were found under {path}"
        (reporter.fail if require_existing else reporter.warn)(message)
        return

    builder_dirs = sorted(
        child for child in best_root.iterdir() if child.is_dir() and (child / "1.0.0").is_dir()
    )
    names = [child.name for child in builder_dirs]
    reporter.pass_(
        f"Using ALOHA TFDS root for layout inspection: {best_root} ({len(builder_dirs)} dataset directory(s): {human_join(names[:5])})"
    )

    for child in builder_dirs:
        version_dir = child / "1.0.0"
        json_count = count_files(version_dir, "*.json")
        tfrecord_count = len(list(version_dir.rglob("*.tfrecord*")))
        if json_count == 0 or tfrecord_count == 0:
            message = (
                f"ALOHA dataset directory {version_dir} looks incomplete "
                f"({json_count} json file(s), {tfrecord_count} TFRecord shard(s)); "
                "this check does not establish native asset readiness"
            )
            (reporter.fail if require_existing else reporter.warn)(message)
        else:
            reporter.pass_(
                f"ALOHA TFDS files observed at {version_dir} "
                f"({json_count} json file(s), {tfrecord_count} TFRecord shard(s)); "
                "this check does not establish native asset readiness"
            )


def inspect_data_root(benchmark: str, path: Optional[Path], reporter: Reporter, require_existing: bool) -> None:
    if path is None:
        reporter.warn("--data-root not provided; skipped benchmark data-layout check.")
        return

    if not path.exists():
        message = f"Data root does not exist: {path}"
        (reporter.fail if require_existing else reporter.warn)(message)
        return

    if not path.is_dir():
        message = f"Data root is not a directory: {path}"
        (reporter.fail if require_existing else reporter.warn)(message)
        return

    reporter.pass_(f"Data root exists: {path}")

    if benchmark == "libero":
        inspect_libero_root(path, reporter, require_existing)
    elif benchmark == "calvin":
        inspect_calvin_root(path, reporter, require_existing)
    elif benchmark == "aloha":
        inspect_aloha_root(path, reporter, require_existing)
    else:  # pragma: no cover - argparse constrains this already
        reporter.fail(f"Unknown benchmark: {benchmark}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate VLA-Adapter data roots, checkpoint layout, and VLM config bundles safely."
    )
    parser.add_argument(
        "--benchmark",
        required=True,
        choices=("libero", "calvin", "aloha"),
        help="Benchmark family to validate.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="Local dataset root to inspect.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="Local checkpoint file or run directory to inspect.",
    )
    parser.add_argument(
        "--vlm-config-dir",
        type=Path,
        default=None,
        help="Local Prismatic/VLM config directory to inspect.",
    )
    parser.add_argument(
        "--require-existing",
        action="store_true",
        help="Treat every missing requested path as a failure instead of a warning.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    reporter = Reporter()
    data_root = normalize_path(args.data_root)
    checkpoint = normalize_path(args.checkpoint)
    vlm_config_dir = normalize_path(args.vlm_config_dir)

    inspect_data_root(args.benchmark, data_root, reporter, args.require_existing)
    inspect_checkpoint(checkpoint, reporter, args.require_existing)
    inspect_vlm_config_dir(vlm_config_dir, reporter, args.require_existing)

    return reporter.summary(args.require_existing)


if __name__ == "__main__":
    raise SystemExit(main())
