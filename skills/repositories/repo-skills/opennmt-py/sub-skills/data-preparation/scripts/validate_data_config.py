#!/usr/bin/env python3
"""
Self-contained OpenNMT-py data configuration validator.

Purpose:
  Parse an OpenNMT-py YAML config, check corpus mappings, source/target
  path fields, vocabulary fields, transform/tokenizer pitfalls, source feature
  defaults, and early data-preparation failure modes before running
  onmt_build_vocab or onmt_train.

Example:
  python validate_data_config.py --config CONFIG.yaml --root . --mode build-vocab

This script intentionally does not import OpenNMT-py or modify sys.path. It only needs PyYAML for parsing.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

FEATURE_SEP = "￨"

KNOWN_TRANSFORMS = {
    "bart",
    "bpe",
    "clean",
    "docify",
    "filtertoolong",
    "fuzzymatch",
    "inferfeats",
    "inlinetags",
    "insert_mask_before_placeholder",
    "normalize",
    "onmt_tokenize",
    "prefix",
    "sentencepiece",
    "suffix",
    "switchout",
    "terminology",
    "tokendrop",
    "tokenmask",
    "uppercase",
}

TOKENIZER_TRANSFORMS = {"sentencepiece", "bpe", "onmt_tokenize"}
ALIGN_INCOMPATIBLE_TRANSFORMS = {
    "sentencepiece",
    "bpe",
    "onmt_tokenize",
    "tokendrop",
    "prefix",
    "bart",
}
VOCAB_REQUIRED_TRANSFORMS = {"bart", "switchout"}
TRANSFORM_FILE_OPTIONS = {
    "fuzzymatch": ["tm_path"],
    "inlinetags": ["tags_dictionary_path"],
    "terminology": ["termbase_path"],
}


class IssueLog:
    def __init__(self) -> None:
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []

    def error(self, message: str, where: str = "") -> None:
        self.errors.append({"where": where, "message": message})

    def warn(self, message: str, where: str = "") -> None:
        self.warnings.append({"where": where, "message": message})


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an OpenNMT-py corpus/vocabulary YAML without importing OpenNMT-py.",
    )
    parser.add_argument("--config", required=True, help="YAML config file to inspect.")
    parser.add_argument(
        "--root",
        default=".",
        help="Base directory used to check relative data/vocab paths. Default: current directory.",
    )
    parser.add_argument(
        "--mode",
        choices=["generic", "build-vocab", "train"],
        default="generic",
        help=(
            "Validation target. generic checks data shape; build-vocab requires output vocab fields; "
            "train requires existing vocab input files."
        ),
    )
    parser.add_argument(
        "--no-check-files",
        action="store_true",
        help="Skip file existence checks for corpus, vocab, tokenizer, and transform file paths.",
    )
    parser.add_argument(
        "--sample-lines",
        type=int,
        default=20,
        help="Number of nonempty source lines per corpus to sample for source-feature checks. Use 0 to skip.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return nonzero when warnings are present, not only when errors are present.",
    )
    parser.add_argument(
        "--allow-custom-transforms",
        action="store_true",
        help="Warn instead of error for transform names not in the built-in OpenNMT-py transform list.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args(argv)


def load_yaml(path: Path, issues: IssueLog) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        issues.error("PyYAML is required to parse OpenNMT-py YAML configs. Install pyyaml in this environment.")
        return {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
    except FileNotFoundError:
        issues.error(f"Config file does not exist: {path}", "config")
        return {}
    except Exception as exc:  # YAML scanners/parsers share no stable base in this no-import helper.
        issues.error(f"Could not parse YAML: {exc}", "config")
        return {}

    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        issues.error("Top-level YAML document must be a mapping.", "config")
        return {}
    return loaded


def as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1", "on"}:
            return True
        if lowered in {"false", "no", "0", "off"}:
            return False
    return default


def to_int(value: Any, issues: IssueLog, where: str, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    if isinstance(value, bool):
        issues.error("Expected an integer, got a boolean.", where)
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        issues.error(f"Expected an integer, got {value!r}.", where)
        return default


def to_float(value: Any, issues: IssueLog, where: str, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        issues.error("Expected a number, got a boolean.", where)
        return default
    try:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError
        return result
    except (TypeError, ValueError):
        issues.error(f"Expected a finite number, got {value!r}.", where)
        return default


def normalize_path(value: Any, root: Path) -> Optional[Path]:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate
    return root / candidate


def check_input_file(
    value: Any,
    root: Path,
    issues: IssueLog,
    where: str,
    check_files: bool,
) -> None:
    if value is None:
        return
    if not isinstance(value, str) or value == "":
        issues.error("Path field must be a nonempty string when present.", where)
        return
    if check_files:
        resolved = normalize_path(value, root)
        if resolved is not None and not resolved.is_file():
            issues.error(f"Input file does not exist under the selected root: {value}", where)


def check_output_path(
    value: Any,
    root: Path,
    issues: IssueLog,
    where: str,
    check_files: bool,
    overwrite: bool,
) -> None:
    if value is None:
        return
    if not isinstance(value, str) or value == "":
        issues.error("Output path must be a nonempty string when present.", where)
        return
    if not check_files:
        return
    resolved = normalize_path(value, root)
    if resolved is None:
        return
    if resolved.exists() and not overwrite:
        issues.error("Output file already exists and overwrite is false.", where)


def ensure_mapping(value: Any, issues: IssueLog, where: str) -> Optional[Mapping[str, Any]]:
    if not isinstance(value, Mapping):
        issues.error("Expected a mapping.", where)
        return None
    return value


def normalize_transform_list(value: Any, issues: IssueLog, where: str) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        issues.error("Transforms must be a YAML list, not a single string.", where)
        return [value]
    if not isinstance(value, list):
        issues.error("Transforms must be a YAML list of strings.", where)
        return []
    result: List[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str):
            issues.error(f"Transform at index {idx} is not a string: {item!r}", where)
        else:
            result.append(item)
    return result


def parse_dict_string(value: Any, issues: IssueLog, where: str) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, str):
        issues.error("Expected a dictionary string.", where)
        return None
    try:
        parsed = ast.literal_eval(value)
    except Exception as exc:
        issues.error(f"Could not parse dictionary string: {exc}", where)
        return None
    if not isinstance(parsed, dict):
        issues.error("Dictionary string did not evaluate to a dict.", where)
        return None
    return parsed


def split_defaults(value: Any, n_src_feats: int, issues: IssueLog) -> Optional[List[str]]:
    if value is None:
        return None
    if not isinstance(value, str):
        issues.error("src_feats_defaults must be a string separated by the feature delimiter.", "src_feats_defaults")
        return None
    parts = value.split(FEATURE_SEP)
    if len(parts) != n_src_feats:
        issues.error(
            f"src_feats_defaults has {len(parts)} value(s), but n_src_feats is {n_src_feats}.",
            "src_feats_defaults",
        )
    return parts


def inspect_feature_lines(
    path_value: Any,
    root: Path,
    corpus_name: str,
    n_src_feats: int,
    defaults: Optional[List[str]],
    sample_lines: int,
    issues: IssueLog,
    check_files: bool,
) -> None:
    if sample_lines <= 0 or not isinstance(path_value, str):
        return
    path = normalize_path(path_value, root)
    if path is None or not path.is_file():
        return

    checked = 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                stripped = line.rstrip("\n")
                if stripped == "":
                    continue
                checked += 1
                check_count = 0
                token_count = 0
                for raw_token in stripped.split(" "):
                    if raw_token == "":
                        continue
                    _token, *features = raw_token.split(FEATURE_SEP)
                    check_count += len(features)
                    token_count += 1
                    effective_features = features
                    if not effective_features and defaults is not None and n_src_feats > 0:
                        effective_features = defaults
                    if len(effective_features) != n_src_feats:
                        issues.error(
                            (
                                f"Token {raw_token!r} has {len(features)} explicit feature value(s); "
                                f"expected {n_src_feats}."
                            ),
                            f"data.{corpus_name}.path_src line {line_no}",
                        )
                        return
                if n_src_feats > 0 and token_count > 0 and check_count not in {0, token_count * n_src_feats}:
                    issues.error(
                        "Line mixes annotated and unannotated tokens; OpenNMT-py expects all tokens to have features or none before defaults are applied.",
                        f"data.{corpus_name}.path_src line {line_no}",
                    )
                    return
                if n_src_feats == 0 and check_count > 0:
                    issues.error(
                        "Source line contains feature separators but n_src_feats is 0.",
                        f"data.{corpus_name}.path_src line {line_no}",
                    )
                    return
                if checked >= sample_lines:
                    break
    except UnicodeDecodeError as exc:
        issues.error(f"Source file is not valid UTF-8 text: {exc}", f"data.{corpus_name}.path_src")
    except OSError as exc:
        if check_files:
            issues.error(f"Could not read source file for feature sampling: {exc}", f"data.{corpus_name}.path_src")


def validate_vocab_fields(
    config: Mapping[str, Any],
    root: Path,
    mode: str,
    issues: IssueLog,
    check_files: bool,
) -> None:
    share_vocab = as_bool(config.get("share_vocab"), default=False)
    overwrite = as_bool(config.get("overwrite"), default=False)
    src_vocab = config.get("src_vocab")
    tgt_vocab = config.get("tgt_vocab")
    save_data = config.get("save_data")
    n_sample = to_int(config.get("n_sample"), issues, "n_sample", default=None)
    dump_transforms = as_bool(config.get("dump_transforms"), default=False)

    if mode == "generic":
        if src_vocab is None:
            issues.warn("src_vocab is absent; this is acceptable only if supplied on the CLI or not yet in scope.", "src_vocab")
        if tgt_vocab is None and not share_vocab:
            issues.warn("tgt_vocab is absent and share_vocab is false; build/train modes require tgt_vocab.", "tgt_vocab")
        if save_data is None:
            issues.warn("save_data is absent; build-vocab and sample-dump workflows require it.", "save_data")
    elif mode == "build-vocab":
        if save_data is None:
            issues.error("save_data is required for onmt_build_vocab.", "save_data")
        if src_vocab is None:
            issues.error("src_vocab is required for onmt_build_vocab.", "src_vocab")
        if tgt_vocab is None and not share_vocab:
            issues.error("tgt_vocab is required for onmt_build_vocab unless share_vocab is true.", "tgt_vocab")
        if n_sample is not None and not (n_sample == -1 or n_sample > 1):
            issues.error("onmt_build_vocab expects n_sample to be -1 or greater than 1.", "n_sample")
        if n_sample is None:
            issues.warn("n_sample is not in the YAML; onmt_build_vocab defaults to a sample count unless overridden on the CLI.", "n_sample")
        check_output_path(src_vocab, root, issues, "src_vocab", check_files, overwrite)
        if not share_vocab:
            check_output_path(tgt_vocab, root, issues, "tgt_vocab", check_files, overwrite)
    elif mode == "train":
        if src_vocab is None:
            issues.error("src_vocab is required for onmt_train.", "src_vocab")
        else:
            check_input_file(src_vocab, root, issues, "src_vocab", check_files)
        if tgt_vocab is None and not share_vocab:
            issues.error("tgt_vocab is required for onmt_train unless share_vocab is true.", "tgt_vocab")
        elif not share_vocab:
            check_input_file(tgt_vocab, root, issues, "tgt_vocab", check_files)
        if n_sample not in (None, 0) or dump_transforms:
            if save_data is None:
                issues.error("save_data is required when train-mode preparation dumps samples or transforms.", "save_data")

    if share_vocab and tgt_vocab and src_vocab and tgt_vocab != src_vocab:
        issues.warn("share_vocab is true; OpenNMT-py uses src_vocab as the shared vocabulary and does not require a distinct tgt_vocab.", "tgt_vocab")

    for field in ["src_vocab_size", "tgt_vocab_size", "vocab_size_multiple", "src_words_min_frequency", "tgt_words_min_frequency"]:
        if field in config:
            value = to_int(config.get(field), issues, field, default=None)
            if value is not None and value < 0:
                issues.error(f"{field} must be nonnegative.", field)


def validate_transforms(
    config: Mapping[str, Any],
    corpus_transforms: Mapping[str, List[str]],
    all_transforms: Iterable[str],
    root: Path,
    issues: IssueLog,
    check_files: bool,
    allow_custom: bool,
    mode: str,
) -> None:
    all_transform_set = set(all_transforms)

    for transform in sorted(all_transform_set):
        if transform not in KNOWN_TRANSFORMS:
            if allow_custom:
                issues.warn(f"Transform {transform!r} is not in this helper's built-in list; assuming a custom installed transform.", "transforms")
            else:
                issues.error(f"Transform {transform!r} is not a known built-in OpenNMT-py transform.", "transforms")

    lambda_align = to_float(config.get("lambda_align"), issues, "lambda_align", default=0.0)
    if lambda_align > 0:
        bad = sorted(all_transform_set & ALIGN_INCOMPATIBLE_TRANSFORMS)
        if bad:
            issues.error(
                "lambda_align is incompatible with these configured transforms: " + ", ".join(bad),
                "lambda_align",
            )

    vocab_needed = sorted(all_transform_set & VOCAB_REQUIRED_TRANSFORMS)
    if vocab_needed and mode == "build-vocab":
        issues.warn(
            "These transforms require existing vocabularies and may be disabled or skipped while building vocab: " + ", ".join(vocab_needed),
            "transforms",
        )

    for corpus_name, transforms in corpus_transforms.items():
        if "prefix" in transforms:
            corpus = config.get("data", {}).get(corpus_name, {}) if isinstance(config.get("data"), Mapping) else {}
            if not corpus.get("src_prefix") and not corpus.get("tgt_prefix"):
                issues.warn("prefix transform is configured but both src_prefix and tgt_prefix are empty or absent.", f"data.{corpus_name}.transforms")
        if "suffix" in transforms:
            corpus = config.get("data", {}).get(corpus_name, {}) if isinstance(config.get("data"), Mapping) else {}
            if not corpus.get("src_suffix") and not corpus.get("tgt_suffix"):
                issues.warn("suffix transform is configured but both src_suffix and tgt_suffix are empty or absent.", f"data.{corpus_name}.transforms")

    for transform, options in TRANSFORM_FILE_OPTIONS.items():
        if transform in all_transform_set:
            for option in options:
                value = config.get(option)
                if value is None:
                    issues.warn(f"{transform} usually needs {option}; add it if this transform is active for real data.", option)
                else:
                    check_input_file(value, root, issues, option, check_files)

    validate_tokenizer_options(config, all_transform_set, root, issues, check_files, mode)


def validate_tokenizer_options(
    config: Mapping[str, Any],
    all_transforms: set,
    root: Path,
    issues: IssueLog,
    check_files: bool,
    mode: str,
) -> None:
    share_vocab = as_bool(config.get("share_vocab"), default=False)
    learn_subwords = as_bool(config.get("learn_subwords"), default=False)

    for field in ["src_subword_alpha", "tgt_subword_alpha"]:
        if field in config:
            value = to_float(config.get(field), issues, field, default=0.0)
            if not 0 <= value <= 1:
                issues.error(f"{field} must be in the range [0, 1].", field)

    for field in ["src_vocab_threshold", "tgt_vocab_threshold", "src_subword_nbest", "tgt_subword_nbest", "learn_subwords_size"]:
        if field in config:
            value = to_int(config.get(field), issues, field, default=None)
            if value is not None and field.endswith("threshold") and value < 0:
                issues.error(f"{field} must be nonnegative.", field)

    if "sentencepiece" in all_transforms or "bpe" in all_transforms:
        src_model = config.get("src_subword_model")
        tgt_model = config.get("tgt_subword_model")
        if src_model is None:
            issues.error("src_subword_model is required by sentencepiece/bpe transforms.", "src_subword_model")
        else:
            check_input_file(src_model, root, issues, "src_subword_model", check_files)
        if tgt_model is None and not share_vocab:
            issues.error("tgt_subword_model is required by sentencepiece/bpe transforms unless share_vocab is true and sharing is intended.", "tgt_subword_model")
        elif tgt_model is not None:
            check_input_file(tgt_model, root, issues, "tgt_subword_model", check_files)

    if "onmt_tokenize" in all_transforms:
        for side in ["src", "tgt"]:
            type_field = f"{side}_subword_type"
            model_field = f"{side}_subword_model"
            subword_type = config.get(type_field, "none")
            if subword_type not in {"none", "sentencepiece", "bpe"}:
                issues.error(f"{type_field} must be one of none, sentencepiece, or bpe.", type_field)
            if subword_type != "none":
                model_value = config.get(model_field)
                if model_value is None:
                    if mode == "build-vocab" and learn_subwords and side == "src":
                        issues.warn(f"{model_field} is absent; learn_subwords may create the source model before vocab counting.", model_field)
                    elif side == "tgt" and share_vocab:
                        issues.warn(f"{model_field} is absent; relying on shared source subword model for target side.", model_field)
                    else:
                        issues.error(f"{model_field} is required when {type_field} is {subword_type}.", model_field)
                else:
                    check_input_file(model_value, root, issues, model_field, check_files)
        for field in ["src_onmttok_kwargs", "tgt_onmttok_kwargs"]:
            parsed = parse_dict_string(config.get(field, "{'mode': 'none'}"), issues, field)
            if parsed is not None and "mode" not in parsed:
                issues.warn("pyonmttok kwargs do not include mode; the default may not match user intent.", field)

    for field in ["src_subword_vocab", "tgt_subword_vocab"]:
        value = config.get(field)
        if value not in (None, ""):
            check_input_file(value, root, issues, field, check_files)


def validate_corpora(
    config: Mapping[str, Any],
    root: Path,
    issues: IssueLog,
    check_files: bool,
    sample_lines: int,
) -> Tuple[Dict[str, List[str]], List[str]]:
    data = config.get("data")
    if data is None:
        issues.error("Top-level data mapping is required.", "data")
        return {}, []
    if isinstance(data, str):
        issues.error("Top-level data is a string; this helper expects the dynamic corpus YAML mapping used by current OpenNMT-py.", "data")
        return {}, []
    data_mapping = ensure_mapping(data, issues, "data")
    if data_mapping is None:
        return {}, []

    default_transforms = normalize_transform_list(config.get("transforms", []), issues, "transforms")
    all_transforms: List[str] = list(default_transforms)
    corpus_transforms: Dict[str, List[str]] = {}
    parallel_corpora: List[str] = []
    source_only_corpora: List[str] = []
    blockwise_corpora: List[str] = []

    n_src_feats = to_int(config.get("n_src_feats"), issues, "n_src_feats", default=0) or 0
    if n_src_feats < 0:
        issues.error("n_src_feats must be nonnegative.", "n_src_feats")
        n_src_feats = 0
    defaults = split_defaults(config.get("src_feats_defaults"), n_src_feats, issues)
    if n_src_feats == 0 and config.get("src_feats_defaults") is not None:
        issues.warn("src_feats_defaults is set while n_src_feats is 0; it will not be useful.", "src_feats_defaults")

    lambda_align = to_float(config.get("lambda_align"), issues, "lambda_align", default=0.0)

    for corpus_name, raw_corpus in data_mapping.items():
        where = f"data.{corpus_name}"
        if not isinstance(corpus_name, str) or corpus_name == "":
            issues.error("Corpus ids must be nonempty strings.", "data")
            continue
        corpus = ensure_mapping(raw_corpus, issues, where)
        if corpus is None:
            continue

        if "transforms" not in corpus:
            transforms = list(default_transforms)
            issues.warn("transforms is absent; OpenNMT-py will use the global default transform list.", f"{where}.transforms")
        else:
            transforms = normalize_transform_list(corpus.get("transforms"), issues, f"{where}.transforms")
        corpus_transforms[corpus_name] = transforms
        all_transforms.extend(transforms)

        path_src = corpus.get("path_src")
        path_tgt = corpus.get("path_tgt")
        path_txt = corpus.get("path_txt")
        path_align = corpus.get("path_align")

        if path_src is not None and path_txt is not None:
            issues.error("Use either path_src or path_txt in one corpus entry, not both.", where)
        if path_src is None and path_txt is None:
            issues.error("Corpus must define path_src or path_txt.", where)

        if path_txt is not None:
            blockwise_corpora.append(corpus_name)
            check_input_file(path_txt, root, issues, f"{where}.path_txt", check_files)
            if path_tgt is not None:
                issues.warn("path_tgt is ignored for path_txt blockwise corpora.", f"{where}.path_tgt")
        if path_src is not None:
            check_input_file(path_src, root, issues, f"{where}.path_src", check_files)
            inspect_feature_lines(path_src, root, corpus_name, n_src_feats, defaults, sample_lines, issues, check_files)
            if path_tgt is None:
                source_only_corpora.append(corpus_name)
                issues.warn("path_tgt is absent; this corpus will be treated as source-only/language-model style.", f"{where}.path_tgt")
            else:
                parallel_corpora.append(corpus_name)
                check_input_file(path_tgt, root, issues, f"{where}.path_tgt", check_files)

        if path_align is None:
            if lambda_align > 0:
                issues.error("path_align is required when lambda_align is greater than 0.", f"{where}.path_align")
        else:
            check_input_file(path_align, root, issues, f"{where}.path_align", check_files)

        weight = corpus.get("weight")
        if weight is None:
            if corpus_name != "valid":
                issues.warn("weight is absent; OpenNMT-py defaults this training corpus to weight 1.", f"{where}.weight")
        else:
            weight_number = to_float(weight, issues, f"{where}.weight", default=1.0)
            if weight_number <= 0:
                issues.error("weight must be positive.", f"{where}.weight")

        if n_src_feats > 0 and "inferfeats" not in transforms:
            issues.error("inferfeats transform is required for every corpus when n_src_feats is greater than 0.", f"{where}.transforms")

    if "valid" not in data_mapping:
        issues.warn("No valid corpus is defined; training can run without this only if validation is intentionally out of scope.", "data.valid")
    if parallel_corpora and source_only_corpora:
        issues.error(
            "Config mixes parallel corpora with source-only corpora: parallel="
            + ",".join(parallel_corpora)
            + " source-only="
            + ",".join(source_only_corpora),
            "data",
        )
    if blockwise_corpora and parallel_corpora:
        issues.warn("Config mixes path_txt blockwise corpora with parallel corpora; confirm this is intentional.", "data")

    return corpus_transforms, all_transforms


def validate_config(config: Mapping[str, Any], args: argparse.Namespace, issues: IssueLog) -> Dict[str, Any]:
    root = Path(args.root).expanduser()
    check_files = not args.no_check_files
    if check_files and not root.exists():
        issues.error(f"Selected root does not exist: {root}", "root")

    corpus_transforms, all_transforms = validate_corpora(
        config,
        root,
        issues,
        check_files=check_files,
        sample_lines=args.sample_lines,
    )
    validate_vocab_fields(config, root, args.mode, issues, check_files=check_files)
    validate_transforms(
        config,
        corpus_transforms,
        all_transforms,
        root,
        issues,
        check_files=check_files,
        allow_custom=args.allow_custom_transforms,
        mode=args.mode,
    )

    data = config.get("data")
    corpus_count = len(data) if isinstance(data, Mapping) else 0
    return {
        "mode": args.mode,
        "config": args.config,
        "root": args.root,
        "corpus_count": corpus_count,
        "all_transforms": sorted(set(all_transforms)),
        "check_files": check_files,
        "sample_lines": args.sample_lines,
    }


def emit_human(summary: Mapping[str, Any], issues: IssueLog) -> None:
    print("OpenNMT-py data config validation")
    print(f"  config: {summary['config']}")
    print(f"  root: {summary['root']}")
    print(f"  mode: {summary['mode']}")
    print(f"  corpora: {summary['corpus_count']}")
    transforms = summary.get("all_transforms", [])
    print("  transforms: " + (", ".join(transforms) if transforms else "none"))
    print(f"  file checks: {'enabled' if summary['check_files'] else 'disabled'}")
    print()

    if not issues.errors and not issues.warnings:
        print("OK: no errors or warnings.")
        return

    if issues.errors:
        print(f"ERRORS ({len(issues.errors)}):")
        for issue in issues.errors:
            prefix = f"[{issue['where']}] " if issue.get("where") else ""
            print(f"  - {prefix}{issue['message']}")
        print()
    if issues.warnings:
        print(f"WARNINGS ({len(issues.warnings)}):")
        for issue in issues.warnings:
            prefix = f"[{issue['where']}] " if issue.get("where") else ""
            print(f"  - {prefix}{issue['message']}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    issues = IssueLog()
    config_path = Path(args.config).expanduser()
    config = load_yaml(config_path, issues)
    summary: Dict[str, Any] = {
        "mode": args.mode,
        "config": args.config,
        "root": args.root,
        "corpus_count": 0,
        "all_transforms": [],
        "check_files": not args.no_check_files,
        "sample_lines": args.sample_lines,
    }
    if config and not issues.errors:
        summary = validate_config(config, args, issues)

    payload = {"summary": summary, "errors": issues.errors, "warnings": issues.warnings}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        emit_human(summary, issues)

    if issues.errors:
        return 1
    if args.strict and issues.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
