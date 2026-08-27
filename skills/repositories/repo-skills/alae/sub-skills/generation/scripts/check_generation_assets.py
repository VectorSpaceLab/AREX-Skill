#!/usr/bin/env python3
"""Safe asset checker for ALAE checkpoint-backed generation workflows.

This script reads config text and verifies file layouts only. It does not import
ALAE modules, load model weights, allocate CUDA tensors, start a GUI, train, or
download anything.
"""

from __future__ import print_function

import argparse
import json
import sys
from pathlib import Path

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")
EXPECTED_DIRECTION_INDICES = [0, 1, 2, 3, 4, 10, 11, 17, 19]
EXPECTED_DIRECTION_LABELS = {
    0: "gender",
    1: "smile",
    2: "attractive",
    3: "wavy-hair",
    4: "young",
    10: "big-lips",
    11: "big-nose",
    17: "chubby",
    19: "glasses",
}


def strip_inline_comment(value):
    """Remove simple unquoted YAML comments."""
    quote = None
    escaped = False
    output = []
    for char in value:
        if escaped:
            output.append(char)
            escaped = False
            continue
        if char == "\\":
            output.append(char)
            escaped = True
            continue
        if char in ("'", '"'):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            output.append(char)
            continue
        if char == "#" and quote is None:
            break
        output.append(char)
    return "".join(output).strip()


def parse_scalar(raw):
    raw = strip_inline_comment(raw).strip()
    if not raw:
        return ""
    if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
        return raw[1:-1]
    return raw


def load_simple_yaml(path):
    """Parse the simple nested key/value shape used by ALAE configs.

    The generated skill should not depend on PyYAML just to inspect asset paths.
    This intentionally small parser handles the repository's config files well
    enough for NAME, OUTPUT_DIR, DATASET.SAMPLES_PATH, and DATASET.STYLE_MIX_PATH.
    """
    data = {}
    stack = []
    indents = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, raw_value = line.strip().split(":", 1)
        key = key.strip()
        while indents and indent <= indents[-1]:
            indents.pop()
            stack.pop()
        dotted = ".".join(stack + [key])
        value = parse_scalar(raw_value)
        if value == "":
            data[dotted] = {}
            stack.append(key)
            indents.append(indent)
        else:
            data[dotted] = value
    return data


def add_result(results, level, check, message, path=None, detail=None):
    item = {
        "level": level,
        "check": check,
        "message": message,
    }
    if path is not None:
        item["path"] = str(path)
    if detail is not None:
        item["detail"] = detail
    results.append(item)


def resolve_under_repo(repo_root, value):
    if value is None or value == "":
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def resolve_config_path(repo_root, config_arg):
    raw = Path(config_arg)
    candidates = []
    if raw.is_absolute():
        candidates.append(raw)
    elif raw.suffix in (".yaml", ".yml") or len(raw.parts) > 1:
        candidates.append(repo_root / raw)
        candidates.append(raw)
    else:
        candidates.append(repo_root / "configs" / (config_arg + ".yaml"))
        candidates.append(repo_root / "configs" / config_arg)
        candidates.append(repo_root / config_arg)
    seen = set()
    unique = []
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            unique.append(candidate)
            seen.add(key)
    for candidate in unique:
        if candidate.is_file():
            return candidate, unique
    return unique[0], unique


def count_image_files(path):
    if not path.is_dir():
        return 0
    return sum(1 for child in path.iterdir() if child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS)


def numbered_image_exists(directory, index):
    for extension in IMAGE_EXTENSIONS:
        if (directory / (str(index) + extension)).is_file():
            return True
    return False


def first_existing(candidates):
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def check_checkpoint(repo_root, cfg, results, allow_missing_target):
    output_value = cfg.get("OUTPUT_DIR")
    if not output_value:
        add_result(results, "ERROR", "checkpoint", "Config does not define OUTPUT_DIR")
        return
    output_dir = resolve_under_repo(repo_root, output_value)
    last_checkpoint = output_dir / "last_checkpoint"
    if not output_dir.exists():
        add_result(results, "ERROR", "checkpoint", "OUTPUT_DIR does not exist", output_dir)
        return
    add_result(results, "OK", "checkpoint", "OUTPUT_DIR exists", output_dir)
    if not last_checkpoint.is_file():
        add_result(results, "ERROR", "checkpoint", "last_checkpoint file is missing", last_checkpoint)
        return
    text = last_checkpoint.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        add_result(results, "ERROR", "checkpoint", "last_checkpoint is empty", last_checkpoint)
        return
    target_text = text.splitlines()[0].strip()
    target = Path(target_text)
    if target.is_absolute():
        candidates = [target]
    else:
        candidates = [repo_root / target, output_dir / target]
    existing = first_existing(candidates)
    add_result(results, "OK", "checkpoint", "last_checkpoint points to a model path", last_checkpoint, target_text)
    if existing is None:
        level = "WARN" if allow_missing_target else "ERROR"
        add_result(results, level, "checkpoint", "checkpoint target referenced by last_checkpoint is missing", candidates[0], target_text)
    else:
        add_result(results, "OK", "checkpoint", "checkpoint target exists", existing)


def check_samples(repo_root, cfg, results, min_samples):
    sample_value = cfg.get("DATASET.SAMPLES_PATH")
    if not sample_value:
        add_result(results, "ERROR", "samples", "Config does not define DATASET.SAMPLES_PATH")
        return
    sample_dir = resolve_under_repo(repo_root, sample_value)
    if not sample_dir.is_dir():
        add_result(results, "ERROR", "samples", "DATASET.SAMPLES_PATH is not an existing directory", sample_dir)
        return
    count = count_image_files(sample_dir)
    if count < min_samples:
        add_result(results, "ERROR", "samples", "Sample directory has too few images", sample_dir, {"found": count, "minimum": min_samples})
    else:
        add_result(results, "OK", "samples", "Sample image directory exists", sample_dir, {"images": count})


def check_style_mix(repo_root, cfg, results, expect_src, expect_dst):
    style_value = cfg.get("DATASET.STYLE_MIX_PATH")
    if not style_value:
        add_result(results, "ERROR", "style-mix", "Config does not define DATASET.STYLE_MIX_PATH")
        return
    style_dir = resolve_under_repo(repo_root, style_value)
    if not style_dir.is_dir():
        add_result(results, "ERROR", "style-mix", "DATASET.STYLE_MIX_PATH is not an existing directory", style_dir)
        return
    add_result(results, "OK", "style-mix", "Style-mix root exists", style_dir)
    for child_name, expected_count in (("src", expect_src), ("dst", expect_dst)):
        child_dir = style_dir / child_name
        if not child_dir.is_dir():
            add_result(results, "ERROR", "style-mix", "Style-mix subdirectory is missing", child_dir)
            continue
        image_count = count_image_files(child_dir)
        missing = [index for index in range(expected_count) if not numbered_image_exists(child_dir, index)]
        if missing:
            add_result(results, "ERROR", "style-mix", "Missing numbered style-mix images", child_dir, {"expected_count": expected_count, "found_images": image_count, "missing_indices": missing})
        else:
            add_result(results, "OK", "style-mix", "Numbered style-mix images are present", child_dir, {"expected_count": expected_count, "found_images": image_count})


def check_directions(repo_root, directions_dir_arg, results):
    directions_dir = resolve_under_repo(repo_root, directions_dir_arg)
    if not directions_dir.is_dir():
        add_result(results, "ERROR", "directions", "Principal-directions directory is missing", directions_dir)
        return
    missing = []
    for index in EXPECTED_DIRECTION_INDICES:
        path = directions_dir / ("direction_%d.npy" % index)
        if not path.is_file():
            missing.append(index)
    if missing:
        add_result(results, "ERROR", "directions", "Missing expected direction_*.npy files", directions_dir, {"missing_indices": missing})
    else:
        add_result(results, "OK", "directions", "All expected direction_*.npy files are present", directions_dir, {"indices": EXPECTED_DIRECTION_INDICES, "labels": EXPECTED_DIRECTION_LABELS})


def print_results(results, as_json):
    if as_json:
        print(json.dumps(results, indent=2, sort_keys=True))
        return
    width = max([len(item["level"]) for item in results] + [5])
    for item in results:
        path_suffix = ""
        if "path" in item:
            path_suffix = " | " + item["path"]
        detail_suffix = ""
        if "detail" in item:
            detail_suffix = " | " + json.dumps(item["detail"], sort_keys=True)
        print("{level:<{width}} {check}: {message}{path_suffix}{detail_suffix}".format(width=width, path_suffix=path_suffix, detail_suffix=detail_suffix, **item))


def build_parser():
    parser = argparse.ArgumentParser(
        description="Safely check ALAE generation config, checkpoint pointer, samples, style-mix images, and direction files without model/GPU use."
    )
    parser.add_argument("--repo-root", default=".", help="ALAE checkout root to inspect (default: current directory).")
    parser.add_argument("--config", default="ffhq", help="Config name such as ffhq, celeba, celeba-hq256, bedroom, or a path to a YAML file.")
    parser.add_argument("--skip-checkpoint", action="store_true", help="Do not check OUTPUT_DIR/last_checkpoint or the pointed .pth file.")
    parser.add_argument("--skip-samples", action="store_true", help="Do not check DATASET.SAMPLES_PATH.")
    parser.add_argument("--skip-style-mix", action="store_true", help="Do not check DATASET.STYLE_MIX_PATH/src and dst images.")
    parser.add_argument("--skip-directions", action="store_true", help="Do not check principal_directions/direction_*.npy files.")
    parser.add_argument("--directions-dir", default="principal_directions", help="Direction-file directory, relative to repo root unless absolute.")
    parser.add_argument("--expect-style-src", type=int, default=5, help="Expected numbered source images for stylemix.py (default: 5).")
    parser.add_argument("--expect-style-dst", type=int, default=6, help="Expected numbered destination images for stylemix.py (default: 6).")
    parser.add_argument("--min-samples", type=int, default=1, help="Minimum sample images required when checking DATASET.SAMPLES_PATH (default: 1).")
    parser.add_argument("--allow-missing-checkpoint-target", action="store_true", help="Warn instead of error when last_checkpoint points to a missing .pth file.")
    parser.add_argument("--soft", action="store_true", help="Always exit 0 after reporting findings.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    results = []

    if not repo_root.is_dir():
        add_result(results, "ERROR", "repo-root", "Repository root is not an existing directory", repo_root)
        print_results(results, args.json)
        return 0 if args.soft else 1

    config_path, candidates = resolve_config_path(repo_root, args.config)
    if not config_path.is_file():
        add_result(results, "ERROR", "config", "Config file was not found", config_path, {"searched": [str(path) for path in candidates]})
        print_results(results, args.json)
        return 0 if args.soft else 1

    try:
        cfg = load_simple_yaml(config_path)
    except Exception as exc:  # pragma: no cover - defensive for malformed local YAML
        add_result(results, "ERROR", "config", "Could not parse config text", config_path, str(exc))
        print_results(results, args.json)
        return 0 if args.soft else 1

    add_result(results, "OK", "config", "Config file exists and was parsed", config_path, {
        "NAME": cfg.get("NAME"),
        "OUTPUT_DIR": cfg.get("OUTPUT_DIR"),
        "DATASET.SAMPLES_PATH": cfg.get("DATASET.SAMPLES_PATH"),
        "DATASET.STYLE_MIX_PATH": cfg.get("DATASET.STYLE_MIX_PATH"),
    })

    if not args.skip_checkpoint:
        check_checkpoint(repo_root, cfg, results, args.allow_missing_checkpoint_target)
    if not args.skip_samples:
        check_samples(repo_root, cfg, results, args.min_samples)
    if not args.skip_style_mix:
        check_style_mix(repo_root, cfg, results, args.expect_style_src, args.expect_style_dst)
    if not args.skip_directions:
        check_directions(repo_root, args.directions_dir, results)

    print_results(results, args.json)
    if args.soft:
        return 0
    has_error = any(item["level"] == "ERROR" for item in results)
    has_warning = any(item["level"] == "WARN" for item in results)
    if has_error or (args.strict and has_warning):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
