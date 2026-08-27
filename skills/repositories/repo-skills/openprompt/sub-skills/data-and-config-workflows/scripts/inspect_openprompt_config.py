#!/usr/bin/env python3
"""
Safe OpenPrompt config inspector.

This script is intentionally self-contained. It does not import openprompt, does
not import experiments/cli.py, does not instantiate processors, does not start
training, and does not download datasets or models. It statically summarizes an
OpenPrompt-style YAML config, checks known processor names, validates selector
branches, and optionally checks referenced local dataset/prompt-asset paths.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


KNOWN_PROCESSORS: Dict[str, Dict[str, Any]] = {
    # Text classification
    "agnews": {"family": "text_classification", "class": "AgnewsProcessor", "local": True},
    "dbpedia": {"family": "text_classification", "class": "DBpediaProcessor", "local": True},
    "amazon": {"family": "text_classification", "class": "AmazonProcessor", "local": True},
    "imdb": {"family": "text_classification", "class": "ImdbProcessor", "local": True},
    "sst-2": {"family": "text_classification", "class": "SST2Processor", "local": True},
    "mnli": {"family": "text_classification", "class": "MnliProcessor", "local": True},
    "yahoo": {"family": "text_classification", "class": "YahooProcessor", "local": True},
    # FewGLUE local
    "wic": {"family": "fewglue_local", "class": "WicProcessor", "local": True},
    "rte": {"family": "fewglue_local", "class": "RteProcessor", "local": True},
    "cb": {"family": "fewglue_local", "class": "CbProcessor", "local": True},
    "wsc": {"family": "fewglue_local", "class": "WscProcessor", "local": True},
    "boolq": {"family": "fewglue_local", "class": "BoolQProcessor", "local": True},
    "copa": {"family": "fewglue_local", "class": "CopaProcessor", "local": True},
    "multirc": {"family": "fewglue_local", "class": "MultiRcProcessor", "local": True},
    "record": {"family": "fewglue_local", "class": "RecordProcessor", "local": True, "quirk": "source static-method/signature bug; verify before use"},
    # HuggingFace datasets wrappers
    "super_glue.multirc": {"family": "huggingface", "class": "SuperglueMultiRCProcessor", "local": False},
    "super_glue.boolq": {"family": "huggingface", "class": "SuperglueBoolQProcessor", "local": False},
    "super_glue.cb": {"family": "huggingface", "class": "SuperglueCBProcessor", "local": False},
    "super_glue.copa": {"family": "huggingface", "class": "SuperglueCOPAProcessor", "local": False},
    "super_glue.rte": {"family": "huggingface", "class": "SuperglueRTEProcessor", "local": False},
    "super_glue.wic": {"family": "huggingface", "class": "SuperglueWiCProcessor", "local": False},
    "super_glue.wsc": {"family": "huggingface", "class": "SuperglueWSCProcessor", "local": False},
    "super_glue.record": {"family": "huggingface", "class": "SuperglueRecordProcessor", "local": False},
    "yahoo_answers_topics": {"family": "huggingface", "class": "YahooAnswersTopicsProcessor", "local": False},
    # Other local families
    "snli": {"family": "nli", "class": "SNLIProcessor", "local": True},
    "tacred": {"family": "relation_classification", "class": "TACREDProcessor", "local": True},
    "tacrev": {"family": "relation_classification", "class": "TACREVProcessor", "local": True},
    "retacred": {"family": "relation_classification", "class": "ReTACREDProcessor", "local": True},
    "semeval": {"family": "relation_classification", "class": "SemEvalProcessor", "local": True},
    "fewnerd": {"family": "typing", "class": "FewNERDProcessor", "local": True},
    "webnlg_2017": {"family": "conditional_generation", "class": "WebNLGProcessor", "local": True},
    "webnlg": {"family": "conditional_generation", "class": "WebNLGProcessor", "local": True},
    "csqa": {"family": "conditional_generation", "class": "CSQAProcessor", "local": True},
    "ultrachat": {"family": "conditional_generation", "class": "UltraChatProcessor", "local": True, "quirk": "processor expects a data file path rather than normal data_dir/split"},
    # Source map quirk: the original key is uppercase LAMA, but load_dataset lowercases names.
    "lama": {"family": "lama", "class": "LAMAProcessor", "local": True, "quirk": "not a normal load_dataset YAML processor; source map key is uppercase and constructor needs tokenizer/base_path"},
}

DEFAULT_SELECTOR_BRANCHES = {
    "task": {"classification", "generation", "relation_classification"},
    "template": {
        "manual_template",
        "mixed_template",
        "soft_template",
        "prefix_tuning_template",
        "ptuning_template",
        "ptr_template",
    },
    "verbalizer": {
        "manual_verbalizer",
        "one2one_verbalizer",
        "automatic_verbalizer",
        "knowledgeable_verbalizer",
        "soft_verbalizer",
        "proto_verbalizer",
        "ptr_verbalizer",
        "contextual_verbalizer",
        "generation_verbalizer",
    },
    "learning_setting": {"full", "few_shot", "few-shot", "zero_shot", "zero-shot"},
    "few_shot_sampling": {"sampling_from_train"},
    "calibrate": {"contextualized_calibrate", "pmi_calibrate"},
}

EXPECTED_PARENT = {
    "classification": "task",
    "generation": "task",
    "relation_classification": "task",
    "manual_template": "template",
    "mixed_template": "template",
    "soft_template": "template",
    "prefix_tuning_template": "template",
    "ptuning_template": "template",
    "ptr_template": "template",
    "manual_verbalizer": "verbalizer",
    "one2one_verbalizer": "verbalizer",
    "automatic_verbalizer": "verbalizer",
    "knowledgeable_verbalizer": "verbalizer",
    "soft_verbalizer": "verbalizer",
    "proto_verbalizer": "verbalizer",
    "ptr_verbalizer": "verbalizer",
    "contextual_verbalizer": "verbalizer",
    "generation_verbalizer": "verbalizer",
    "zero_shot": "learning_setting",
    "few_shot": "learning_setting",
    "sampling_from_train": "few_shot_sampling",
    "contextualized_calibrate": "calibrate",
    "pmi_calibrate": "calibrate",
}

MODEL_PATH_KEYS = {
    "plm.model_path",
    "template_generator.plm.model_path",
    "verbalizer_generator.plm.model_path",
}
OUTPUT_PATH_KEYS = {"logging.path", "logging.path_base", "checkpoint.path"}


def strip_yaml_comment(line: str) -> str:
    quote: Optional[str] = None
    escaped = False
    out = []
    for ch in line:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            out.append(ch)
            continue
        if ch == "#":
            break
        out.append(ch)
    return "".join(out).rstrip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if value in {"null", "Null", "NULL", "~", "None"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    if value.startswith("{") and value.endswith("}"):
        # Keep inline prompt-template JSON-like strings as strings in the fallback parser.
        return value
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass
    if re.fullmatch(r"[-+]?(\d+\.\d*|\d*\.\d+)([eE][-+]?\d+)?", value) or re.fullmatch(r"[-+]?\d+[eE][-+]?\d+", value):
        try:
            return float(value)
        except ValueError:
            pass
    return value


def fallback_yaml_load(text: str) -> Any:
    """Parse the simple YAML subset used by OpenPrompt example configs."""
    lines: List[Tuple[int, str, int]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        cleaned = strip_yaml_comment(raw).rstrip()
        if not cleaned.strip():
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        lines.append((indent, cleaned[indent:], lineno))

    def parse_block(index: int, indent: int) -> Tuple[Any, int]:
        if index >= len(lines):
            return {}, index
        is_list = lines[index][0] == indent and lines[index][1].startswith("- ")
        if is_list:
            result: List[Any] = []
            while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
                content = lines[index][1][2:].strip()
                index += 1
                if not content:
                    if index < len(lines) and lines[index][0] > indent:
                        item, index = parse_block(index, lines[index][0])
                    else:
                        item = None
                elif ":" in content and not content.startswith(("'", '"')):
                    key, val = content.split(":", 1)
                    item = {key.strip(): parse_scalar(val)}
                    if index < len(lines) and lines[index][0] > indent:
                        child, index = parse_block(index, lines[index][0])
                        if isinstance(child, dict):
                            item.update(child)
                else:
                    item = parse_scalar(content)
                    if index < len(lines) and lines[index][0] > indent:
                        # Fallback cannot attach nested blocks to scalars; keep the scalar and skip child.
                        _, index = parse_block(index, lines[index][0])
                result.append(item)
            return result, index

        result_dict: Dict[str, Any] = {}
        while index < len(lines):
            current_indent, content, lineno = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                break
            if content.startswith("- "):
                break
            if ":" not in content:
                raise ValueError(f"fallback parser expected key:value at line {lineno}: {content!r}")
            key, val = content.split(":", 1)
            key = key.strip()
            val = val.strip()
            index += 1
            if val:
                result_dict[key] = parse_scalar(val)
            elif index < len(lines) and lines[index][0] > current_indent:
                child, index = parse_block(index, lines[index][0])
                result_dict[key] = child
            else:
                result_dict[key] = None
        return result_dict, index

    parsed, index = parse_block(0, lines[0][0] if lines else 0)
    if index < len(lines):
        raise ValueError(f"fallback parser stopped early near line {lines[index][2]}")
    return parsed


def load_yaml_file(path: Path) -> Tuple[Any, str]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text), "PyYAML.safe_load"
    except ImportError:
        return fallback_yaml_load(text), "built-in minimal parser"


def get_nested(data: Any, dotted: str, default: Any = None) -> Any:
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def iter_leaves(data: Any, prefix: Tuple[str, ...] = ()) -> Iterable[Tuple[Tuple[str, ...], Any]]:
    if isinstance(data, dict):
        for key, value in data.items():
            yield from iter_leaves(value, prefix + (str(key),))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            yield from iter_leaves(value, prefix + (str(idx),))
    else:
        yield prefix, data


def iter_dict_nodes(data: Any, prefix: Tuple[str, ...] = ()) -> Iterable[Tuple[Tuple[str, ...], Dict[str, Any]]]:
    if isinstance(data, dict):
        yield prefix, data
        for key, value in data.items():
            yield from iter_dict_nodes(value, prefix + (str(key),))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            yield from iter_dict_nodes(value, prefix + (str(idx),))


def normalize_scalar(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def is_localish_path(value: str) -> bool:
    if value.startswith(("/", "./", "../", "~")):
        return True
    if os.sep in value or (os.altsep and os.altsep in value):
        return True
    if re.search(r"\.(txt|tsv|csv|json|jsonl|yaml|yml|pt|bin|ckpt|pkl)$", value, re.I):
        return True
    return False


def resolve_path(value: str, base_dir: Path) -> Path:
    p = Path(os.path.expanduser(value))
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()


def expected_files_for_processor(name: str) -> Sequence[str]:
    info = KNOWN_PROCESSORS.get(name, {})
    family = info.get("family")
    if family == "huggingface":
        return []
    if name in {"agnews", "mnli", "yahoo"}:
        return ["train.csv", "test.csv"]
    if name in {"dbpedia", "amazon", "imdb"}:
        return ["train.txt", "train_labels.txt", "test.txt", "test_labels.txt"]
    if name == "sst-2":
        return ["train.tsv", "dev.tsv", "test.tsv"]
    if family == "fewglue_local":
        return ["train.jsonl", "dev32.jsonl", "val.jsonl"]
    if name == "snli":
        return ["train.tsv", "dev.tsv", "test.tsv"]
    if name in {"tacred", "tacrev", "retacred"}:
        return ["train.json", "dev.json", "test.json"]
    if name == "semeval":
        return ["train.jsonl", "dev.jsonl", "test.jsonl"]
    if name == "fewnerd":
        return ["supervised/train.txt", "supervised/dev.txt", "supervised/test.txt"]
    if name in {"webnlg", "webnlg_2017"}:
        return ["train.json", "dev.json", "test.json"]
    if name == "csqa":
        return ["train_rand_split.jsonl", "dev_rand_split.jsonl", "test_rand_split_no_answers.jsonl"]
    if name == "ultrachat":
        return []
    if name == "lama":
        return ["single_relations", "29k-vocab.json", "34k-vocab.json"]
    return []


def classify_path_key(dotted: str, value: Any) -> Optional[str]:
    if value is None or isinstance(value, (dict, list, bool, int, float)):
        return None
    s = str(value).strip()
    if not s:
        return None
    last = dotted.split(".")[-1]
    if dotted == "dataset.path":
        return "dataset"
    if dotted in MODEL_PATH_KEYS:
        return "model"
    if dotted in OUTPUT_PATH_KEYS:
        return "output"
    if last == "file_path":
        return "asset"
    if last.endswith("_path") or last == "path":
        return "local_or_output"
    return None


def list_processors() -> Dict[str, Any]:
    grouped: Dict[str, List[str]] = {}
    for name, info in sorted(KNOWN_PROCESSORS.items()):
        grouped.setdefault(info["family"], []).append(name)
    return grouped


def inspect_config(config_path: Path, base_dir: Path, check_paths: bool, check_model_paths: bool) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "config": str(config_path),
        "baseDir": str(base_dir),
        "parser": None,
        "summary": {},
        "processors": {"knownCount": len(KNOWN_PROCESSORS), "byFamily": list_processors()},
        "pathReferences": [],
        "issues": [],
        "warnings": [],
        "notes": [],
    }

    try:
        data, parser_name = load_yaml_file(config_path)
        result["parser"] = parser_name
    except Exception as exc:  # noqa: BLE001 - command-line diagnostic
        result["issues"].append({"code": "YAML_PARSE_FAILED", "message": str(exc)})
        return result

    if data is None:
        data = {}
    if not isinstance(data, dict):
        result["issues"].append({"code": "YAML_NOT_MAPPING", "message": "Top-level YAML must be a mapping."})
        return result

    summary_keys = [
        "dataset.name",
        "dataset.path",
        "task",
        "learning_setting",
        "template",
        "verbalizer",
        "plm.model_name",
        "plm.model_path",
        "environment.num_gpus",
        "environment.cuda_visible_devices",
        "environment.local_rank",
        "train.batch_size",
        "dev.batch_size",
        "test.batch_size",
    ]
    summary = {key: get_nested(data, key) for key in summary_keys if get_nested(data, key) is not None}
    summary.setdefault("task", "classification (OpenPrompt default when omitted)")
    result["summary"] = summary

    dataset_name_raw = normalize_scalar(get_nested(data, "dataset.name"))
    dataset_name = dataset_name_raw.lower() if dataset_name_raw else None
    if not dataset_name_raw:
        result["issues"].append({"code": "MISSING_DATASET_NAME", "message": "config.dataset.name is absent."})
    elif dataset_name not in KNOWN_PROCESSORS:
        close = [name for name in KNOWN_PROCESSORS if dataset_name and (dataset_name in name or name in dataset_name)]
        result["issues"].append({
            "code": "UNKNOWN_DATASET_NAME",
            "message": f"dataset.name {dataset_name_raw!r} is not in the bundled OpenPrompt processor catalog.",
            "suggestions": close[:8],
        })
    else:
        info = KNOWN_PROCESSORS[dataset_name]
        result["summary"]["dataset.processorClass"] = info["class"]
        result["summary"]["dataset.processorFamily"] = info["family"]
        if info.get("quirk"):
            result["warnings"].append({"code": "PROCESSOR_QUIRK", "message": f"{dataset_name_raw}: {info['quirk']}"})
        if info["family"] == "huggingface":
            result["notes"].append({"code": "HF_DATASET", "message": f"{dataset_name_raw} wraps HuggingFace datasets; static inspection will not instantiate it or download data."})

    # Validate selector values and branches.
    top_keys = set(data.keys())
    for selector, allowed in DEFAULT_SELECTOR_BRANCHES.items():
        selected_value = normalize_scalar(get_nested(data, selector))
        if selected_value is None or selected_value == "":
            continue
        if selector == "learning_setting" and selected_value == "full":
            continue
        selected_key = selected_value.replace("-", "_") if selector == "learning_setting" else selected_value
        if selected_value not in allowed and selected_key not in allowed and selected_value not in top_keys and selected_key not in top_keys:
            result["warnings"].append({
                "code": "UNKNOWN_SELECTOR_VALUE",
                "message": f"{selector}: {selected_value!r} is not a known/default branch; verify the runtime loader supports it.",
            })
        if selected_key not in top_keys and selected_value not in top_keys and selected_value in allowed:
            # Some allowed branches are in OpenPrompt defaults; this is a note rather than a failure.
            result["notes"].append({
                "code": "BRANCH_FROM_DEFAULTS",
                "message": f"{selector}: {selected_value!r} is not defined in this YAML; OpenPrompt defaults may provide it if supported by the installed version.",
            })

    for prefix, node in iter_dict_nodes(data):
        if not prefix:
            continue
        if "parent_config" in node:
            branch = prefix[-1]
            parent = normalize_scalar(node.get("parent_config"))
            expected = EXPECTED_PARENT.get(branch)
            if expected and parent != expected:
                result["warnings"].append({
                    "code": "PARENT_CONFIG_MISMATCH",
                    "message": f"Branch {'.'.join(prefix)} declares parent_config={parent!r}; expected {expected!r} for standard OpenPrompt behavior.",
                })
            elif parent and parent not in DEFAULT_SELECTOR_BRANCHES and parent not in top_keys:
                result["warnings"].append({
                    "code": "UNKNOWN_PARENT_CONFIG",
                    "message": f"Branch {'.'.join(prefix)} declares parent_config={parent!r}, but no such selector is known or present at top level.",
                })

    learning = normalize_scalar(get_nested(data, "learning_setting"))
    if learning in {"few_shot", "few-shot"}:
        sampling = get_nested(data, "few_shot.few_shot_sampling")
        if not sampling:
            result["issues"].append({"code": "FEW_SHOT_SAMPLING_MISSING", "message": "learning_setting is few_shot but few_shot.few_shot_sampling is absent."})
        per_label = get_nested(data, "sampling_from_train.num_examples_per_label")
        total = get_nested(data, "sampling_from_train.num_examples_total")
        if per_label is not None and total is not None:
            result["issues"].append({"code": "FEW_SHOT_STRATEGY_CONFLICT", "message": "Set only one of num_examples_per_label or num_examples_total."})
        if per_label is None and total is None:
            result["warnings"].append({"code": "FEW_SHOT_STRATEGY_UNSPECIFIED", "message": "No sampling_from_train num_examples_per_label or num_examples_total found."})

    task = normalize_scalar(get_nested(data, "task")) or "classification"
    verbalizer = normalize_scalar(get_nested(data, "verbalizer"))
    if task == "generation" and verbalizer:
        result["notes"].append({"code": "GENERATION_VERBALIZER", "message": "Generation configs usually leave verbalizer empty; verify this is intentional."})
    if task != "generation" and not verbalizer:
        result["warnings"].append({"code": "CLASSIFICATION_VERBALIZER_MISSING", "message": "Classification-style configs normally set a verbalizer selector."})

    # Path references.
    for parts, value in iter_leaves(data):
        dotted = ".".join(parts)
        kind = classify_path_key(dotted, value)
        if not kind:
            continue
        value_s = str(value).strip()
        entry: Dict[str, Any] = {"key": dotted, "kind": kind, "value": value_s}
        if kind == "model" and not is_localish_path(value_s):
            entry["resolution"] = "model-id-or-cache-name"
            entry["checked"] = False
            result["notes"].append({"code": "MODEL_ID_NOT_CHECKED", "message": f"{dotted}={value_s!r} looks like a model id/cache name, not a local path."})
        elif kind == "output":
            entry["resolution"] = "output-path-not-required-for-static-validation"
            entry["checked"] = False
        else:
            resolved = resolve_path(value_s, base_dir)
            entry["resolved"] = str(resolved)
            should_check = check_paths and (kind != "model" or check_model_paths)
            entry["checked"] = should_check
            if should_check:
                exists = resolved.exists()
                entry["exists"] = exists
                if not exists:
                    code = "MISSING_ASSET_PATH" if kind == "asset" else "MISSING_REFERENCED_PATH"
                    result["issues"].append({"code": code, "message": f"{dotted} does not exist: {resolved}"})
        result["pathReferences"].append(entry)

    # Dataset path and expected split files.
    dataset_path_value = normalize_scalar(get_nested(data, "dataset.path"))
    if dataset_name and dataset_name in KNOWN_PROCESSORS:
        info = KNOWN_PROCESSORS[dataset_name]
        if info.get("family") == "huggingface":
            if not dataset_path_value:
                result["notes"].append({"code": "HF_DATASET_PATH_EMPTY", "message": "Blank dataset.path is common for HuggingFace-backed configs; runtime may use cache/network."})
        elif not dataset_path_value:
            result["warnings"].append({"code": "LOCAL_DATASET_PATH_EMPTY", "message": f"{dataset_name_raw} is a local processor but dataset.path is empty."})
        elif check_paths:
            dataset_dir = resolve_path(dataset_path_value, base_dir)
            if dataset_name == "ultrachat":
                if not dataset_dir.exists():
                    result["issues"].append({"code": "MISSING_ULTRACHAT_FILE", "message": f"UltraChat data file/path does not exist: {dataset_dir}"})
            elif dataset_dir.exists():
                missing = [rel for rel in expected_files_for_processor(dataset_name) if not (dataset_dir / rel).exists()]
                if missing:
                    result["warnings"].append({
                        "code": "DATASET_SPLITS_MISSING",
                        "message": f"{dataset_name_raw} dataset path exists but expected split/layout entries are missing.",
                        "path": str(dataset_dir),
                        "missing": missing,
                    })
            # Missing directory itself is already reported through pathReferences.

    if not check_paths:
        result["notes"].append({"code": "PATHS_NOT_CHECKED", "message": "Run with --check-paths to verify local dataset and prompt asset references."})
    if config_path.parent.name == "experiments" and base_dir == config_path.parent.resolve():
        result["notes"].append({
            "code": "EXPERIMENTS_BASE_DIR_HINT",
            "message": "Repo-style OpenPrompt examples often resolve paths from the project root, not the experiments/ directory; pass --base-dir <project-root> when adapting those configs.",
        })

    return result


def print_human(report: Dict[str, Any]) -> None:
    print("OpenPrompt config inspection")
    print(f"  config: {report.get('config')}")
    print(f"  base-dir: {report.get('baseDir')}")
    print(f"  parser: {report.get('parser')}")
    print("\nSummary:")
    for key, value in report.get("summary", {}).items():
        print(f"  {key}: {value}")
    print("\nPath references:")
    paths = report.get("pathReferences", [])
    if not paths:
        print("  (none found)")
    for entry in paths:
        bits = [f"{entry['key']}={entry['value']!r}", f"kind={entry['kind']}"]
        if "resolved" in entry:
            bits.append(f"resolved={entry['resolved']}")
        if entry.get("checked"):
            bits.append(f"exists={entry.get('exists')}")
        elif entry.get("resolution"):
            bits.append(entry["resolution"])
        print("  - " + "; ".join(bits))
    for title, key in [("Issues", "issues"), ("Warnings", "warnings"), ("Notes", "notes")]:
        items = report.get(key, [])
        print(f"\n{title}: {len(items)}")
        for item in items:
            msg = item.get("message", item)
            print(f"  - [{item.get('code', 'INFO')}] {msg}")
            if item.get("missing"):
                print("    missing: " + ", ".join(item["missing"]))
            if item.get("suggestions"):
                print("    suggestions: " + ", ".join(item["suggestions"]))
    print("\nKnown processor families:")
    for family, names in report.get("processors", {}).get("byFamily", {}).items():
        print(f"  {family}: {', '.join(names)}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inspect OpenPrompt YAML configs without training or downloads.")
    parser.add_argument("--config", type=Path, help="OpenPrompt YAML config to inspect.")
    parser.add_argument("--base-dir", type=Path, help="Base directory for resolving relative dataset and asset paths. Defaults to the config file's parent directory.")
    parser.add_argument("--check-paths", action="store_true", help="Check local dataset and prompt asset paths for existence.")
    parser.add_argument("--check-model-paths", action="store_true", help="Also check model_path values that look like local paths. Off by default because many are HuggingFace ids.")
    parser.add_argument("--list-processors", action="store_true", help="Print the bundled known OpenPrompt processor names and exit.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when issues are found.")
    args = parser.parse_args(argv)

    if args.list_processors and not args.config:
        payload = {"knownCount": len(KNOWN_PROCESSORS), "byFamily": list_processors(), "processors": KNOWN_PROCESSORS}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Known OpenPrompt processors: {len(KNOWN_PROCESSORS)}")
            for family, names in payload["byFamily"].items():
                print(f"  {family}: {', '.join(names)}")
        return 0

    if not args.config:
        parser.error("--config is required unless --list-processors is used")

    config_path = args.config.expanduser().resolve()
    if not config_path.exists():
        print(f"Config file does not exist: {config_path}", file=sys.stderr)
        return 2
    base_dir = args.base_dir.expanduser().resolve() if args.base_dir else config_path.parent.resolve()
    report = inspect_config(config_path, base_dir, args.check_paths, args.check_model_paths)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print_human(report)

    if report.get("issues") and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
