#!/usr/bin/env python3
"""Read-only validation for an rPPG-Toolbox YACS-style YAML config.

This helper intentionally does not import the repository, mutate YAML, create
cache directories, or download data. It checks the mode-specific shape and the
path/type constraints that can be diagnosed before invoking ``main.py``.
PyYAML is the only non-standard dependency, matching the repository requirements.
"""

import argparse
import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - makes the failure actionable
    yaml = None


SUPPORTED_MODES = ("train_and_test", "only_test", "unsupervised_method")
SUPPORTED_UNSUPERVISED = ("POS", "CHROM", "ICA", "GREEN", "LGI", "PBV", "OMIT")


class Report:
    """Collect deterministic errors and warnings without changing the input."""

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append("ERROR: " + message)

    def warning(self, message: str) -> None:
        self.warnings.append("WARNING: " + message)


def mapping(value: Any, label: str, report: Report) -> Optional[Dict[str, Any]]:
    """Return a YAML mapping or record a useful shape error."""
    if not isinstance(value, dict):
        report.error("{} must be a YAML mapping".format(label))
        return None
    return value


def nonempty_string(value: Any, label: str, report: Report) -> bool:
    """Require a non-empty string for path/name-like values."""
    if not isinstance(value, str) or not value.strip():
        report.error("{} must be a non-empty string".format(label))
        return False
    return True


def validate_file_list(value: Any, label: str, report: Report) -> None:
    """Check the source updater's directory-or-lowercase-csv contract."""
    if not nonempty_string(value, label, report):
        return
    extension = os.path.splitext(value)[1]
    if extension and extension != ".csv":
        report.error("{} must be a directory path or a .csv file".format(label))


def validate_bounds(data: Dict[str, Any], label: str, report: Report) -> None:
    """Check the bounds asserted by BaseLoader when values are supplied."""
    begin = data.get("BEGIN", 0.0)
    end = data.get("END", 1.0)
    if isinstance(begin, bool) or not isinstance(begin, (int, float)):
        report.error("{}.BEGIN must be numeric".format(label))
    if isinstance(end, bool) or not isinstance(end, (int, float)):
        report.error("{}.END must be numeric".format(label))
    if isinstance(begin, (int, float)) and not isinstance(begin, bool):
        if begin < 0:
            report.error("{}.BEGIN must be >= 0".format(label))
    if isinstance(end, (int, float)) and not isinstance(end, bool):
        if end > 1:
            report.error("{}.END must be <= 1".format(label))
    if isinstance(begin, (int, float)) and isinstance(end, (int, float)):
        if not isinstance(begin, bool) and not isinstance(end, bool) and begin >= end:
            report.error("{}.BEGIN must be less than {}.END".format(label, label))


def validate_data_block(
    root: Dict[str, Any],
    block_name: str,
    report: Report,
    check_paths: bool,
    require_path: bool = True,
) -> Optional[Dict[str, Any]]:
    """Validate one TRAIN/VALID/TEST/UNSUPERVISED DATA block."""
    block = mapping(root.get(block_name), block_name, report)
    if block is None:
        return None
    data = mapping(block.get("DATA"), block_name + ".DATA", report)
    if data is None:
        return None

    dataset = data.get("DATASET")
    if not nonempty_string(dataset, block_name + ".DATA.DATASET", report):
        pass

    data_path = data.get("DATA_PATH")
    if require_path:
        if not nonempty_string(data_path, block_name + ".DATA.DATA_PATH", report):
            pass
    elif data_path is not None and data_path != "":
        nonempty_string(data_path, block_name + ".DATA.DATA_PATH", report)

    for key in ("DO_PREPROCESS",):
        if key in data and not isinstance(data[key], bool):
            report.error("{}.DATA.{} must be boolean".format(block_name, key))

    if "FILE_LIST_PATH" in data:
        validate_file_list(data["FILE_LIST_PATH"], block_name + ".DATA.FILE_LIST_PATH", report)
    else:
        report.warning(
            "{}.DATA.FILE_LIST_PATH is omitted; config.py will derive it under CACHED_PATH/DataFileLists".format(
                block_name
            )
        )

    if "CACHED_PATH" in data and not nonempty_string(
        data["CACHED_PATH"], block_name + ".DATA.CACHED_PATH", report
    ):
        pass

    validate_bounds(data, block_name + ".DATA", report)
    if check_paths:
        check_local_path(data_path, block_name + ".DATA.DATA_PATH", report)
        check_local_path(data.get("CACHED_PATH"), block_name + ".DATA.CACHED_PATH", report)
        check_local_path(data.get("FILE_LIST_PATH"), block_name + ".DATA.FILE_LIST_PATH", report)
    return data


def check_local_path(value: Any, label: str, report: Report) -> None:
    """Report absent local paths, while ignoring empty optional values."""
    if not isinstance(value, str) or not value.strip():
        return
    # Paths are intentionally treated as local. This helper never probes URLs.
    if not os.path.exists(os.path.expanduser(value)):
        report.warning("{} does not exist: {}".format(label, value))


def validate_device(root: Dict[str, Any], report: Report) -> None:
    """Validate the root device setting and explain the schema default."""
    if "DEVICE" not in root:
        report.warning("DEVICE is omitted; config.py defaults it to cuda:0")
    elif not nonempty_string(root["DEVICE"], "DEVICE", report):
        pass


def validate_mode(root: Dict[str, Any], report: Report, check_paths: bool) -> None:
    """Validate the three main mode shapes and their required settings."""
    mode = root.get("TOOLBOX_MODE")
    if mode not in SUPPORTED_MODES:
        report.error(
            "TOOLBOX_MODE must be one of {}".format(", ".join(SUPPORTED_MODES))
        )
        return

    if mode == "train_and_test":
        validate_data_block(root, "TRAIN", report, check_paths)
        validate_data_block(root, "TEST", report, check_paths)
        valid = validate_data_block(root, "VALID", report, check_paths)
        test = mapping(root.get("TEST"), "TEST", report)
        use_last = True if test is None else test.get("USE_LAST_EPOCH", True)
        if not isinstance(use_last, bool):
            report.error("TEST.USE_LAST_EPOCH must be boolean")
        elif not use_last and valid is None:
            report.error("VALID.DATA is required when TEST.USE_LAST_EPOCH is false")
        if test is not None and "USE_LAST_EPOCH" not in test:
            report.warning("TEST.USE_LAST_EPOCH is omitted; config.py defaults it to true")
    elif mode == "only_test":
        validate_data_block(root, "TEST", report, check_paths)
        inference = mapping(root.get("INFERENCE"), "INFERENCE", report)
        if inference is None:
            return
        model_path = inference.get("MODEL_PATH")
        if not nonempty_string(model_path, "INFERENCE.MODEL_PATH", report):
            pass
        elif check_paths:
            check_local_path(model_path, "INFERENCE.MODEL_PATH", report)
    else:
        data = validate_data_block(root, "UNSUPERVISED", report, check_paths)
        unsupervised = mapping(root.get("UNSUPERVISED"), "UNSUPERVISED", report)
        if unsupervised is None:
            return
        methods = unsupervised.get("METHOD")
        if not isinstance(methods, list) or not methods:
            report.error("UNSUPERVISED.METHOD must be a non-empty YAML list")
        elif any(method not in SUPPORTED_UNSUPERVISED for method in methods):
            bad = [str(method) for method in methods if method not in SUPPORTED_UNSUPERVISED]
            report.error(
                "unsupported UNSUPERVISED.METHOD token(s): {}".format(", ".join(bad))
            )
        if data is not None:
            preprocess = data.get("PREPROCESS", {})
            if isinstance(preprocess, dict) and preprocess.get("USE_PSUEDO_PPG_LABEL") is True:
                report.error(
                    "UNSUPERVISED.DATA.PREPROCESS.USE_PSUEDO_PPG_LABEL must be false"
                )


def load_yaml(path: str, report: Report) -> Optional[Dict[str, Any]]:
    """Load one YAML document safely and return its mapping."""
    if yaml is None:
        report.error("PyYAML is not installed; install the repository requirement PyYAML==6.0")
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except OSError as exc:
        report.error("cannot read config {}: {}".format(path, exc))
        return None
    except yaml.YAMLError as exc:
        report.error("invalid YAML in {}: {}".format(path, exc))
        return None
    if not isinstance(value, dict):
        report.error("config root must be a YAML mapping")
        return None
    return value


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Read-only validation for an rPPG-Toolbox YAML config."
    )
    parser.add_argument("config", help="path to a YAML configuration file")
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="warn for explicitly configured raw/cache/file-list/checkpoint paths that do not exist",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print only errors and the final status",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Validate one config and return zero only when no errors were found."""
    args = parse_args(argv)
    report = Report()
    root = load_yaml(args.config, report)
    if root is not None:
        validate_device(root, report)
        validate_mode(root, report, args.check_paths)

    if not args.quiet:
        for warning in report.warnings:
            print(warning)
    for error in report.errors:
        print(error)
    if report.errors:
        print("INVALID: {} error(s), {} warning(s)".format(len(report.errors), len(report.warnings)))
        return 1
    print("VALID: {} warning(s)".format(len(report.warnings)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
