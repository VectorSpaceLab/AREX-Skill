#!/usr/bin/env python3
"""Validate ALAE data path conventions without importing ALAE source code.

The checker reads a simple ALAE YAML config, validates TFRecord path patterns,
and optionally checks repository-relative sample/style/output directories. It is
read-only and has no network, training, or dataset conversion side effects.

Example:
    python scripts/validate_alae_data_layout.py \
      --config-file configs/ffhq.yaml \
      --repo-root /path/to/ALAE \
      --world-size 8
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Any

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Public defaults distilled from ALAE defaults.py. Keeping them here lets this
# checker validate effective config values without importing the source repo.
ALAE_DATASET_DEFAULTS: dict[str, Any] = {
    "PATH": "celeba/data_fold_%d_lod_%d.pkl",
    "PATH_TEST": "",
    "FFHQ_SOURCE": "/data/datasets/ffhq-dataset/tfrecords/ffhq/ffhq-r%02d.tfrecords",
    "PART_COUNT": 1,
    "PART_COUNT_TEST": 1,
    "SIZE": 70000,
    "SIZE_TEST": 10000,
    "FLIP_IMAGES": True,
    "SAMPLES_PATH": "dataset_samples/faces/realign128x128",
    "STYLE_MIX_PATH": "style_mixing/test_images/set_celeba/",
    "MAX_RESOLUTION_LEVEL": 10,
}
ALAE_OUTPUT_DIR_DEFAULT = "results"


class Reporter:
    def __init__(self, *, strict: bool = False) -> None:
        self.strict = strict
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.infos: list[str] = []

    def info(self, message: str) -> None:
        self.infos.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def missing(self, message: str) -> None:
        if self.strict:
            self.error(message)
        else:
            self.warn(message)

    def print(self) -> None:
        for message in self.infos:
            print(f"[OK] {message}")
        for message in self.warnings:
            print(f"[WARN] {message}")
        for message in self.errors:
            print(f"[ERROR] {message}")
        if self.errors:
            print(f"FAIL: {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
        elif self.warnings:
            print(f"PASS with warnings: {len(self.warnings)} warning(s)")
        else:
            print("PASS: ALAE data layout checks completed without warnings")

    def exit_code(self) -> int:
        return 1 if self.errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate an ALAE config's data paths, sample directories, style-mixing layout, and TFRecord patterns.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config-file", type=Path, required=True, help="Path to an ALAE YAML config file.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional ALAE checkout root used to resolve relative SAMPLES_PATH, STYLE_MIX_PATH, and OUTPUT_DIR values.",
    )
    parser.add_argument(
        "--world-size",
        type=int,
        default=1,
        help="Expected training world size/GPU process count; validates PART_COUNT divisibility.",
    )
    parser.add_argument(
        "--check-tfrecords",
        action="store_true",
        help="Also check existence of every expected train/test TFRecord shard. This can produce many warnings.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing sample/style/output directories and empty image layouts as errors instead of warnings.",
    )
    return parser


def strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for idx, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:idx]
    return line


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        try:
            return ast.literal_eval(value)
        except Exception:
            return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        try:
            return ast.literal_eval(value)
        except Exception:
            return value
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except Exception:
            return value
    if re.fullmatch(r"[-+]?\d+\.\d*", value):
        try:
            return float(value)
        except Exception:
            return value
    return value


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = strip_comment(raw).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        if ":" not in text:
            raise ValueError(f"line {line_number}: expected 'key: value' syntax, got {text!r}")
        key, value = text.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"line {line_number}: empty key")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"line {line_number}: invalid indentation")
        parent = stack[-1][1]
        value = value.strip()
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)
    return root


def get_nested(mapping: dict[str, Any], dotted: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in dotted.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def merge_alae_defaults(raw_cfg: dict[str, Any], reporter: Reporter) -> dict[str, Any]:
    """Merge the subset of ALAE defaults.py that affects data layout."""
    cfg = dict(raw_cfg)
    raw_dataset = raw_cfg.get("DATASET", {})
    if raw_dataset is None:
        raw_dataset = {}
    if not isinstance(raw_dataset, dict):
        reporter.error("DATASET section must be a mapping")
        raw_dataset = {}
    dataset = dict(ALAE_DATASET_DEFAULTS)
    dataset.update(raw_dataset)
    cfg["DATASET"] = dataset
    if "OUTPUT_DIR" not in cfg:
        cfg["OUTPUT_DIR"] = ALAE_OUTPUT_DIR_DEFAULT
    return cfg


def as_int(value: Any, name: str, reporter: Reporter, *, default: int | None = None) -> int | None:
    if value is None:
        if default is not None:
            return default
        reporter.error(f"{name} is missing")
        return None
    try:
        return int(value)
    except Exception:
        reporter.error(f"{name} must be an integer, got {value!r}")
        return None


def format_pattern(pattern: Any, args: tuple[int, ...], name: str, reporter: Reporter) -> str | None:
    if pattern is None or pattern == "":
        reporter.warn(f"{name} is empty or absent")
        return None
    if not isinstance(pattern, str):
        reporter.error(f"{name} must be a string path pattern, got {type(pattern).__name__}")
        return None
    try:
        return pattern % args
    except Exception as exc:
        reporter.error(f"{name} does not accept {len(args)} integer placeholder(s): {pattern!r} ({exc})")
        return None


def resolve_path(path_value: Any, repo_root: Path | None) -> Path | None:
    if path_value is None:
        return None
    value = str(path_value)
    if value == "" or value == "no_path":
        return None
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    if repo_root is None:
        return None
    return repo_root / path


def count_images(directory: Path) -> int:
    return sum(1 for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)


def has_numbered_image(directory: Path, idx: int) -> bool:
    for suffix in (".png", ".jpg", ".jpeg"):
        if (directory / f"{idx}{suffix}").is_file():
            return True
    return False


def check_path_contains_data_prefix(name: str, value: Any, reporter: Reporter) -> None:
    if isinstance(value, str) and value.startswith("/data/datasets"):
        reporter.warn(f"{name} uses the source default /data/datasets prefix; override it or create a deliberate symlink if your data lives elsewhere")


def check_tfrecord_files(
    *,
    pattern: str,
    name: str,
    part_count: int,
    max_lod: int,
    repo_root: Path | None,
    reporter: Reporter,
) -> None:
    missing: list[str] = []
    unresolved_relative = False
    for lod in range(2, max_lod + 1):
        for part in range(part_count):
            formatted = pattern % (lod, part)
            path = Path(formatted).expanduser()
            if not path.is_absolute():
                if repo_root is None:
                    unresolved_relative = True
                    continue
                path = repo_root / path
            if not path.exists():
                missing.append(str(path))
    if unresolved_relative:
        reporter.warn(f"{name} contains relative paths; pass --repo-root to check TFRecord existence")
    if missing:
        preview = "; ".join(missing[:5])
        more = "" if len(missing) <= 5 else f"; ... {len(missing) - 5} more"
        reporter.warn(f"{name} missing {len(missing)} expected TFRecord shard(s): {preview}{more}")
    elif not unresolved_relative:
        reporter.info(f"{name} expected TFRecord shards exist for LOD 2..{max_lod} and {part_count} part(s)")


def infer_repo_root(config_file: Path, explicit_repo_root: Path | None) -> Path | None:
    if explicit_repo_root is not None:
        return explicit_repo_root.expanduser().resolve()
    parent = config_file.parent
    if parent.name == "configs":
        return parent.parent.resolve()
    return None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    reporter = Reporter(strict=args.strict)

    config_file = args.config_file.expanduser()
    if not config_file.is_file():
        parser.error(f"--config-file does not exist or is not a file: {config_file}")
    if args.world_size < 1:
        parser.error("--world-size must be a positive integer")

    repo_root = infer_repo_root(config_file.resolve(), args.repo_root)
    if repo_root is not None and not repo_root.is_dir():
        reporter.error(f"repo root does not exist or is not a directory: {repo_root}")

    try:
        raw_cfg = parse_simple_yaml(config_file)
    except Exception as exc:
        print(f"[ERROR] Could not parse config YAML: {exc}", file=sys.stderr)
        return 1

    cfg = merge_alae_defaults(raw_cfg, reporter)
    reporter.info(f"parsed config and merged ALAE data defaults: {config_file}")
    if repo_root is not None:
        reporter.info(f"resolving relative paths from repo root: {repo_root}")
    else:
        reporter.warn("relative directory existence checks are limited because --repo-root was not supplied and could not be inferred")

    dataset = get_nested(cfg, "DATASET", {})
    if not isinstance(dataset, dict):
        reporter.error("DATASET section must be a mapping")
        dataset = {}
    raw_dataset = raw_cfg.get("DATASET", {})
    if not isinstance(raw_dataset, dict):
        raw_dataset = {}

    part_count = as_int(dataset.get("PART_COUNT"), "DATASET.PART_COUNT", reporter, default=1)
    part_count_test = as_int(dataset.get("PART_COUNT_TEST"), "DATASET.PART_COUNT_TEST", reporter, default=1)
    max_lod = as_int(dataset.get("MAX_RESOLUTION_LEVEL"), "DATASET.MAX_RESOLUTION_LEVEL", reporter)

    if part_count is not None and part_count < 1:
        reporter.error("DATASET.PART_COUNT must be positive")
    if part_count_test is not None and part_count_test < 1:
        reporter.error("DATASET.PART_COUNT_TEST must be positive")
    if max_lod is not None and max_lod < 2:
        reporter.error("DATASET.MAX_RESOLUTION_LEVEL must be at least 2")
    if part_count is not None and part_count > 0:
        if part_count % args.world_size != 0:
            reporter.error(
                f"DATASET.PART_COUNT={part_count} is not divisible by --world-size={args.world_size}; "
                "the ALAE loader asserts this during distributed training"
            )
        else:
            reporter.info(f"PART_COUNT {part_count} is compatible with world size {args.world_size}")

    path_pattern = dataset.get("PATH")
    path_example = format_pattern(path_pattern, (2, 0), "DATASET.PATH", reporter)
    check_path_contains_data_prefix("DATASET.PATH", path_pattern, reporter)
    if path_example is not None:
        reporter.info(f"DATASET.PATH example: {path_example}")

    path_test_pattern = dataset.get("PATH_TEST")
    path_test_example = format_pattern(path_test_pattern, (2, 0), "DATASET.PATH_TEST", reporter)
    check_path_contains_data_prefix("DATASET.PATH_TEST", path_test_pattern, reporter)
    if path_test_example is not None:
        reporter.info(f"DATASET.PATH_TEST example: {path_test_example}")

    ffhq_source = dataset.get("FFHQ_SOURCE")
    # DATASET.FFHQ_SOURCE exists in ALAE defaults, but it is relevant only to
    # split scripts and presets that explicitly set it (FFHQ/bedroom).
    if "FFHQ_SOURCE" in raw_dataset and ffhq_source not in (None, ""):
        ffhq_example = format_pattern(ffhq_source, (2,), "DATASET.FFHQ_SOURCE", reporter)
        check_path_contains_data_prefix("DATASET.FFHQ_SOURCE", ffhq_source, reporter)
        if ffhq_example is not None:
            reporter.info(f"DATASET.FFHQ_SOURCE example: {ffhq_example}")

    if args.check_tfrecords and isinstance(path_pattern, str) and part_count and max_lod:
        try:
            # Reuse the formatting check before enumerating every shard.
            path_pattern % (2, 0)
            check_tfrecord_files(
                pattern=path_pattern,
                name="DATASET.PATH",
                part_count=part_count,
                max_lod=max_lod,
                repo_root=repo_root,
                reporter=reporter,
            )
        except Exception:
            pass
    if args.check_tfrecords and isinstance(path_test_pattern, str) and path_test_pattern and part_count_test and max_lod:
        try:
            path_test_pattern % (2, 0)
            check_tfrecord_files(
                pattern=path_test_pattern,
                name="DATASET.PATH_TEST",
                part_count=part_count_test,
                max_lod=max_lod,
                repo_root=repo_root,
                reporter=reporter,
            )
        except Exception:
            pass

    samples_value = dataset.get("SAMPLES_PATH")
    if samples_value == "no_path":
        reporter.info("DATASET.SAMPLES_PATH is 'no_path'; sample previews are intentionally disabled")
    elif samples_value in (None, ""):
        reporter.warn("DATASET.SAMPLES_PATH is absent or empty")
    else:
        sample_path = resolve_path(samples_value, repo_root)
        if sample_path is None:
            reporter.warn(f"DATASET.SAMPLES_PATH={samples_value!r} is relative; pass --repo-root to check it")
        elif sample_path.is_dir():
            image_count = count_images(sample_path)
            if image_count:
                reporter.info(f"sample image directory exists with {image_count} image(s): {sample_path}")
            else:
                reporter.missing(f"sample image directory exists but contains no supported image files: {sample_path}")
        else:
            reporter.missing(f"sample image directory is missing: {sample_path}")

    style_value = dataset.get("STYLE_MIX_PATH")
    if style_value in (None, ""):
        reporter.warn("DATASET.STYLE_MIX_PATH is absent or empty")
    else:
        style_path = resolve_path(style_value, repo_root)
        if style_path is None:
            reporter.warn(f"DATASET.STYLE_MIX_PATH={style_value!r} is relative; pass --repo-root to check it")
        elif not style_path.is_dir():
            reporter.missing(f"style-mixing directory is missing: {style_path}")
        else:
            src_dir = style_path / "src"
            dst_dir = style_path / "dst"
            if not src_dir.is_dir():
                reporter.missing(f"style-mixing src directory is missing: {src_dir}")
            else:
                src_count = count_images(src_dir)
                if src_count:
                    reporter.info(f"style-mixing src directory has {src_count} image(s): {src_dir}")
                else:
                    reporter.missing(f"style-mixing src directory has no supported image files: {src_dir}")
                missing_src = [idx for idx in range(5) if not has_numbered_image(src_dir, idx)]
                if missing_src:
                    reporter.missing(f"style-mixing src is missing expected numbered image(s) 0..4: {missing_src}")
            if not dst_dir.is_dir():
                reporter.missing(f"style-mixing dst directory is missing: {dst_dir}")
            else:
                dst_count = count_images(dst_dir)
                if dst_count:
                    reporter.info(f"style-mixing dst directory has {dst_count} image(s): {dst_dir}")
                else:
                    reporter.missing(f"style-mixing dst directory has no supported image files: {dst_dir}")
                missing_dst = [idx for idx in range(6) if not has_numbered_image(dst_dir, idx)]
                if missing_dst:
                    reporter.missing(f"style-mixing dst is missing expected numbered image(s) 0..5: {missing_dst}")

    output_value = cfg.get("OUTPUT_DIR", "results")
    output_path = resolve_path(output_value, repo_root)
    if output_path is None:
        reporter.warn(f"OUTPUT_DIR={output_value!r} is relative; pass --repo-root to check it")
    elif output_path.exists():
        if output_path.is_dir():
            reporter.info(f"OUTPUT_DIR exists: {output_path}")
        else:
            reporter.error(f"OUTPUT_DIR exists but is not a directory: {output_path}")
    else:
        reporter.missing(f"OUTPUT_DIR is missing: {output_path}")

    reporter.print()
    return reporter.exit_code()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
