#!/usr/bin/env python3
"""Validate an OpenNMT-py translation server model_config JSON file.

The validator checks the shape of the JSON consumed by `onmt_server` and the
runtime `TranslationServer`: top-level models list, per-model paths and flags,
tokenizer configuration, feature routing, hook lists, and CTranslate2 fields.

It is intentionally self-contained and avoids importing the OpenNMT-py source
checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VALID_TIMEOUT_ACTIONS = {"to_cpu", "unload"}
VALID_TOKENIZER_TYPES = {"sentencepiece", "pyonmttok"}
VALID_REVERSIBLE_TOKENIZATION = {"joiner", "spacer"}
DEFAULT_OPT_VALUES = {
    "gpu": -1,
    "beam_size": 5,
    "batch_size": 30,
    "n_best": 1,
    "max_length": 250,
    "min_length": 0,
}


@dataclass
class Message:
    level: str
    text: str


class Report:
    def __init__(self) -> None:
        self.errors: list[Message] = []
        self.warnings: list[Message] = []

    def error(self, text: str) -> None:
        self.errors.append(Message("error", text))

    def warn(self, text: str) -> None:
        self.warnings.append(Message("warning", text))

    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok(),
            "errors": [m.text for m in self.errors],
            "warnings": [m.text for m in self.warnings],
        }

    def emit(self, as_json: bool = False) -> None:
        if as_json:
            print(json.dumps(self.as_dict(), indent=2, sort_keys=True))
            return
        for warning in self.warnings:
            print(f"warning: {warning.text}", file=sys.stderr)
        for error in self.errors:
            print(f"error: {error.text}", file=sys.stderr)
        if self.warnings:
            print(f"warning_count: {len(self.warnings)}", file=sys.stderr)
        if self.errors:
            print(f"error_count: {len(self.errors)}", file=sys.stderr)


def is_string(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def resolve_path(base: Path, raw: str) -> Path:
    candidate = Path(raw).expanduser()
    return candidate if candidate.is_absolute() else base / candidate


def check_path(report: Report, base: Path, raw: Any, context: str, field: str, *, required: bool = True, check_files: bool = True) -> None:
    if raw is None:
        return
    if not is_string(raw):
        report.error(f"{context}.{field} must be a non-empty string")
        return
    if check_files:
        path = resolve_path(base, raw)
        if not path.exists():
            level = report.error if required else report.warn
            level(f"{context}.{field} path does not exist: {path}")


def ensure_list(report: Report, value: Any, context: str, field: str) -> list[Any]:
    if not isinstance(value, list):
        report.error(f"{context}.{field} must be a list")
        return []
    return value


def ensure_str_list(report: Report, value: Any, context: str, field: str) -> list[str]:
    items = ensure_list(report, value, context, field)
    out: list[str] = []
    for idx, item in enumerate(items):
        if not is_string(item):
            report.error(f"{context}.{field}[{idx}] must be a non-empty string")
        else:
            out.append(item)
    return out


def validate_tokenizer(report: Report, tokenizer: Any, model_root: Path, context: str, *, check_files: bool) -> None:
    if not isinstance(tokenizer, dict):
        report.error(f"{context}.tokenizer must be an object")
        return

    if "src" in tokenizer or "tgt" in tokenizer:
        if not ("src" in tokenizer and "tgt" in tokenizer):
            report.error(f"{context}.tokenizer must contain both src and tgt when using side-specific tokenizers")
            return
        validate_single_tokenizer(report, tokenizer["src"], model_root, f"{context}.tokenizer.src", check_files=check_files)
        validate_single_tokenizer(report, tokenizer["tgt"], model_root, f"{context}.tokenizer.tgt", check_files=check_files)
        return

    validate_single_tokenizer(report, tokenizer, model_root, f"{context}.tokenizer", check_files=check_files)


def validate_single_tokenizer(report: Report, spec: Any, model_root: Path, context: str, *, check_files: bool) -> None:
    if not isinstance(spec, dict):
        report.error(f"{context} must be an object")
        return

    tokenizer_type = spec.get("type")
    if tokenizer_type not in VALID_TOKENIZER_TYPES:
        report.error(f"{context}.type must be one of {sorted(VALID_TOKENIZER_TYPES)}")
        return

    if tokenizer_type == "sentencepiece":
        check_path(report, model_root, spec.get("model"), context, "model", check_files=check_files)
        return

    if "mode" not in spec:
        report.error(f"{context}.mode is required for pyonmttok")
    elif spec["mode"] is not None and not is_string(spec["mode"]):
        report.error(f"{context}.mode must be a string or null")

    params = spec.get("params")
    if not isinstance(params, dict):
        report.error(f"{context}.params must be an object")
        return

    for key, value in params.items():
        if key.endswith("path"):
            check_path(report, model_root, value, f"{context}.params", key, check_files=check_files)


def validate_features(report: Report, features: Any, context: str) -> None:
    if not isinstance(features, dict):
        report.error(f"{context}.features must be an object")
        return

    n_src_feats = features.get("n_src_feats")
    if n_src_feats is not None and not is_int(n_src_feats):
        report.error(f"{context}.features.n_src_feats must be an integer")

    defaults = features.get("src_feats_defaults")
    if defaults is not None and not is_string(defaults):
        report.error(f"{context}.features.src_feats_defaults must be a string or null")
    if is_int(n_src_feats) and is_string(defaults) and len(defaults.split("￨")) != n_src_feats:
        report.error(
            f"{context}.features.src_feats_defaults contains {len(defaults.split('￨'))} values, expected {n_src_feats}"
        )

    reversible = features.get("reversible_tokenization")
    if reversible is not None and reversible not in VALID_REVERSIBLE_TOKENIZATION:
        report.error(f"{context}.features.reversible_tokenization must be one of {sorted(VALID_REVERSIBLE_TOKENIZATION)}")


def validate_translate_opt(report: Report, opt: Any, context: str) -> None:
    if not isinstance(opt, dict):
        report.error(f"{context}.opt must be an object")
        return

    for key in ("gpu", "beam_size", "batch_size", "n_best", "max_length", "min_length", "world_size"):
        if key in opt and not is_int(opt[key]):
            report.error(f"{context}.opt.{key} must be an integer")

    for key in ("report_align", "gold_align", "replace_unk", "tgt_file_prefix", "with_score", "verbose"):
        if key in opt and not is_bool(opt[key]):
            report.error(f"{context}.opt.{key} must be a boolean")

    if opt.get("model_task") not in {None, "lm", "seq2seq"}:
        report.error(f"{context}.opt.model_task must be 'lm' or 'seq2seq'")

    if "transforms" in opt:
        ensure_str_list(report, opt["transforms"], f"{context}.opt", "transforms")

    if opt.get("gold_align"):
        if not opt.get("report_align", False):
            report.error(f"{context}.opt.gold_align requires {context}.opt.report_align=true")
        if not is_string(opt.get("tgt")):
            report.error(f"{context}.opt.gold_align requires {context}.opt.tgt")
        if opt.get("replace_unk", False):
            report.error(f"{context}.opt.gold_align cannot be combined with replace_unk")


def validate_ct2(report: Report, opt: Any, ct2_translator_args: Any, ct2_translate_batch_args: Any, context: str) -> None:
    if ct2_translator_args is not None and not isinstance(ct2_translator_args, dict):
        report.error(f"{context}.ct2_translator_args must be an object")
        ct2_translator_args = None
    if ct2_translate_batch_args is not None and not isinstance(ct2_translate_batch_args, dict):
        report.error(f"{context}.ct2_translate_batch_args must be an object")
        ct2_translate_batch_args = None

    if not isinstance(opt, dict):
        return

    gpu = opt.get("gpu", DEFAULT_OPT_VALUES["gpu"])
    if not is_int(gpu):
        return

    expected_device = "cuda" if gpu > -1 else "cpu"
    expected_device_index = gpu if gpu > -1 else 0

    if ct2_translator_args:
        if "device" in ct2_translator_args and ct2_translator_args["device"] != expected_device:
            report.error(f"{context}.ct2_translator_args.device must be {expected_device!r} when opt.gpu={gpu}")
        if "device_index" in ct2_translator_args:
            device_index = ct2_translator_args["device_index"]
            if not is_int(device_index) or device_index < 0:
                report.error(f"{context}.ct2_translator_args.device_index must be a non-negative integer")
            elif device_index != expected_device_index:
                report.error(f"{context}.ct2_translator_args.device_index must be {expected_device_index} when opt.gpu={gpu}")
        if "inter_threads" in ct2_translator_args and not is_int(ct2_translator_args["inter_threads"]):
            report.error(f"{context}.ct2_translator_args.inter_threads must be an integer")
        if "intra_threads" in ct2_translator_args and not is_int(ct2_translator_args["intra_threads"]):
            report.error(f"{context}.ct2_translator_args.intra_threads must be an integer")
        if "compute_type" in ct2_translator_args and not is_string(ct2_translator_args["compute_type"]):
            report.error(f"{context}.ct2_translator_args.compute_type must be a string")

    if ct2_translate_batch_args:
        expected_pairs = {
            "beam_size": opt.get("beam_size", DEFAULT_OPT_VALUES["beam_size"]),
            "max_batch_size": opt.get("batch_size", DEFAULT_OPT_VALUES["batch_size"]),
            "num_hypotheses": opt.get("n_best", DEFAULT_OPT_VALUES["n_best"]),
            "max_decoding_length": opt.get("max_length", DEFAULT_OPT_VALUES["max_length"]),
            "min_decoding_length": opt.get("min_length", DEFAULT_OPT_VALUES["min_length"]),
        }
        for key, expected in expected_pairs.items():
            if key in ct2_translate_batch_args and ct2_translate_batch_args[key] != expected:
                report.error(f"{context}.ct2_translate_batch_args.{key} must match opt value {expected!r}")


def validate_model_entry(report: Report, entry: Any, top_models_root: Path, root: Path, index: int, *, check_files: bool) -> None:
    context = f"models[{index}]"
    if not isinstance(entry, dict):
        report.error(f"{context} must be an object")
        return

    if "id" in entry and not is_int(entry["id"]):
        report.error(f"{context}.id must be an integer")
    elif "id" not in entry:
        report.warn(f"{context} has no id; the server will auto-assign one")

    if "load" in entry and not is_bool(entry["load"]):
        report.error(f"{context}.load must be a boolean")

    if "timeout" in entry:
        timeout = entry["timeout"]
        if not is_int(timeout):
            report.error(f"{context}.timeout must be an integer")
        elif timeout < -1:
            report.error(f"{context}.timeout must be >= -1")

    if entry.get("on_timeout") not in {None, *VALID_TIMEOUT_ACTIONS}:
        report.error(f"{context}.on_timeout must be one of {sorted(VALID_TIMEOUT_ACTIONS)}")

    if "models" in entry:
        model_list = ensure_str_list(report, entry["models"], context, "models")
    elif "model" in entry:
        report.warn(f"{context} uses legacy 'model'; prefer a 'models' list")
        model_list = ensure_str_list(report, [entry["model"]], context, "models")
    else:
        report.error(f"{context} must contain a 'models' list or legacy 'model' entry")
        model_list = []

    entry_root_raw = entry.get("model_root", str(top_models_root))
    if entry_root_raw is not None and not is_string(entry_root_raw):
        report.error(f"{context}.model_root must be a non-empty string")
        entry_root = top_models_root
    else:
        entry_root = resolve_path(root, entry_root_raw) if is_string(entry_root_raw) else top_models_root

    if check_files:
        for rel_path in model_list:
            check_path(report, top_models_root, rel_path, context, "models", check_files=True)
            if entry_root != top_models_root:
                check_path(report, entry_root, rel_path, context, "models@model_root", check_files=True, required=False)

    if "opt" in entry:
        validate_translate_opt(report, entry["opt"], context)

    if "tokenizer" in entry:
        validate_tokenizer(report, entry["tokenizer"], entry_root, context, check_files=check_files)

    if "features" in entry:
        validate_features(report, entry["features"], context)

    if "preprocess" in entry:
        ensure_str_list(report, entry["preprocess"], context, "preprocess")
    if "postprocess" in entry:
        ensure_str_list(report, entry["postprocess"], context, "postprocess")
    if "custom_opt" in entry and not isinstance(entry["custom_opt"], dict):
        report.error(f"{context}.custom_opt must be an object")

    if "ct2_model" in entry:
        check_path(report, entry_root, entry["ct2_model"], context, "ct2_model", check_files=check_files)

    validate_ct2(report, entry.get("opt", {}), entry.get("ct2_translator_args"), entry.get("ct2_translate_batch_args"), context)


def validate_config(data: Any, root: Path, *, check_files: bool) -> Report:
    report = Report()
    if not isinstance(data, dict):
        report.error("top-level JSON value must be an object")
        return report

    models_root_raw = data.get("models_root", "./available_models")
    if not is_string(models_root_raw):
        report.error("models_root must be a non-empty string when present")
        models_root_raw = "./available_models"
    models_root = resolve_path(root, models_root_raw)

    if check_files and not models_root.exists():
        report.error(f"models_root does not exist: {models_root}")

    models = data.get("models")
    if not isinstance(models, list) or not models:
        report.error("top-level models must be a non-empty list")
        return report

    for index, entry in enumerate(models):
        validate_model_entry(report, entry, models_root, root, index, check_files=check_files)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an OpenNMT-py translation server config JSON")
    parser.add_argument("config", nargs="?", help="Path to the server model_config JSON file")
    parser.add_argument("--config", dest="config_opt", help="Path to the server model_config JSON file")
    parser.add_argument("--root", default=".", help="Base directory used to resolve relative model and tokenizer paths")
    parser.add_argument("--no-check-files", action="store_true", help="Skip file existence checks")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when warnings are present")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = args.config_opt or args.config
    if not config:
        print("error: missing config path", file=sys.stderr)
        return 2

    config_path = Path(config).expanduser()
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        print(f"error: config file not found: {config_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {config_path}: {exc}", file=sys.stderr)
        return 1

    root = Path(args.root).expanduser()
    report = validate_config(data, root, check_files=not args.no_check_files)
    report.emit(as_json=args.json)

    if report.errors:
        return 1
    if args.strict and report.warnings:
        return 1

    if not args.json:
        print(f"Validated {len(data.get('models', [])) if isinstance(data, dict) else 0} server model entries from {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
