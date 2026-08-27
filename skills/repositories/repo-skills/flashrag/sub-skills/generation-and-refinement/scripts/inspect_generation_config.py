#!/usr/bin/env python3
"""Statically inspect FlashRAG generation/refiner/judger config files.

This script is intentionally safe: it parses YAML or JSON only. It does not
import FlashRAG, load models, download tokenizers, or call API services.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

SECRET_MARKERS = ("sk-", "api_key", "apikey", "token", "secret")
PLACEHOLDER_VALUES = {"", "none", "null", "your-api-key", "<openai_api_key>", "${openai_api_key}"}


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if path.suffix.lower() == ".json" or stripped.startswith("{"):
        data = json.loads(text)
    else:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on user env
            raise RuntimeError("PyYAML is required for YAML configs; use JSON or install pyyaml") from exc
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping/object")
    return data


def flatten(mapping: dict[str, Any], prefix: str = "") -> Iterable[tuple[str, Any]]:
    for key, value in mapping.items():
        dotted = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            yield from flatten(value, dotted)
        else:
            yield dotted, value


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in PLACEHOLDER_VALUES:
        return True
    return False


def add(report: list[tuple[str, str]], level: str, message: str) -> None:
    report.append((level, message))


def check_required(config: dict[str, Any], report: list[tuple[str, str]]) -> None:
    framework = config.get("framework")
    if framework not in {"hf", "vllm", "fschat", "openai"}:
        add(report, "ERROR", "framework should be one of: hf, vllm, fschat, openai")

    for key in ("generator_model", "generator_max_input_len", "generator_batch_size", "generation_params"):
        if key not in config:
            add(report, "WARN", f"missing generator key: {key}")

    model_path = config.get("generator_model_path")
    model2path = config.get("model2path")
    generator_model = config.get("generator_model")
    if framework != "openai" and is_missing(model_path):
        mapped = isinstance(model2path, dict) and generator_model in model2path
        if not mapped:
            add(report, "WARN", "generator_model_path is empty and model2path does not map generator_model")

    if framework == "openai":
        openai_setting = config.get("openai_setting")
        if not isinstance(openai_setting, dict):
            add(report, "ERROR", "framework is openai but openai_setting is missing or not a mapping")
        else:
            api_key = openai_setting.get("api_key")
            if is_missing(api_key):
                if os.getenv("OPENAI_API_KEY"):
                    add(report, "OK", "OpenAI API key is not in config; OPENAI_API_KEY is set in environment")
                else:
                    add(report, "WARN", "OpenAI API key is not set in config or OPENAI_API_KEY environment")
            elif isinstance(api_key, str) and api_key.strip().startswith("sk-"):
                add(report, "WARN", "config appears to contain a raw OpenAI-style API key; prefer environment variables")
            if openai_setting.get("api_type") == "azure":
                add(report, "INFO", "Azure OpenAI mode detected; verify endpoint, api_version, and deployment model name")


def check_generation_params(config: dict[str, Any], report: list[tuple[str, str]]) -> None:
    params = config.get("generation_params")
    if params is None:
        return
    if not isinstance(params, dict):
        add(report, "ERROR", "generation_params should be a mapping")
        return

    framework = config.get("framework")
    has_max_tokens = "max_tokens" in params
    has_max_new_tokens = "max_new_tokens" in params
    if has_max_tokens and has_max_new_tokens and params["max_tokens"] != params["max_new_tokens"]:
        add(report, "WARN", "generation_params contains different max_tokens and max_new_tokens values")
    if framework in {"hf", "fschat"} and has_max_tokens and not has_max_new_tokens:
        add(report, "INFO", "HF/FastChat paths usually resolve generation length to max_new_tokens")
    if framework in {"vllm", "openai"} and has_max_new_tokens and not has_max_tokens:
        add(report, "INFO", "vLLM/OpenAI paths usually resolve generation length to max_tokens")
    if framework == "vllm" and "do_sample" in params:
        add(report, "INFO", "vLLM path converts do_sample: false to temperature: 0")
    if framework == "openai" and "do_sample" in params:
        add(report, "INFO", "OpenAI path removes do_sample before API calls")


def check_optional_components(config: dict[str, Any], report: list[tuple[str, str]]) -> None:
    framework = config.get("framework")
    if framework == "vllm":
        add(report, "INFO", "vLLM backend requires the vllm package and compatible CUDA/PyTorch runtime")
        if config.get("generator_lora_path"):
            add(report, "INFO", "generator_lora_path is set; vLLM LoRA support must be available")
    elif framework == "openai":
        add(report, "INFO", "OpenAI backend requires openai and tiktoken packages")
    elif framework in {"hf", "fschat"}:
        add(report, "INFO", "HF/FastChat backend requires torch, transformers, and tqdm")

    model_path = config.get("generator_model_path")
    if isinstance(model_path, str) and any(name in model_path.lower() for name in ("qwen2-vl", "internvl", "llava")):
        add(report, "INFO", "multimodal-looking generator path detected; verify image dependencies and message-block inputs")
        if "qwen" in model_path.lower():
            add(report, "INFO", "Qwen-VL style models may require qwen_vl_utils")


def check_refiner(config: dict[str, Any], report: list[tuple[str, str]]) -> None:
    refiner_name = config.get("refiner_name")
    if is_missing(refiner_name):
        return
    name = str(refiner_name).lower()
    if is_missing(config.get("refiner_model_path")) and "kg-trace" not in name:
        add(report, "WARN", "refiner_name is set but refiner_model_path is empty; only some RECOMP names have defaults")
    if "lingua" in name:
        if config.get("refiner_input_prompt_flag"):
            add(report, "INFO", "LLMLingua prompt mode expects dataset items with prompt fields")
        else:
            add(report, "INFO", "LLMLingua document mode expects dataset items with retrieval_result fields")
        if "llmlinuga_config" in config and "llmlingua_config" not in config:
            add(report, "WARN", "found llmlinuga_config; FlashRAG code expects llmlingua_config")
    elif "selective-context" in name or name == "sc":
        add(report, "INFO", "Selective Context requires its compressor dependencies and sc_config tuning")
    elif "recomp" in name or "extractive" in name:
        for key in ("refiner_topk", "refiner_pooling_method", "refiner_encode_max_length"):
            if key not in config and "extractive" in name:
                add(report, "WARN", f"extractive refiner may need {key}")
    elif "kg-trace" in name:
        add(report, "INFO", "KG Trace refinement also depends on compatible retriever/generator composition")


def check_judger(config: dict[str, Any], report: list[tuple[str, str]]) -> None:
    judger_name = config.get("judger_name")
    if is_missing(judger_name):
        return
    name = str(judger_name).lower()
    judger_config = config.get("judger_config")
    if not isinstance(judger_config, dict):
        add(report, "ERROR", "judger_name is set but judger_config is missing or not a mapping")
        return
    if "skr" in name:
        for key in ("model_path", "training_data_path"):
            if is_missing(judger_config.get(key)):
                add(report, "ERROR", f"SKR judger_config missing {key}")
        add(report, "INFO", "SKR judger requires training data with ir_better/ir_worse judgement labels")
    elif "adaptive" in name:
        if is_missing(judger_config.get("model_path")):
            add(report, "ERROR", "Adaptive judger_config missing model_path")
    else:
        add(report, "ERROR", "judger_name should contain skr or adaptive for built-in FlashRAG judgers")


def check_secret_leaks(config: dict[str, Any], report: list[tuple[str, str]]) -> None:
    for dotted, value in flatten(config):
        if not isinstance(value, str):
            continue
        lower_key = dotted.lower()
        lower_value = value.lower()
        if any(marker in lower_key for marker in SECRET_MARKERS) and value and not is_missing(value):
            if "api" in lower_key or "token" in lower_key or "secret" in lower_key:
                add(report, "WARN", f"{dotted} contains a non-empty secret-like value; prefer environment variables")
        elif "sk-" in lower_value:
            add(report, "WARN", f"{dotted} appears to contain an OpenAI-style token")


def render(report: list[tuple[str, str]]) -> int:
    order = {"ERROR": 0, "WARN": 1, "INFO": 2, "OK": 3}
    for level, message in sorted(report, key=lambda item: (order.get(item[0], 9), item[1])):
        print(f"[{level}] {message}")
    if not report:
        print("[OK] No generation/refiner/judger issues detected by static checks")
    return 2 if any(level == "ERROR" for level, _ in report) else 1 if any(level == "WARN" for level, _ in report) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="FlashRAG YAML or JSON config path")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except Exception as exc:
        print(f"[ERROR] failed to parse config: {exc}", file=sys.stderr)
        return 2

    report: list[tuple[str, str]] = []
    check_required(config, report)
    check_generation_params(config, report)
    check_optional_components(config, report)
    check_refiner(config, report)
    check_judger(config, report)
    check_secret_leaks(config, report)
    return render(report)


if __name__ == "__main__":
    raise SystemExit(main())
