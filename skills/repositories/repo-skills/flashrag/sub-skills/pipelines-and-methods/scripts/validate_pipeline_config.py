#!/usr/bin/env python3
"""Safe FlashRAG pipeline config checker.

This script reads YAML and reports likely pipeline/method prerequisites without
importing FlashRAG, loading models, building indexes, or running inference.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

try:
    import yaml
except Exception:  # pragma: no cover - depends on runtime environment
    yaml = None
else:
    YAML_IMPORT_ERROR = None

METHODS: Dict[str, Dict[str, Any]] = {
    "naive": {"pipeline": "SequentialPipeline", "requires_retrieval": True, "requires_generator": True},
    "zero-shot": {"pipeline": "SequentialPipeline.naive_run", "requires_generator": True},
    "AAR-contriever": {"pipeline": "SequentialPipeline", "requires_retrieval": True, "requires_generator": True, "extra": ["AAR retriever checkpoint", "matching AAR index"]},
    "AAR-ANCE": {"pipeline": "SequentialPipeline", "requires_retrieval": True, "requires_generator": True, "extra": ["AAR retriever checkpoint", "matching AAR index"]},
    "llmlingua": {"pipeline": "SequentialPipeline", "requires_retrieval": True, "requires_generator": True, "requires_refiner": True, "extra": ["LongLLMLingua/Llama2-style refiner model"]},
    "recomp": {"pipeline": "SequentialPipeline", "requires_retrieval": True, "requires_generator": True, "requires_refiner": True, "extra": ["RECOMP compressor checkpoint"]},
    "selective-context": {"pipeline": "SequentialPipeline", "requires_retrieval": True, "requires_generator": True, "requires_refiner": True, "extra": ["GPT2-style refiner model", "spaCy model/package"]},
    "ret-robust": {"pipeline": "SelfAskPipeline", "requires_retrieval": True, "requires_generator": True, "extra": ["Llama2-13B base", "Ret-Robust LoRA", "single_hop decision"]},
    "sure": {"pipeline": "SuRePipeline", "requires_retrieval": True, "requires_generator": True},
    "replug": {"pipeline": "REPLUGPipeline", "requires_retrieval": True, "requires_generator": True, "extra": ["REPLUG model wrapper", "retriever scores"]},
    "skr": {"pipeline": "ConditionalPipeline", "requires_retrieval": True, "requires_generator": True, "requires_judger": True, "extra": ["SKR encoder", "judgement training data"]},
    "selfrag": {"pipeline": "SelfRAGPipeline", "requires_retrieval": True, "requires_generator": True, "framework": "vllm", "extra": ["Self-RAG checkpoint", "control tokens", "logprobs"]},
    "flare": {"pipeline": "FLAREPipeline", "requires_retrieval": True, "requires_generator": True},
    "iterretgen": {"pipeline": "IterativePipeline", "requires_retrieval": True, "requires_generator": True},
    "ircot": {"pipeline": "IRCOTPipeline", "requires_retrieval": True, "requires_generator": True},
    "trace": {"pipeline": "SequentialPipeline + kg-trace", "requires_retrieval": True, "requires_generator": True, "framework": "hf", "requires_refiner": True},
    "spring": {"pipeline": "SequentialPipeline", "requires_retrieval": True, "requires_generator": True, "framework": "hf", "extra": ["virtual token embedding file"]},
    "adaptive": {"pipeline": "AdaptivePipeline", "requires_retrieval": True, "requires_generator": True, "requires_judger": True, "extra": ["Adaptive-RAG classifier"]},
    "rqrag": {"pipeline": "RQRAGPipeline", "requires_retrieval": True, "requires_generator": True, "framework": "vllm"},
    "r1-searcher": {"pipeline": "ReasoningPipeline", "requires_retrieval": True, "requires_generator": True, "framework": "vllm"},
    "search-r1": {"pipeline": "SearchR1Pipeline", "requires_retrieval": True, "requires_generator": True, "framework": "vllm"},
    "autorefine": {"pipeline": "AutoRefinePipeline", "requires_retrieval": True, "requires_generator": True, "framework": "vllm"},
    "o2-searcher": {"pipeline": "O2SearcherPipeline", "requires_retrieval": True, "requires_generator": True, "framework": "vllm"},
    "rearag": {"pipeline": "ReaRAGPipeline", "requires_retrieval": True, "requires_generator": True, "framework": "vllm"},
    "corag": {"pipeline": "CoRAGPipeline", "requires_retrieval": True, "requires_generator": True, "framework": "vllm", "requires_task_desc": True},
    "simpledeepsearcher": {"pipeline": "SimpleDeepSearcherPipeline", "requires_retrieval": True, "requires_generator": True, "framework": "vllm"},
    "mathvista": {"pipeline": "MMSequentialPipeline", "requires_generator": True, "multimodal": True},
    "gaokao_mm": {"pipeline": "MMSequentialPipeline", "requires_generator": True, "multimodal": True},
    "mmqa": {"pipeline": "MMSequentialPipeline", "requires_generator": True, "multimodal": True},
}

REMOTE_PREFIXES = ("hf://", "s3://", "gs://", "http://", "https://")
PLACEHOLDER_VALUES = {"", "~", "none", "null", "todo", "tbd", "path/to/model", "path/to/index", "path/to/corpus"}


def strip_yaml_comment(line: str) -> str:
    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif char == "#" and quote is None:
            return line[:index]
    return line


def parse_scalar(raw: str) -> Any:
    import ast

    value = raw.strip()
    lowered = value.lower()
    if lowered in {"~", "null", "none"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return ast.literal_eval(value)
    except Exception:
        pass
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def simple_yaml_load(text: str) -> Dict[str, Any]:
    prepared: List[Tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped_comment = strip_yaml_comment(raw_line).rstrip()
        if not stripped_comment.strip():
            continue
        indent = len(stripped_comment) - len(stripped_comment.lstrip(" "))
        prepared.append((indent, stripped_comment.strip()))

    def parse_block(position: int, indent: int) -> Tuple[Any, int]:
        if position >= len(prepared):
            return {}, position
        is_list = prepared[position][1].startswith("- ")
        if is_list:
            values: List[Any] = []
            while position < len(prepared):
                line_indent, text = prepared[position]
                if line_indent < indent or not text.startswith("- "):
                    break
                item_text = text[2:].strip()
                if not item_text:
                    child, position = parse_block(position + 1, next_indent(position, line_indent))
                    values.append(child)
                    continue
                if ":" in item_text and not item_text.startswith(("'", '"')):
                    key, raw_value = item_text.split(":", 1)
                    item: Dict[str, Any] = {}
                    if raw_value.strip():
                        item[key.strip()] = parse_scalar(raw_value)
                        position += 1
                    else:
                        child, position = parse_block(position + 1, next_indent(position, line_indent))
                        item[key.strip()] = child
                    while position < len(prepared) and prepared[position][0] > line_indent and not prepared[position][1].startswith("- "):
                        child_indent, child_text = prepared[position]
                        if ":" not in child_text:
                            break
                        child_key, child_raw = child_text.split(":", 1)
                        if child_raw.strip():
                            item[child_key.strip()] = parse_scalar(child_raw)
                            position += 1
                        else:
                            child_value, position = parse_block(position + 1, next_indent(position, child_indent))
                            item[child_key.strip()] = child_value
                    values.append(item)
                else:
                    values.append(parse_scalar(item_text))
                    position += 1
            return values, position

        values: Dict[str, Any] = {}
        while position < len(prepared):
            line_indent, text = prepared[position]
            if line_indent < indent or text.startswith("- "):
                break
            if ":" not in text:
                position += 1
                continue
            key, raw_value = text.split(":", 1)
            key = key.strip()
            if raw_value.strip():
                values[key] = parse_scalar(raw_value)
                position += 1
            else:
                child, position = parse_block(position + 1, next_indent(position, line_indent))
                values[key] = child
        return values, position

    def next_indent(position: int, current_indent: int) -> int:
        next_position = position + 1
        if next_position < len(prepared) and prepared[next_position][0] > current_indent:
            return prepared[next_position][0]
        return current_indent + 2

    parsed, _ = parse_block(0, prepared[0][0] if prepared else 0)
    if not isinstance(parsed, dict):
        raise ValueError("top-level YAML value must be a mapping")
    return parsed


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        text = handle.read()
    if yaml is not None:
        loaded = yaml.safe_load(text) or {}
    else:
        loaded = simple_yaml_load(text)
    if not isinstance(loaded, dict):
        raise ValueError("top-level YAML value must be a mapping")
    return loaded


def parse_override(value: str) -> Tuple[str, Any]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("overrides must use KEY=VALUE")
    key, raw = value.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError("override key cannot be empty")
    parsed = yaml.safe_load(raw) if yaml is not None else parse_scalar(raw)
    return key, parsed


def set_dotted(config: MutableMapping[str, Any], dotted_key: str, value: Any) -> None:
    current: MutableMapping[str, Any] = config
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    current[parts[-1]] = value


def missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in PLACEHOLDER_VALUES
    return False


def looks_remote(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(REMOTE_PREFIXES)


def path_exists_if_local(value: Any, base_dir: Path) -> Optional[bool]:
    if missing(value) or not isinstance(value, str) or looks_remote(value):
        return None
    expanded = Path(os.path.expanduser(value))
    if not expanded.is_absolute():
        expanded = base_dir / expanded
    return expanded.exists()


def get_model_path(config: Mapping[str, Any], model_key_name: str, explicit_path_key: str) -> Any:
    explicit = config.get(explicit_path_key)
    if not missing(explicit):
        return explicit
    model_name = config.get(model_key_name)
    model2path = config.get("model2path")
    if isinstance(model2path, dict) and model_name in model2path:
        return model2path.get(model_name)
    return None


def add_path_note(label: str, value: Any, base_dir: Path, warnings: List[str]) -> None:
    if missing(value):
        warnings.append(f"{label} is not set")
        return
    exists = path_exists_if_local(value, base_dir)
    if exists is False:
        warnings.append(f"{label} does not exist locally: {value}")
    elif looks_remote(value):
        warnings.append(f"{label} is remote or may trigger download: {value}")


def check_retrieval(config: Mapping[str, Any], base_dir: Path, errors: List[str], warnings: List[str]) -> None:
    retrieval_method = config.get("retrieval_method")
    if missing(retrieval_method):
        errors.append("retrieval_method is required for retrieval pipelines")
    corpus_path = config.get("corpus_path")
    if missing(corpus_path):
        errors.append("corpus_path is required for retrieval pipelines unless a complete retrieval cache is used")
    else:
        add_path_note("corpus_path", corpus_path, base_dir, warnings)
    index_path = config.get("index_path")
    method2index = config.get("method2index")
    method_index = method2index.get(retrieval_method) if isinstance(method2index, dict) else None
    if missing(index_path) and missing(method_index):
        errors.append("index_path or method2index[retrieval_method] is required for dense/BM25 retrieval")
    else:
        add_path_note("index_path", index_path if not missing(index_path) else method_index, base_dir, warnings)
    retriever_path = get_model_path(config, "retrieval_method", "retriever_model_path")
    if missing(retriever_path) and retrieval_method not in {"bm25", "BM25"}:
        warnings.append("retriever model path is not resolvable from model2path/retriever_model_path")
    elif not missing(retriever_path):
        add_path_note("retriever model path", retriever_path, base_dir, warnings)


def check_generator(config: Mapping[str, Any], base_dir: Path, errors: List[str], warnings: List[str]) -> None:
    generator_model = config.get("generator_model")
    generator_path = get_model_path(config, "generator_model", "generator_model_path")
    if missing(generator_model) and missing(generator_path):
        errors.append("generator_model or generator_model_path is required")
    elif not missing(generator_path):
        add_path_note("generator model path", generator_path, base_dir, warnings)
    elif not missing(generator_model):
        warnings.append("generator_model is set but no local path is resolvable from model2path/generator_model_path")


def check_refiner(config: Mapping[str, Any], base_dir: Path, errors: List[str], warnings: List[str]) -> None:
    if missing(config.get("refiner_name")):
        warnings.append("method usually needs refiner_name; runner may provide it as an override")
    refiner_path = config.get("refiner_model_path")
    if missing(refiner_path):
        warnings.append("method usually needs refiner_model_path; runner may provide it as an override")
    else:
        add_path_note("refiner_model_path", refiner_path, base_dir, warnings)


def check_judger(config: Mapping[str, Any], base_dir: Path, errors: List[str], warnings: List[str]) -> None:
    if missing(config.get("judger_name")):
        warnings.append("method needs judger_name; runner may provide it as an override")
    judger_config = config.get("judger_config")
    if not isinstance(judger_config, dict):
        warnings.append("method needs judger_config; runner may provide it as an override")
        return
    for key in ("model_path", "training_data_path"):
        if key in judger_config and not missing(judger_config[key]):
            add_path_note(f"judger_config.{key}", judger_config[key], base_dir, warnings)


def check_multimodal(config: Mapping[str, Any], base_dir: Path, errors: List[str], warnings: List[str]) -> None:
    if not config.get("use_multi_retriever"):
        warnings.append("use_multi_retriever is not enabled; no-retrieval multimodal mode may still be valid")
        return
    setting = config.get("multi_retriever_setting")
    if not isinstance(setting, dict):
        errors.append("multi_retriever_setting must be a mapping when use_multi_retriever is true")
        return
    retrievers = setting.get("retriever_list")
    if not isinstance(retrievers, list) or not retrievers:
        errors.append("multi_retriever_setting.retriever_list must be a non-empty list")
        return
    for index, retriever in enumerate(retrievers):
        if not isinstance(retriever, dict):
            errors.append(f"retriever_list[{index}] must be a mapping")
            continue
        prefix = f"retriever_list[{index}]"
        if missing(retriever.get("retrieval_method")):
            errors.append(f"{prefix}.retrieval_method is required")
        if missing(retriever.get("corpus_path")):
            errors.append(f"{prefix}.corpus_path is required")
        else:
            add_path_note(f"{prefix}.corpus_path", retriever.get("corpus_path"), base_dir, warnings)
        if "multimodal_index_path_dict" in retriever:
            index_dict = retriever.get("multimodal_index_path_dict")
            if not isinstance(index_dict, dict) or not index_dict:
                errors.append(f"{prefix}.multimodal_index_path_dict must be a non-empty mapping")
            else:
                for modal, value in index_dict.items():
                    add_path_note(f"{prefix}.multimodal_index_path_dict.{modal}", value, base_dir, warnings)
        elif missing(retriever.get("index_path")):
            errors.append(f"{prefix}.index_path or multimodal_index_path_dict is required")
        else:
            add_path_note(f"{prefix}.index_path", retriever.get("index_path"), base_dir, warnings)


def analyze(config: Mapping[str, Any], method: str, base_dir: Path, multimodal: bool) -> Tuple[List[str], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    notes: List[str] = []
    spec = METHODS.get(method)
    if spec is None:
        errors.append(f"unknown method: {method}")
        notes.append("Known methods: " + ", ".join(sorted(METHODS)))
        return errors, warnings, notes

    notes.append(f"pipeline: {spec['pipeline']}")
    for extra in spec.get("extra", []):
        notes.append(f"prerequisite: {extra}")

    if spec.get("requires_generator"):
        check_generator(config, base_dir, errors, warnings)
    if spec.get("requires_retrieval"):
        check_retrieval(config, base_dir, errors, warnings)
    if spec.get("requires_refiner"):
        check_refiner(config, base_dir, errors, warnings)
    if spec.get("requires_judger"):
        check_judger(config, base_dir, errors, warnings)
    if spec.get("requires_task_desc") and missing(config.get("task_desc")):
        warnings.append("CoRAG needs task_desc; runner may derive it from dataset_name")

    expected_framework = spec.get("framework")
    actual_framework = config.get("framework")
    if expected_framework and not missing(actual_framework) and actual_framework != expected_framework:
        warnings.append(f"method usually expects framework={expected_framework!r}, got {actual_framework!r}")
    elif expected_framework and missing(actual_framework):
        warnings.append(f"method usually expects framework={expected_framework!r}")

    if multimodal or spec.get("multimodal"):
        check_multimodal(config, base_dir, errors, warnings)

    sample_num = config.get("test_sample_num")
    if missing(sample_num):
        warnings.append("test_sample_num is not set; full split may run if execution proceeds")
    elif isinstance(sample_num, int) and sample_num > 50:
        warnings.append(f"test_sample_num={sample_num} is larger than a smoke test")

    retrieval_topk = config.get("retrieval_topk")
    if isinstance(retrieval_topk, int) and retrieval_topk > 10:
        warnings.append(f"retrieval_topk={retrieval_topk} may increase prompt length and cost")

    generation_params = config.get("generation_params")
    if isinstance(generation_params, dict):
        max_tokens = generation_params.get("max_tokens", generation_params.get("max_new_tokens"))
        if isinstance(max_tokens, int) and max_tokens > 512:
            warnings.append(f"generation max tokens={max_tokens} is expensive for smoke tests")

    if config.get("use_retrieval_cache") and missing(config.get("retrieval_cache_path")):
        warnings.append("use_retrieval_cache is true but retrieval_cache_path is not set")
    if config.get("save_retrieval_cache") and missing(config.get("retrieval_cache_path")):
        warnings.append("save_retrieval_cache is true without an explicit retrieval_cache_path")

    return errors, warnings, notes


def print_report(method: str, errors: Sequence[str], warnings: Sequence[str], notes: Sequence[str], dry_run_plan: bool) -> None:
    status = "FAIL" if errors else "OK"
    print(f"FlashRAG pipeline config check: {status}")
    print(f"method: {method}")
    if notes:
        print("\nPlan notes:")
        for item in notes:
            print(f"  - {item}")
    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print(f"  - {item}")
    if errors:
        print("\nErrors:")
        for item in errors:
            print(f"  - {item}")
    if dry_run_plan:
        print("\nDry-run plan:")
        print("  - This checker did not import FlashRAG, load models, build indexes, or run inference.")
        print("  - Resolve errors first; review warnings before any expensive execution.")
        print("  - For smoke execution, use a tiny sample count, low retrieval_topk, and short generation tokens.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely validate a FlashRAG pipeline/method config without model execution.")
    parser.add_argument("--config", type=Path, required=True, help="YAML config file to inspect")
    parser.add_argument("--method", required=True, help="FlashRAG method key or multimodal dataset key")
    parser.add_argument("--set", dest="overrides", action="append", default=[], type=parse_override, metavar="KEY=VALUE", help="Override a config value; dotted keys are supported")
    parser.add_argument("--multimodal", action="store_true", help="Also apply multimodal retriever checks")
    parser.add_argument("--dry-run-plan", action="store_true", help="Print a safe dry-run plan reminder")
    parser.add_argument("--strict-warnings", action="store_true", help="Exit non-zero when warnings are present")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_yaml(args.config)
    except Exception as exc:
        print(f"Failed to read config: {exc}", file=sys.stderr)
        return 2
    for key, value in args.overrides:
        set_dotted(config, key, value)
    base_dir = args.config.resolve().parent
    errors, warnings, notes = analyze(config, args.method, base_dir, args.multimodal)
    print_report(args.method, errors, warnings, notes, args.dry_run_plan)
    if errors:
        return 1
    if warnings and args.strict_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
