#!/usr/bin/env python3
"""Validate an Otter benchmark-evaluation config without loading models or datasets.

This helper mirrors the source registries and constructor-facing YAML schema for
`python -m pipeline.benchmarks.evaluate`. It performs only static checks: no
model imports, dataset downloads, API calls, or checkpoint reads.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover - depends on caller env
    yaml = None
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None

AVAILABLE_MODELS: dict[str, str] = {
    "video_chat": "VideoChat",
    "otter_video": "OtterVideo",
    "llama_adapter": "LlamaAdapter",
    "mplug_owl": "mPlug_owl",
    "video_chatgpt": "Video_ChatGPT",
    "otter_image": "OtterImage",
    "frozen_bilm": "FrozenBilm",
    "idefics": "Idefics",
    "fuyu": "Fuyu",
    "otterhd": "OtterHD",
    "instructblip": "InstructBLIP",
    "qwen_vl": "QwenVL",
    "llava_model": "LLaVA_Model",
    "gpt4v": "OpenAIGPT4Vision",
}

AVAILABLE_DATASETS: dict[str, str] = {
    "mmbench": "MMBenchDataset",
    "mme": "MMEDataset",
    "mathvista": "MathVistaDataset",
    "mmvet": "MMVetDataset",
    "seedbench": "SEEDBenchDataset",
    "pope": "PopeDataset",
    "scienceqa": "ScienceQADataset",
    "magnifierbench": "MagnifierBenchDataset",
}

MODEL_ALLOWED_KEYS: dict[str, set[str]] = {
    "fuyu": {"name", "model_path", "cuda_id", "resolution", "max_new_tokens"},
    "gpt4v": {"name", "api_key", "max_new_tokens"},
    "idefics": {"name", "model_path", "batch"},
    "instructblip": {"name", "model_path", "cuda_id", "max_new_tokens"},
    "llama_adapter": {"name", "model_path"},
    "llava_model": {"name", "model_path", "model_base", "model_name", "conv_mode"},
    "mplug_owl": {"name", "model_path"},
    "otter_image": {"name", "model_path", "load_bit"},
    "otter_video": {"name", "model_path", "load_bit"},
    "otterhd": {"name", "model_path", "cuda_id", "resolution", "max_new_tokens"},
    "qwen_vl": {"name", "model_name", "model_path"},
    "video_chat": {"name", "model_path"},
    "video_chatgpt": {"name", "model_path"},
    "frozen_bilm": {"name"},
}

DATASET_ALLOWED_KEYS: dict[str, set[str]] = {
    "magnifierbench": {"name", "data_path", "cache_dir", "default_output_path", "split", "debug", "prompt", "api_key"},
    "mathvista": {"name", "data_path", "split", "default_output_path", "cache_dir", "api_key", "gpt_model", "debug", "quick_extract"},
    "mmbench": {"name", "data_path", "sys_prompt", "version", "split", "cache_dir", "default_output_path", "debug"},
    "mme": {"name", "data_path", "cache_dir", "default_output_path", "split", "debug"},
    "mmvet": {"name", "data_path", "gpt_model", "api_key", "split", "cache_dir", "default_output_path", "num_run", "prompt", "decimail_places", "debug"},
    "pope": {"name", "data_path", "split", "default_output_path", "cache_dir", "batch_size"},
    "scienceqa": {"name", "data_path", "split", "cache_dir", "default_output_path", "batch", "debug", "prompt"},
    "seedbench": {"name", "data_path", "split", "default_output_path", "cache_dir"},
}

MODEL_PATH_REQUIRED = {"llama_adapter", "mplug_owl", "video_chat", "video_chatgpt"}
MODEL_API_KEY_REQUIRED = {"gpt4v"}
GPT_JUDGED_DATASETS = {"magnifierbench", "mmvet", "mathvista"}
BROKEN_OR_EMPTY_MODEL_IMPLEMENTATIONS = {"frozen_bilm"}
KNOWN_SPLITS: dict[str, set[str]] = {
    "mmbench": {"test", "dev"},
    "mathvista": {"test", "dev"},
}
INT_FIELDS = {"cuda_id", "resolution", "max_new_tokens", "batch", "batch_size", "num_run", "decimail_places"}
BOOL_FIELDS = {"debug", "quick_extract"}
PATH_FIELDS = {"model_path"}
STRING_PATH_FIELDS = {"cache_dir", "default_output_path", "data_path", "output"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically validate Otter benchmark evaluator YAML or CLI-style arguments. No models, datasets, or APIs are loaded.",
    )
    parser.add_argument("config", nargs="?", type=Path, help="YAML config file for pipeline.benchmarks.evaluate.")
    parser.add_argument("--models", help="CLI-mode comma-separated model names, matching pipeline.benchmarks.evaluate --models.")
    parser.add_argument(
        "--model_paths",
        "--model-paths",
        dest="model_paths",
        help="CLI-mode comma-separated model paths, matching pipeline.benchmarks.evaluate --model_paths.",
    )
    parser.add_argument("--datasets", help="CLI-mode comma-separated dataset names, matching pipeline.benchmarks.evaluate --datasets.")
    parser.add_argument("--output", "-o", default="./logs/evaluation.txt", help="Expected evaluator text-report path.")
    parser.add_argument("--cache_dir", "--cache-dir", dest="cache_dir", default=None, help="CLI-mode dataset cache directory.")
    parser.add_argument("--strict", action="store_true", help="Treat unknown constructor keys as errors instead of warnings.")
    parser.add_argument(
        "--allow-missing-credentials",
        action="store_true",
        help="Downgrade missing GPT/API credentials to warnings and skip reasons instead of errors.",
    )
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="For local-looking model_path values, verify that the path exists. Remote Hugging Face ids are not checked.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON validation report.")
    return parser.parse_args()


def split_csv(value: str | None) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def add(report: dict[str, Any], level: str, message: str, where: str | None = None) -> None:
    entry: dict[str, Any] = {"level": level, "message": message}
    if where:
        entry["where"] = where
    report[level + "s"].append(entry)


def add_skip(report: dict[str, Any], message: str, where: str | None = None) -> None:
    entry: dict[str, Any] = {"message": message}
    if where:
        entry["where"] = where
    report["skip_reasons"].append(entry)


def load_yaml_config(path: Path, report: dict[str, Any]) -> dict[str, Any] | None:
    if yaml is None:
        add(report, "error", f"PyYAML is required to parse config YAML: {YAML_IMPORT_ERROR}")
        return None
    if not path.exists():
        add(report, "error", "Config file does not exist", str(path))
        return None
    if not path.is_file():
        add(report, "error", "Config path is not a file", str(path))
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:
        add(report, "error", f"Could not parse YAML: {exc}", str(path))
        return None
    if data is None:
        add(report, "error", "Config file is empty", str(path))
        return None
    if not isinstance(data, dict):
        add(report, "error", "Top-level config must be a mapping/object", str(path))
        return None
    return data


def synthesize_cli_config(args: argparse.Namespace, report: dict[str, Any]) -> dict[str, Any] | None:
    model_names = split_csv(args.models)
    dataset_names = split_csv(args.datasets)
    model_paths = split_csv(args.model_paths)

    if not model_names or not dataset_names:
        add(report, "error", "Provide a YAML config or both --models and --datasets for CLI-mode validation")
        return None

    if args.model_paths is not None and len(model_paths) != len(model_names):
        add(report, "error", "--model_paths count should match --models count; the evaluator zips these lists", "--model_paths")

    models: list[dict[str, Any]] = []
    for idx, name in enumerate(model_names):
        item: dict[str, Any] = {"name": name}
        if idx < len(model_paths):
            item["model_path"] = model_paths[idx]
        models.append(item)

    datasets: list[dict[str, Any]] = []
    for name in dataset_names:
        item = {"name": name}
        if args.cache_dir is not None:
            item["cache_dir"] = args.cache_dir
        datasets.append(item)

    return {"output": args.output, "models": models, "datasets": datasets}


def looks_like_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    text = value.strip()
    if not text:
        return True
    lower = text.lower()
    placeholder_exact = {
        "none",
        "null",
        "todo",
        "tbd",
        "changeme",
        "change-me",
        "your-api-key",
        "your api key",
        "openai_api_key",
        "api_key",
    }
    if lower in placeholder_exact:
        return True
    placeholder_fragments = ["${", "$openai", "your gpt", "you gpt", "replace", "<api", "[you", "[your", "xxx"]
    return any(fragment in lower for fragment in placeholder_fragments)


def credential_problem(report: dict[str, Any], args: argparse.Namespace, where: str, message: str) -> None:
    if args.allow_missing_credentials:
        add(report, "warning", message + "; mark this benchmark/model as skipped unless a real key is provided", where)
        add_skip(report, message, where)
    else:
        add(report, "error", message, where)


def path_looks_local(path_text: str) -> bool:
    expanded = os.path.expanduser(path_text)
    return os.path.isabs(expanded) or path_text.startswith((".", "~/", "../"))


def check_local_path(report: dict[str, Any], where: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        return
    if not path_looks_local(value):
        return
    candidate = Path(os.path.expanduser(value))
    if not candidate.exists():
        add(report, "error", f"Local model_path does not exist: {value}", where)


def validate_output_path(report: dict[str, Any], output: Any, where: str = "output") -> None:
    if not isinstance(output, str) or not output.strip():
        add(report, "error", "output must be a non-empty string path", where)
        return
    if os.path.dirname(output) == "":
        add(report, "error", "output should include a directory component, e.g. ./logs/evaluation.txt", where)


def validate_top_level(config: dict[str, Any], report: dict[str, Any], args: argparse.Namespace) -> tuple[list[Any], list[Any]]:
    allowed_top = {"models", "datasets", "output"}
    extra_top = sorted(set(config) - allowed_top)
    for key in extra_top:
        level = "error" if args.strict else "warning"
        add(report, level, "Unknown top-level key; YAML mode only consumes models, datasets, and output", key)

    if "cache_dir" in config:
        add(report, "warning", "Top-level cache_dir is ignored by YAML mode; put cache_dir inside each dataset entry", "cache_dir")

    output = config.get("output", "./logs/evaluation.txt")
    validate_output_path(report, output)

    models = config.get("models")
    datasets = config.get("datasets")
    if not isinstance(models, list) or not models:
        add(report, "error", "models must be a non-empty list", "models")
        models = []
    if not isinstance(datasets, list) or not datasets:
        add(report, "error", "datasets must be a non-empty list", "datasets")
        datasets = []
    return models, datasets


def validate_unknown_keys(
    report: dict[str, Any],
    args: argparse.Namespace,
    item: dict[str, Any],
    allowed: set[str],
    where: str,
) -> None:
    extras = sorted(set(item) - allowed)
    if extras:
        level = "error" if args.strict else "warning"
        add(report, level, "Unknown constructor key(s): " + ", ".join(extras), where)


def validate_common_types(report: dict[str, Any], item: dict[str, Any], where: str) -> None:
    for key, value in item.items():
        key_where = f"{where}.{key}"
        if key in INT_FIELDS and not isinstance(value, int):
            add(report, "warning", f"{key} is usually an integer", key_where)
        if key in BOOL_FIELDS and not isinstance(value, bool):
            add(report, "warning", f"{key} is usually a boolean", key_where)
        if key in STRING_PATH_FIELDS and value is not None and not isinstance(value, str):
            add(report, "warning", f"{key} is usually a string path or dataset id", key_where)


def validate_model(report: dict[str, Any], args: argparse.Namespace, item: Any, index: int) -> None:
    where = f"models[{index}]"
    if not isinstance(item, dict):
        add(report, "error", "Model entry must be a mapping/object", where)
        return
    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        add(report, "error", "Model entry requires non-empty string name", where)
        return
    name = name.strip()
    report["model_names"].append(name)

    if name not in AVAILABLE_MODELS:
        add(report, "error", f"Unknown model registry key: {name}", f"{where}.name")
        return

    if name in BROKEN_OR_EMPTY_MODEL_IMPLEMENTATIONS:
        add(report, "error", f"Model key {name!r} is registered but has no usable implementation in the inspected source", where)

    validate_unknown_keys(report, args, item, MODEL_ALLOWED_KEYS.get(name, {"name"}), where)
    validate_common_types(report, item, where)

    if name in MODEL_PATH_REQUIRED and not item.get("model_path"):
        add(report, "error", f"Model {name!r} requires model_path", f"{where}.model_path")
    if name in MODEL_API_KEY_REQUIRED and looks_like_placeholder(item.get("api_key")):
        credential_problem(report, args, f"{where}.api_key", f"Model {name!r} requires a real API key")

    if args.check_paths and "model_path" in item:
        check_local_path(report, f"{where}.model_path", item.get("model_path"))


def validate_dataset(report: dict[str, Any], args: argparse.Namespace, item: Any, index: int) -> None:
    where = f"datasets[{index}]"
    if not isinstance(item, dict):
        add(report, "error", "Dataset entry must be a mapping/object", where)
        return
    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        add(report, "error", "Dataset entry requires non-empty string name", where)
        return
    name = name.strip()
    report["dataset_names"].append(name)

    if name not in AVAILABLE_DATASETS:
        add(report, "error", f"Unknown dataset registry key: {name}", f"{where}.name")
        if name.lower() in {"sicenceqa", "science_qa", "science-q-a"}:
            add(report, "warning", "Use the actual registry key scienceqa", f"{where}.name")
        return

    validate_unknown_keys(report, args, item, DATASET_ALLOWED_KEYS.get(name, {"name"}), where)
    validate_common_types(report, item, where)

    split = item.get("split")
    if name in KNOWN_SPLITS and split is not None and split not in KNOWN_SPLITS[name]:
        add(report, "error", f"Dataset {name!r} supports split values {sorted(KNOWN_SPLITS[name])} in the inspected constructor", f"{where}.split")

    if name in GPT_JUDGED_DATASETS and looks_like_placeholder(item.get("api_key")):
        credential_problem(report, args, f"{where}.api_key", f"Dataset {name!r} needs a real GPT/OpenAI-compatible API key for full evaluation")


def validate_config(config: dict[str, Any], report: dict[str, Any], args: argparse.Namespace) -> None:
    models, datasets = validate_top_level(config, report, args)
    report["models"] = len(models)
    report["datasets"] = len(datasets)
    for index, item in enumerate(models):
        validate_model(report, args, item, index)
    for index, item in enumerate(datasets):
        validate_dataset(report, args, item, index)

    if report["datasets"] and report["models"]:
        gpt_datasets = [name for name in report["dataset_names"] if name in GPT_JUDGED_DATASETS]
        if gpt_datasets:
            add(report, "warning", "GPT-judged datasets selected: " + ", ".join(gpt_datasets), "datasets")


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {
        "valid": False,
        "mode": "config" if args.config else "cli",
        "config": str(args.config) if args.config else None,
        "models": 0,
        "datasets": 0,
        "model_names": [],
        "dataset_names": [],
        "errors": [],
        "warnings": [],
        "skip_reasons": [],
    }

    if args.config:
        config = load_yaml_config(args.config, report)
    else:
        config = synthesize_cli_config(args, report)

    if config is not None:
        validate_config(config, report, args)

    report["valid"] = not report["errors"]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=False))
    else:
        status = "VALID" if report["valid"] else "INVALID"
        target = str(args.config) if args.config else "CLI arguments"
        print(f"{status}: {target}")
        print(f"Models ({report['models']}): {', '.join(report['model_names']) or '-'}")
        print(f"Datasets ({report['datasets']}): {', '.join(report['dataset_names']) or '-'}")
        for collection in ("errors", "warnings"):
            for entry in report[collection]:
                where = f" {entry['where']}:" if "where" in entry else ""
                print(f"{entry['level'].upper()}{where} {entry['message']}")
        for entry in report["skip_reasons"]:
            where = f" {entry['where']}:" if "where" in entry else ""
            print(f"SKIP{where} {entry['message']}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
