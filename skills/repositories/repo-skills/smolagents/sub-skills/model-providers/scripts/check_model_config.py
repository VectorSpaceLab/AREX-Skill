#!/usr/bin/env python3
"""Validate smolagents model configuration shape without provider calls.

The script accepts JSON, or YAML when PyYAML is installed. It intentionally does
not import smolagents provider wrappers, instantiate clients, read secret values,
or make network calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MODEL_CLASSES = {
    "InferenceClientModel",
    "LiteLLMModel",
    "LiteLLMRouterModel",
    "OpenAIModel",
    "OpenAIServerModel",
    "AzureOpenAIModel",
    "AzureOpenAIServerModel",
    "AmazonBedrockModel",
    "TransformersModel",
    "MLXModel",
    "VLLMModel",
    "Model",
}

EXTRAS = {
    "LiteLLMModel": "smolagents[litellm]",
    "LiteLLMRouterModel": "smolagents[litellm]",
    "OpenAIModel": "smolagents[openai]",
    "OpenAIServerModel": "smolagents[openai]",
    "AzureOpenAIModel": "smolagents[openai]",
    "AzureOpenAIServerModel": "smolagents[openai]",
    "AmazonBedrockModel": "smolagents[bedrock]",
    "TransformersModel": "smolagents[transformers]",
    "MLXModel": "smolagents[mlx-lm]",
    "VLLMModel": "smolagents[vllm]",
}

SECRET_FIELD_NAMES = {
    "api_key",
    "token",
    "aws_access_key_id",
    "aws_secret_access_key",
    "aws_session_token",
}

ENV_HINTS = {
    "InferenceClientModel": ["HF_TOKEN"],
    "OpenAIModel": ["OPENAI_API_KEY"],
    "OpenAIServerModel": ["OPENAI_API_KEY"],
    "AzureOpenAIModel": ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "OPENAI_API_VERSION"],
    "AzureOpenAIServerModel": ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "OPENAI_API_VERSION"],
    "AmazonBedrockModel": ["AWS_REGION", "AWS_PROFILE", "AWS_BEARER_TOKEN_BEDROCK"],
}


def load_config(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise ValueError("YAML input requires PyYAML; use JSON or install PyYAML.") from exc
        data = yaml.safe_load(raw)
    else:
        data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Top-level config must be an object/dictionary.")
    return data


def as_mapping(config: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    class_name = config.get("class") or config.get("type") or config.get("model_class")
    params = config.get("params", config.get("kwargs", None))
    if params is None:
        params = {k: v for k, v in config.items() if k not in {"class", "type", "model_class"}}
    if not isinstance(params, dict):
        raise ValueError("`params`/`kwargs`, when present, must be an object/dictionary.")
    return class_name, params


def is_secret_literal(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    if value.startswith("${") and value.endswith("}"):
        return False
    if value.startswith("env:"):
        return False
    if "os.getenv(" in value or "os.environ" in value:
        return False
    secret_markers = ("sk-", "hf_", "xox", "akia", "-----begin")
    return any(marker in lowered for marker in secret_markers) or len(value) > 48


def walk_secrets(value: Any, path: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if str(key).lower() in SECRET_FIELD_NAMES and is_secret_literal(child):
                findings.append(child_path)
            findings.extend(walk_secrets(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(walk_secrets(child, f"{path}[{index}]"))
    return findings


def validate_config(class_name: str | None, params: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not class_name:
        errors.append("Missing model class. Use `class`, `type`, or `model_class`.")
        return errors, warnings
    if not isinstance(class_name, str):
        errors.append("Model class must be a string.")
        return errors, warnings
    if class_name not in MODEL_CLASSES:
        errors.append(f"Unknown model class `{class_name}`. Expected one of: {', '.join(sorted(MODEL_CLASSES))}.")
        return errors, warnings

    model_id = params.get("model_id")
    if class_name not in {"Model"} and class_name != "InferenceClientModel" and not model_id:
        errors.append(f"{class_name} should include `model_id`.")
    if class_name == "InferenceClientModel" and not model_id:
        warnings.append("InferenceClientModel has a default model_id, but explicit `model_id` is safer.")

    if class_name == "InferenceClientModel":
        if params.get("token") and params.get("api_key"):
            errors.append("InferenceClientModel accepts `token` or `api_key`, not both.")
        if params.get("base_url") and params.get("provider"):
            warnings.append("`base_url` bypasses provider selection; `provider` will not drive routing.")

    if class_name in {"OpenAIModel", "OpenAIServerModel"}:
        api_base = params.get("api_base")
        if api_base is not None and not isinstance(api_base, str):
            errors.append("`api_base` must be a string URL when provided.")
        if isinstance(api_base, str) and api_base and not api_base.startswith(("http://", "https://")):
            errors.append("`api_base` should start with http:// or https://.")
        if isinstance(api_base, str) and api_base.endswith("/chat/completions"):
            warnings.append("Use the API base URL, not the full /chat/completions path.")

    if class_name in {"AzureOpenAIModel", "AzureOpenAIServerModel"}:
        if not (params.get("azure_endpoint") or params.get("api_key") or params.get("api_version")):
            warnings.append("Azure config relies entirely on environment/default client values.")

    if class_name == "LiteLLMRouterModel":
        model_list = params.get("model_list")
        if not isinstance(model_list, list) or not model_list:
            errors.append("LiteLLMRouterModel requires a non-empty `model_list`.")
        else:
            model_names = {item.get("model_name") for item in model_list if isinstance(item, dict)}
            if model_id and model_id not in model_names:
                warnings.append("`model_id` does not match any `model_list[].model_name` group.")
            for index, item in enumerate(model_list):
                if not isinstance(item, dict):
                    errors.append(f"model_list[{index}] must be an object.")
                    continue
                if "litellm_params" not in item or not isinstance(item["litellm_params"], dict):
                    errors.append(f"model_list[{index}] needs object `litellm_params`.")

    if class_name == "AmazonBedrockModel":
        if "api_base" in params:
            warnings.append("Bedrock uses `client_kwargs`/AWS config, not `api_base`.")
        if "response_format" in params:
            errors.append("AmazonBedrockModel does not support `response_format`.")

    if class_name == "TransformersModel":
        if params.get("max_tokens") and params.get("max_new_tokens"):
            warnings.append("`max_tokens` aliases and overrides `max_new_tokens`.")
        device_map = params.get("device_map")
        if device_map is not None and not isinstance(device_map, str):
            errors.append("`device_map` should be a string such as 'auto', 'cuda', or 'cpu'.")

    if class_name == "MLXModel" and params.get("response_format"):
        errors.append("MLXModel does not support structured outputs/response_format.")

    if class_name == "VLLMModel" and params.get("api_base"):
        warnings.append("For an already-running vLLM OpenAI-compatible server, prefer OpenAIModel with `api_base`.")

    for secret_path in walk_secrets(params):
        warnings.append(f"Possible hardcoded secret at `{secret_path}`; prefer an environment reference.")

    extra = EXTRAS.get(class_name)
    if extra:
        warnings.append(f"Ensure optional extra is installed: {extra}.")
    env_hints = ENV_HINTS.get(class_name)
    if env_hints:
        warnings.append("Relevant environment/default credential names: " + ", ".join(env_hints) + ".")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="JSON or YAML file containing model config")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        class_name, params = as_mapping(config)
        errors, warnings = validate_config(class_name, params)
    except Exception as exc:  # noqa: BLE001 - CLI should show concise validation errors
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if class_name:
        print(f"class: {class_name}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: config shape is valid; no provider calls were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
