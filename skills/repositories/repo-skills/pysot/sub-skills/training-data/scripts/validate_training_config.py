#!/usr/bin/env python3
"""Safe PySOT training-config preflight.

This helper validates the config/data assumptions that PySOT's training loader
checks only after entering the CUDA/distributed training path. It does not run
training, instantiate the dataset, or scan large annotation JSON files.
"""

from __future__ import print_function

import argparse
import json
import sys
from pathlib import Path

_MISSING = object()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate PySOT training config structure and optional data paths without running training."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Experiment YAML passed to tools/train.py --cfg. Relative paths are resolved from cwd, then --repo-root.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="PySOT checkout root used for importing pysot and resolving DATASET ROOT/ANNO paths.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Also require configured dataset roots/annotation files and BACKBONE.PRETRAINED to exist.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable check lines.",
    )
    return parser.parse_args(argv)


def as_path(value):
    return Path(value).expanduser()


def looks_like_pysot_root(path):
    return (path / "pysot" / "core" / "config.py").is_file() and (
        path / "tools" / "train.py"
    ).is_file()


def resolve_existing_path(value, repo_root=None):
    path = as_path(value)
    if path.is_absolute():
        return path
    cwd_candidate = (Path.cwd() / path)
    if cwd_candidate.exists():
        return cwd_candidate.resolve()
    if repo_root is not None:
        repo_candidate = repo_root / path
        if repo_candidate.exists():
            return repo_candidate.resolve()
    return path


def infer_repo_root(config_path=None):
    candidates = []
    cwd = Path.cwd().resolve()
    candidates.append(cwd)
    candidates.extend(cwd.parents)
    if config_path is not None and config_path.exists():
        cfg_parent = config_path.resolve().parent
        candidates.append(cfg_parent)
        candidates.extend(cfg_parent.parents)
    seen = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if looks_like_pysot_root(candidate):
            return candidate
    return None


def load_cfg(config_path, repo_root, failures):
    if repo_root is not None:
        sys.path.insert(0, str(repo_root))
    try:
        from pysot.core.config import cfg as base_cfg  # pylint: disable=import-error
    except Exception as exc:  # pragma: no cover - depends on caller env
        failures.append(
            "Could not import pysot.core.config. Run from a PySOT checkout, set PYTHONPATH to the checkout root, "
            "install in editable/development style, or pass --repo-root. Import error: {}".format(exc)
        )
        return None
    try:
        cfg = base_cfg.clone()
        cfg.merge_from_file(str(config_path))
        return cfg
    except Exception as exc:
        failures.append("Could not merge config '{}': {}".format(config_path, exc))
        return None


def get_attr(node, name):
    try:
        return getattr(node, name)
    except Exception:
        return _MISSING


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def path_for_training(value, repo_root):
    path = as_path(str(value))
    if path.is_absolute():
        return path
    if repo_root is None:
        return None
    return repo_root / path


def check_required_field(sub_cfg, dataset_name, field, failures):
    value = get_attr(sub_cfg, field)
    if value is _MISSING:
        failures.append("DATASET.{} is missing required field {}".format(dataset_name, field))
        return _MISSING
    return value


def check_output_size(cfg, ok, failures):
    train = get_attr(cfg, "TRAIN")
    anchor = get_attr(cfg, "ANCHOR")
    if train is _MISSING or anchor is _MISSING:
        failures.append("Config must contain TRAIN and ANCHOR sections")
        return
    required = [
        ("TRAIN.SEARCH_SIZE", get_attr(train, "SEARCH_SIZE")),
        ("TRAIN.EXEMPLAR_SIZE", get_attr(train, "EXEMPLAR_SIZE")),
        ("TRAIN.BASE_SIZE", get_attr(train, "BASE_SIZE")),
        ("TRAIN.OUTPUT_SIZE", get_attr(train, "OUTPUT_SIZE")),
        ("ANCHOR.STRIDE", get_attr(anchor, "STRIDE")),
    ]
    missing = [name for name, value in required if value is _MISSING]
    if missing:
        failures.append("Missing size fields: {}".format(", ".join(missing)))
        return
    bad_types = [name for name, value in required if not is_number(value)]
    if bad_types:
        failures.append("Size fields must be numeric: {}".format(", ".join(bad_types)))
        return
    search = float(get_attr(train, "SEARCH_SIZE"))
    exemplar = float(get_attr(train, "EXEMPLAR_SIZE"))
    base = float(get_attr(train, "BASE_SIZE"))
    stride = float(get_attr(anchor, "STRIDE"))
    output = float(get_attr(train, "OUTPUT_SIZE"))
    if stride == 0:
        failures.append("ANCHOR.STRIDE must be non-zero")
        return
    desired = (search - exemplar) / stride + 1.0 + base
    if abs(desired - output) > 1e-9:
        failures.append(
            "TRAIN.OUTPUT_SIZE mismatch: expected {} from (SEARCH_SIZE {} - EXEMPLAR_SIZE {}) / STRIDE {} + 1 + BASE_SIZE {}, got {}".format(
                desired, search, exemplar, stride, base, output
            )
        )
    else:
        ok.append("TRAIN output-size formula matches: OUTPUT_SIZE={}".format(get_attr(train, "OUTPUT_SIZE")))


def length_or_none(value):
    try:
        return len(value)
    except Exception:
        return None


def check_anchor_count(cfg, ok, warnings, failures):
    anchor = get_attr(cfg, "ANCHOR")
    if anchor is _MISSING:
        failures.append("Config must contain ANCHOR section")
        return
    ratios = get_attr(anchor, "RATIOS")
    scales = get_attr(anchor, "SCALES")
    anchor_num = get_attr(anchor, "ANCHOR_NUM")
    if ratios is _MISSING or scales is _MISSING or anchor_num is _MISSING:
        failures.append("ANCHOR must define RATIOS, SCALES, and ANCHOR_NUM")
        return
    ratio_len = length_or_none(ratios)
    scale_len = length_or_none(scales)
    if ratio_len is None or scale_len is None:
        failures.append("ANCHOR.RATIOS and ANCHOR.SCALES must be sequences")
        return
    expected = ratio_len * scale_len
    if anchor_num != expected:
        failures.append(
            "ANCHOR.ANCHOR_NUM mismatch: expected len(RATIOS) * len(SCALES) = {}, got {}".format(
                expected, anchor_num
            )
        )
    else:
        ok.append("Anchor count matches: {} anchors per location".format(expected))

    rpn = get_attr(cfg, "RPN")
    if rpn is not _MISSING:
        kwargs = get_attr(rpn, "KWARGS")
        if kwargs is not _MISSING:
            rpn_anchor_num = get_attr(kwargs, "anchor_num")
            if rpn_anchor_num is not _MISSING:
                if rpn_anchor_num != expected:
                    failures.append(
                        "RPN.KWARGS.anchor_num mismatch: expected {}, got {}".format(
                            expected, rpn_anchor_num
                        )
                    )
                else:
                    ok.append("RPN.KWARGS.anchor_num matches anchor count")
            else:
                warnings.append("RPN.KWARGS.anchor_num is not set; this is acceptable if the model head does not require it")


def check_dataset_paths(name, root_value, anno_value, repo_root, failures):
    if repo_root is None:
        failures.append(
            "Cannot resolve DATASET.{} ROOT/ANNO paths without a PySOT repo root; pass --repo-root".format(name)
        )
        return
    root_path = path_for_training(root_value, repo_root)
    anno_path = path_for_training(anno_value, repo_root)
    if root_path is None or not root_path.is_dir():
        failures.append("DATASET.{}.ROOT does not exist or is not a directory: {}".format(name, root_value))
    if anno_path is None or not anno_path.is_file():
        failures.append("DATASET.{}.ANNO does not exist or is not a file: {}".format(name, anno_value))


def check_datasets(cfg, repo_root, check_files, ok, warnings, failures):
    dataset = get_attr(cfg, "DATASET")
    if dataset is _MISSING:
        failures.append("Config must contain DATASET section")
        return
    names = get_attr(dataset, "NAMES")
    if names is _MISSING:
        failures.append("DATASET.NAMES is missing")
        return
    if isinstance(names, str) or not hasattr(names, "__iter__"):
        failures.append("DATASET.NAMES must be a list/tuple of dataset names, got {!r}".format(names))
        return
    names = list(names)
    if not names:
        failures.append("DATASET.NAMES must not be empty")
        return

    for name in names:
        if not isinstance(name, str):
            failures.append("DATASET.NAMES entries must be strings, got {!r}".format(name))
            continue
        sub_cfg = get_attr(dataset, name)
        if sub_cfg is _MISSING:
            failures.append("DATASET.NAMES includes {} but DATASET.{} is not defined".format(name, name))
            continue
        root = check_required_field(sub_cfg, name, "ROOT", failures)
        anno = check_required_field(sub_cfg, name, "ANNO", failures)
        frame_range = check_required_field(sub_cfg, name, "FRAME_RANGE", failures)
        num_use = check_required_field(sub_cfg, name, "NUM_USE", failures)

        if root is not _MISSING and (not isinstance(root, str) or not root):
            failures.append("DATASET.{}.ROOT must be a non-empty string".format(name))
        if anno is not _MISSING and (not isinstance(anno, str) or not anno):
            failures.append("DATASET.{}.ANNO must be a non-empty string".format(name))
        if frame_range is not _MISSING:
            if not is_int(frame_range) or frame_range < 0:
                failures.append("DATASET.{}.FRAME_RANGE must be a non-negative integer".format(name))
        if num_use is not _MISSING:
            if not is_int(num_use) or num_use < -1 or num_use == 0:
                failures.append("DATASET.{}.NUM_USE must be -1 or a positive integer".format(name))
            elif num_use == -1:
                warnings.append("DATASET.{}.NUM_USE=-1 uses all valid entries after zero-box filtering".format(name))

        if check_files and root is not _MISSING and anno is not _MISSING:
            check_dataset_paths(name, root, anno, repo_root, failures)

    ok.append("DATASET.NAMES checked: {}".format(", ".join(names)))


def check_pretrained_files(cfg, repo_root, check_files, ok, warnings, failures):
    if not check_files:
        return
    if repo_root is None:
        warnings.append("Skipping pretrained path existence checks because repo root could not be inferred")
        return
    backbone = get_attr(cfg, "BACKBONE")
    if backbone is _MISSING:
        warnings.append("BACKBONE section missing; skipping BACKBONE.PRETRAINED check")
        return
    pretrained = get_attr(backbone, "PRETRAINED")
    if pretrained is _MISSING or not pretrained:
        warnings.append("BACKBONE.PRETRAINED is empty; full training may need a user-supplied pretrained backbone")
        return
    pretrained_path = path_for_training(pretrained, repo_root)
    if pretrained_path is None or not pretrained_path.is_file():
        failures.append("BACKBONE.PRETRAINED is set but file was not found: {}".format(pretrained))
    else:
        ok.append("BACKBONE.PRETRAINED exists")


def build_report(args):
    ok = []
    warnings = []
    failures = []

    repo_root = as_path(args.repo_root).resolve() if args.repo_root else None
    config_path = resolve_existing_path(args.config, repo_root)
    if not config_path.exists():
        failures.append("Config file does not exist: {}".format(args.config))
        return ok, warnings, failures
    config_path = config_path.resolve()

    if repo_root is None:
        repo_root = infer_repo_root(config_path)
    elif not repo_root.exists():
        failures.append("--repo-root does not exist: {}".format(args.repo_root))
        return ok, warnings, failures
    elif not looks_like_pysot_root(repo_root):
        warnings.append("--repo-root does not look like a PySOT checkout root; imports or file checks may fail")

    cfg = load_cfg(config_path, repo_root, failures)
    if cfg is None:
        return ok, warnings, failures

    ok.append("Config merged: {}".format(config_path.name))
    if repo_root is not None:
        ok.append("Repo root available for relative training paths")
    else:
        warnings.append("Repo root not inferred; pass --repo-root for path checks")

    check_output_size(cfg, ok, failures)
    check_anchor_count(cfg, ok, warnings, failures)
    check_datasets(cfg, repo_root, args.check_files, ok, warnings, failures)
    check_pretrained_files(cfg, repo_root, args.check_files, ok, warnings, failures)
    return ok, warnings, failures


def emit_human(ok, warnings, failures):
    for message in ok:
        print("[OK] {}".format(message))
    for message in warnings:
        print("[WARN] {}".format(message))
    for message in failures:
        print("[FAIL] {}".format(message))
    status = "failed" if failures else "passed"
    print("Summary: {} ({} ok, {} warning, {} failure)".format(status, len(ok), len(warnings), len(failures)))


def main(argv=None):
    args = parse_args(argv)
    ok, warnings, failures = build_report(args)
    if args.json:
        print(
            json.dumps(
                {
                    "status": "failed" if failures else "passed",
                    "ok": ok,
                    "warnings": warnings,
                    "failures": failures,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        emit_human(ok, warnings, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
