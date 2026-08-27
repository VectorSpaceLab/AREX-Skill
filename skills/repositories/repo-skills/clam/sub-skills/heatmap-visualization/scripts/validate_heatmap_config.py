#!/usr/bin/env python3
"""Static validator for CLAM create_heatmaps.py YAML configs.

This helper intentionally does not import CLAM, PyTorch, OpenSlide, encoders,
checkpoints, or slide files. It validates config/process-list shape and common
consistency issues before a heavy heatmap run.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment message only
    yaml = None


REQUIRED_KEYS: dict[str, tuple[str, ...]] = {
    "exp_arguments": (
        "n_classes",
        "save_exp_code",
        "raw_save_dir",
        "production_save_dir",
        "batch_size",
    ),
    "data_arguments": (
        "data_dir",
        "process_list",
        "preset",
        "slide_ext",
        "label_dict",
    ),
    "patching_arguments": (
        "patch_size",
        "overlap",
        "patch_level",
        "custom_downsample",
    ),
    "encoder_arguments": (
        "model_name",
        "target_img_size",
    ),
    "model_arguments": (
        "ckpt_path",
        "model_type",
        "initiate_fn",
        "model_size",
        "drop_out",
        "embed_dim",
    ),
    "heatmap_arguments": (
        "vis_level",
        "alpha",
        "blank_canvas",
        "save_orig",
        "save_ext",
        "use_ref_scores",
        "blur",
        "use_center_shift",
        "use_roi",
        "calc_heatmap",
        "binarize",
        "binary_thresh",
        "custom_downsample",
        "cmap",
    ),
    "sample_arguments": ("samples",),
}

SUPPORTED_ENCODERS = {"resnet50_trunc", "uni_v1", "conch_v1"}
EXPECTED_EMBED_DIM = {
    "resnet50_trunc": 1024,
    "uni_v1": 1024,
    "conch_v1": 512,
}
SUPPORTED_HEATMAP_MODELS = {"clam_sb", "clam_mb"}
SUPPORTED_SAMPLE_MODES = {"topk", "reverse_topk", "range_sample"}
ROI_COLUMNS = {"x1", "x2", "y1", "y2"}
PROCESS_LIST_BASE_COLUMNS = {"slide_id"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def print(self) -> None:
        for message in self.errors:
            print(f"ERROR: {message}")
        for message in self.warnings:
            print(f"WARNING: {message}")
        if not self.errors and not self.warnings:
            print("OK: no static config issues found")
        elif not self.errors:
            print(f"OK: validation completed with {len(self.warnings)} warning(s)")
        else:
            print(
                f"FAILED: validation found {len(self.errors)} error(s) "
                f"and {len(self.warnings)} warning(s)"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely validate a CLAM heatmap YAML config without loading slides or checkpoints."
    )
    parser.add_argument(
        "config",
        help=(
            "Path to a heatmap YAML config, or a filename to resolve under "
            "--config-root. Runtime create_heatmaps.py expects filenames under heatmaps/configs."
        ),
    )
    parser.add_argument(
        "--config-root",
        default="heatmaps/configs",
        help="Directory used when CONFIG is a filename. Default: heatmaps/configs",
    )
    parser.add_argument(
        "--process-list-root",
        default="heatmaps/process_lists",
        help="Directory used for data_arguments.process_list filenames. Default: heatmaps/process_lists",
    )
    parser.add_argument(
        "--strict-paths",
        action="store_true",
        help="Treat missing checkpoint, slide directory, preset, and output parent paths as errors instead of warnings.",
    )
    return parser.parse_args()


def strip_inline_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote is not None:
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            continue
        if char == "#" and quote is None:
            if index == 0 or line[index - 1].isspace():
                return line[:index].rstrip()
    return line.rstrip()


def split_key_value(content: str) -> tuple[str, str] | None:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(content):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote is not None:
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            continue
        if char == ":" and quote is None:
            return content[:index].strip(), content[index + 1 :].strip()
    return None


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if any(marker in value for marker in (".", "e", "E")):
            return float(value)
        return int(value)
    except ValueError:
        return value


def simple_yaml_load(text: str) -> dict[str, Any]:
    parsed_lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if raw_line.strip() in {"", "---"}:
            continue
        cleaned = strip_inline_comment(raw_line)
        if cleaned.strip() == "":
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        parsed_lines.append((indent, cleaned.strip()))

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(parsed_lines):
            return {}, index
        if parsed_lines[index][1].startswith("- "):
            return parse_list(index, indent)
        return parse_map(index, indent)

    def parse_map(index: int, indent: int) -> tuple[dict[str, Any], int]:
        mapping: dict[str, Any] = {}
        while index < len(parsed_lines):
            line_indent, content = parsed_lines[index]
            if line_indent < indent:
                break
            if line_indent > indent:
                break
            if content.startswith("- "):
                break
            pair = split_key_value(content)
            if pair is None:
                raise ValueError(f"expected key/value entry: {content}")
            key, value = pair
            if not key:
                raise ValueError(f"empty key in entry: {content}")
            index += 1
            if value == "":
                if index < len(parsed_lines) and parsed_lines[index][0] > line_indent:
                    child, index = parse_block(index, parsed_lines[index][0])
                    mapping[key] = child
                else:
                    mapping[key] = None
            else:
                mapping[key] = parse_scalar(value)
        return mapping, index

    def parse_list(index: int, indent: int) -> tuple[list[Any], int]:
        items: list[Any] = []
        while index < len(parsed_lines):
            line_indent, content = parsed_lines[index]
            if line_indent < indent:
                break
            if line_indent != indent or not content.startswith("- "):
                break
            item_content = content[2:].strip()
            index += 1
            pair = split_key_value(item_content) if item_content else None
            if pair is None:
                item: Any = parse_scalar(item_content)
                if index < len(parsed_lines) and parsed_lines[index][0] > line_indent:
                    child, index = parse_block(index, parsed_lines[index][0])
                    item = child if item is None else item
                items.append(item)
                continue

            key, value = pair
            item_dict: dict[str, Any] = {}
            if value == "":
                if index < len(parsed_lines) and parsed_lines[index][0] > line_indent:
                    child, index = parse_block(index, parsed_lines[index][0])
                    item_dict[key] = child
                else:
                    item_dict[key] = None
            else:
                item_dict[key] = parse_scalar(value)
            if index < len(parsed_lines) and parsed_lines[index][0] > line_indent:
                child, index = parse_block(index, parsed_lines[index][0])
                if isinstance(child, dict):
                    item_dict.update(child)
            items.append(item_dict)
        return items, index

    if not parsed_lines:
        return {}
    loaded, final_index = parse_block(0, parsed_lines[0][0])
    if final_index != len(parsed_lines):
        raise ValueError("could not parse the full YAML document")
    if not isinstance(loaded, dict):
        raise ValueError("YAML root is not a mapping")
    return loaded


def load_yaml(path: Path, reporter: Reporter) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        reporter.error(f"config file not found: {path}")
        return None

    if yaml is not None:
        try:
            loaded = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            reporter.error(f"YAML parse error in {path}: {exc}")
            return None
    else:
        try:
            loaded = simple_yaml_load(text)
        except ValueError as exc:
            reporter.error(
                f"could not parse YAML without PyYAML: {exc}; install PyYAML for full YAML support"
            )
            return None

    if not isinstance(loaded, dict):
        reporter.error("config root must be a mapping of top-level sections")
        return None
    return loaded


def resolve_config_path(config_arg: str, config_root: str, reporter: Reporter) -> Path:
    raw_path = Path(config_arg)
    if raw_path.exists():
        if raw_path.parent != Path("."):
            reporter.warn(
                "create_heatmaps.py prepends heatmaps/configs to --config_file; "
                "pass only the config filename at runtime"
            )
        return raw_path
    rooted = Path(config_root) / config_arg
    if rooted.exists():
        return rooted
    return raw_path


def section(config: dict[str, Any], name: str, reporter: Reporter) -> dict[str, Any]:
    value = config.get(name)
    if not isinstance(value, dict):
        reporter.error(f"missing or non-mapping section: {name}")
        return {}
    return value


def validate_required_keys(config: dict[str, Any], reporter: Reporter) -> None:
    for section_name, keys in REQUIRED_KEYS.items():
        values = section(config, section_name, reporter)
        if not values:
            continue
        for key in keys:
            if key not in values:
                reporter.error(f"{section_name}.{key} is required by the CLAM heatmap template")


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_exp_and_labels(config: dict[str, Any], reporter: Reporter) -> None:
    exp = section(config, "exp_arguments", reporter)
    data = section(config, "data_arguments", reporter)
    n_classes = as_int(exp.get("n_classes"))
    if n_classes is None or n_classes < 2:
        reporter.error("exp_arguments.n_classes must be an integer >= 2")
    batch_size = as_int(exp.get("batch_size"))
    if batch_size is None or batch_size < 1:
        reporter.error("exp_arguments.batch_size must be a positive integer")

    label_dict = data.get("label_dict")
    if not isinstance(label_dict, dict) or not label_dict:
        reporter.error("data_arguments.label_dict must be a non-empty mapping of label name to integer class id")
        return

    class_ids: list[int] = []
    for label, class_id in label_dict.items():
        parsed = as_int(class_id)
        if parsed is None:
            reporter.error(f"data_arguments.label_dict[{label!r}] must be an integer class id")
        else:
            class_ids.append(parsed)

    if n_classes is not None and class_ids:
        expected = set(range(n_classes))
        actual = set(class_ids)
        if actual != expected:
            reporter.warn(
                "data_arguments.label_dict values should cover exactly "
                f"0..{n_classes - 1}; found {sorted(actual)}"
            )


def validate_model_encoder(config: dict[str, Any], reporter: Reporter) -> None:
    encoder = section(config, "encoder_arguments", reporter)
    model = section(config, "model_arguments", reporter)
    model_name = encoder.get("model_name")
    if model_name not in SUPPORTED_ENCODERS:
        reporter.error(
            "encoder_arguments.model_name must be one of "
            f"{sorted(SUPPORTED_ENCODERS)} for the current CLAM heatmap workflow"
        )
    target_img_size = as_int(encoder.get("target_img_size"))
    if target_img_size is None or target_img_size < 1:
        reporter.error("encoder_arguments.target_img_size must be a positive integer")

    model_type = model.get("model_type")
    if model_type not in SUPPORTED_HEATMAP_MODELS:
        reporter.error(
            "model_arguments.model_type must be 'clam_sb' or 'clam_mb'; "
            "heatmap infer_single_slide does not implement MIL attention heatmaps"
        )

    if model.get("initiate_fn") != "initiate_model":
        reporter.error("model_arguments.initiate_fn must be initiate_model for create_heatmaps.py")

    model_size = model.get("model_size")
    if model_size not in {"small", "big"}:
        reporter.warn("model_arguments.model_size is normally 'small' or 'big' and must match training")

    drop_out = as_float(model.get("drop_out"))
    if drop_out is None or drop_out < 0 or drop_out >= 1:
        reporter.warn("model_arguments.drop_out should be a dropout probability in [0, 1)")

    embed_dim = as_int(model.get("embed_dim"))
    if embed_dim is None or embed_dim < 1:
        reporter.error("model_arguments.embed_dim must be a positive integer")
    elif model_name in EXPECTED_EMBED_DIM:
        expected = EXPECTED_EMBED_DIM[model_name]
        if embed_dim != expected:
            reporter.error(
                f"encoder {model_name} expects model_arguments.embed_dim {expected}; found {embed_dim}"
            )

    if model_name == "uni_v1":
        reporter.warn("runtime heatmap inference with uni_v1 requires UNI_CKPT_PATH to be set")
    if model_name == "conch_v1":
        reporter.warn("runtime heatmap inference with conch_v1 requires CONCH_CKPT_PATH and the CONCH package")


def validate_patching_and_heatmap(config: dict[str, Any], reporter: Reporter) -> None:
    patching = section(config, "patching_arguments", reporter)
    heatmap = section(config, "heatmap_arguments", reporter)

    patch_size = as_int(patching.get("patch_size"))
    if patch_size is None or patch_size < 1:
        reporter.error("patching_arguments.patch_size must be a positive integer")
    overlap = as_float(patching.get("overlap"))
    if overlap is None or overlap < 0 or overlap >= 1:
        reporter.error("patching_arguments.overlap must be in [0, 1)")
    patch_level = as_int(patching.get("patch_level"))
    if patch_level is None or patch_level < 0:
        reporter.warn("patching_arguments.patch_level is normally a non-negative OpenSlide level")
    custom_downsample = as_int(patching.get("custom_downsample"))
    if custom_downsample is None or custom_downsample < 1:
        reporter.error("patching_arguments.custom_downsample must be a positive integer")

    alpha = as_float(heatmap.get("alpha"))
    if alpha is None or alpha < 0 or alpha > 1:
        reporter.warn("heatmap_arguments.alpha should be in [0, 1]")
    binary_thresh = as_float(heatmap.get("binary_thresh"))
    if heatmap.get("binarize") and (binary_thresh is None or binary_thresh < 0 or binary_thresh > 1):
        reporter.error("heatmap_arguments.binary_thresh must be in [0, 1] when binarize is true")
    save_ext = str(heatmap.get("save_ext", ""))
    if save_ext.startswith("."):
        reporter.warn("heatmap_arguments.save_ext should be an extension without a leading dot")
    if save_ext and save_ext.lower() not in {"jpg", "jpeg", "png", "tif", "tiff"}:
        reporter.warn("heatmap_arguments.save_ext is unusual; verify PIL can save this extension")


def validate_samples(config: dict[str, Any], reporter: Reporter) -> None:
    sample_arguments = section(config, "sample_arguments", reporter)
    samples = sample_arguments.get("samples")
    if samples is None:
        return
    if not isinstance(samples, list):
        reporter.error("sample_arguments.samples must be a list")
        return
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            reporter.error(f"sample_arguments.samples[{index}] must be a mapping")
            continue
        if not sample.get("sample"):
            continue
        mode = sample.get("mode")
        if mode not in SUPPORTED_SAMPLE_MODES:
            reporter.error(
                f"sample_arguments.samples[{index}].mode must be one of {sorted(SUPPORTED_SAMPLE_MODES)}"
            )
        k = as_int(sample.get("k"))
        if k is None or k < 1:
            reporter.error(f"sample_arguments.samples[{index}].k must be a positive integer")
        if mode == "range_sample":
            start = as_float(sample.get("score_start", 0))
            end = as_float(sample.get("score_end", 1))
            if start is None or end is None or start < 0 or end > 1 or start > end:
                reporter.error(
                    f"sample_arguments.samples[{index}] range_sample score_start/score_end must satisfy 0 <= start <= end <= 1"
                )


def read_process_list(path: Path, reporter: Reporter) -> tuple[list[str], list[dict[str, str]]] | None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            rows = list(reader)
    except FileNotFoundError:
        reporter.error(f"process list not found: {path}")
        return None
    except csv.Error as exc:
        reporter.error(f"could not parse process list {path}: {exc}")
        return None
    if not columns:
        reporter.error(f"process list has no header: {path}")
        return None
    return columns, rows


def resolve_process_list_path(value: Any, process_list_root: str) -> Path | None:
    if value in (None, "", "null"):
        return None
    path = Path(str(value))
    if path.exists() or path.parent != Path("."):
        return path
    return Path(process_list_root) / path


def row_is_processed(row: dict[str, str]) -> bool:
    value = row.get("process")
    if value is None or value == "":
        return True
    return str(value).strip() not in {"0", "false", "False", "FALSE", "no", "No", "NO"}


def validate_process_list(config: dict[str, Any], args: argparse.Namespace, reporter: Reporter) -> None:
    data = section(config, "data_arguments", reporter)
    heatmap = section(config, "heatmap_arguments", reporter)
    process_path = resolve_process_list_path(data.get("process_list"), args.process_list_root)

    data_dir = data.get("data_dir")
    if isinstance(data_dir, dict):
        data_dir_key = data.get("data_dir_key")
        if not data_dir_key:
            reporter.error("data_arguments.data_dir_key is required when data_arguments.data_dir is a mapping")
    elif not isinstance(data_dir, str):
        reporter.error("data_arguments.data_dir must be a slide directory string or a source-to-directory mapping")

    slide_ext = data.get("slide_ext")
    if not isinstance(slide_ext, str) or not slide_ext.startswith("."):
        reporter.warn("data_arguments.slide_ext should be a string beginning with '.', such as .svs")

    if process_path is None:
        if heatmap.get("use_roi"):
            reporter.error("heatmap_arguments.use_roi requires a process list with x1/x2/y1/y2 columns")
        reporter.warn("data_arguments.process_list is null; create_heatmaps.py will scan data_dir for slide_ext")
        return

    parsed = read_process_list(process_path, reporter)
    if parsed is None:
        return
    columns, rows = parsed
    column_set = set(columns)
    missing_base = PROCESS_LIST_BASE_COLUMNS - column_set
    if missing_base:
        reporter.error(f"process list missing required column(s): {sorted(missing_base)}")

    processed_rows = [row for row in rows if row_is_processed(row)]
    if not processed_rows:
        reporter.warn("process list has no rows selected for processing")

    if isinstance(data_dir, dict):
        key = data.get("data_dir_key")
        if key and key not in column_set:
            reporter.error(f"process list missing data_dir_key column: {key}")
        elif key:
            valid_sources = set(map(str, data_dir.keys()))
            unknown = sorted({row.get(key, "") for row in processed_rows} - valid_sources)
            if unknown:
                reporter.error(f"process list contains source key(s) not present in data_dir mapping: {unknown}")

    if heatmap.get("use_roi"):
        missing_roi = ROI_COLUMNS - column_set
        if missing_roi:
            reporter.error(f"ROI heatmaps require process-list column(s): {sorted(missing_roi)}")
        else:
            for row_index, row in enumerate(processed_rows, start=2):
                values = {name: as_float(row.get(name)) for name in ROI_COLUMNS}
                bad = [name for name, value in values.items() if value is None]
                if bad:
                    reporter.error(f"process list row {row_index} has non-numeric ROI value(s): {bad}")
                    continue
                if not (values["x1"] < values["x2"] and values["y1"] < values["y2"]):
                    reporter.error(f"process list row {row_index} ROI must satisfy x1 < x2 and y1 < y2")

    labels = {str(key) for key in (data.get("label_dict") or {}).keys()}
    if "label" in column_set and labels:
        unknown_labels = sorted(
            {
                row.get("label", "")
                for row in processed_rows
                if row.get("label", "") not in labels and row.get("label", "") != ""
            }
        )
        if unknown_labels:
            reporter.warn(f"process list label value(s) not present in label_dict: {unknown_labels}")


def validate_paths(config: dict[str, Any], args: argparse.Namespace, reporter: Reporter) -> None:
    data = section(config, "data_arguments", reporter)
    model = section(config, "model_arguments", reporter)
    exp = section(config, "exp_arguments", reporter)

    def path_issue(message: str) -> None:
        if args.strict_paths:
            reporter.error(message)
        else:
            reporter.warn(message)

    ckpt_path = model.get("ckpt_path")
    if ckpt_path and not Path(str(ckpt_path)).exists():
        path_issue(f"checkpoint path does not exist from current directory: {ckpt_path}")

    preset = data.get("preset")
    if preset not in (None, "", "null") and not Path(str(preset)).exists():
        path_issue(f"preset path does not exist from current directory: {preset}")

    data_dir = data.get("data_dir")
    if isinstance(data_dir, str) and not Path(data_dir).exists():
        path_issue(f"slide data directory does not exist from current directory: {data_dir}")
    elif isinstance(data_dir, dict):
        for key, value in data_dir.items():
            if not Path(str(value)).exists():
                path_issue(f"slide data directory for source {key!r} does not exist from current directory: {value}")

    for key in ("raw_save_dir", "production_save_dir"):
        value = exp.get(key)
        if not value:
            continue
        parent = Path(str(value)).parent
        if str(parent) != "." and not parent.exists():
            path_issue(f"parent directory for exp_arguments.{key} does not exist: {parent}")


def main() -> int:
    args = parse_args()
    reporter = Reporter()
    config_path = resolve_config_path(args.config, args.config_root, reporter)
    config = load_yaml(config_path, reporter)
    if config is not None:
        validate_required_keys(config, reporter)
        validate_exp_and_labels(config, reporter)
        validate_model_encoder(config, reporter)
        validate_patching_and_heatmap(config, reporter)
        validate_samples(config, reporter)
        validate_process_list(config, args, reporter)
        validate_paths(config, args, reporter)
    reporter.print()
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    sys.exit(main())
