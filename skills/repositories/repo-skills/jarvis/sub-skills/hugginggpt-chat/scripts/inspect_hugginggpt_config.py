#!/usr/bin/env python3
"""Safely summarize a HuggingGPT/JARVIS chat config.

The script parses YAML only. It does not import awesome_chat.py or
models_server.py, does not contact OpenAI/Hugging Face/Azure/local endpoints,
does not download models, and does not print credential values.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on caller environment
    raise SystemExit("PyYAML is required: install pyyaml before running this inspector.") from exc

CONFIG_FILES = {
    "default": "config.default.yaml",
    "lite": "config.lite.yaml",
    "gradio": "config.gradio.yaml",
    "azure": "config.azure.yaml",
}

PLACEHOLDER_MARKERS = (
    "REPLACE_WITH",
    "YOUR_",
    "CHANGEME",
    "CHANGE_ME",
    "TODO",
    "<API",
    "<TOKEN",
    "<KEY",
    "<ENDPOINT",
    "<DEPLOYMENT",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a redacted JSON summary for a HuggingGPT config."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--config",
        type=Path,
        help="Path to a HuggingGPT YAML config file.",
    )
    source.add_argument(
        "--repo-root",
        type=Path,
        help="Repository root containing hugginggpt/server/configs/.",
    )
    parser.add_argument(
        "--config-name",
        choices=sorted(CONFIG_FILES),
        default="default",
        help="Named config to inspect when --repo-root is used.",
    )
    return parser.parse_args()


def resolve_config(args: argparse.Namespace) -> Path:
    if args.config is not None:
        return args.config
    return args.repo_root / "hugginggpt" / "server" / "configs" / CONFIG_FILES[args.config_name]


def as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def is_placeholder(value: Any) -> bool:
    if is_missing(value):
        return False
    text = str(value).strip()
    upper = text.upper()
    if any(marker in upper for marker in PLACEHOLDER_MARKERS):
        return True
    if upper in {"NONE", "NULL", "N/A", "NA"}:
        return True
    if text.startswith("<") and text.endswith(">"):
        return True
    return False


def field_status(value: Any, *, prefix: Optional[str] = None) -> str:
    if is_missing(value):
        return "missing"
    if is_placeholder(value):
        return "placeholder"
    if prefix and not str(value).startswith(prefix):
        return "present_unexpected_prefix"
    return "configured"


def env_status(name: str, *, prefix: Optional[str] = None) -> str:
    value = os.environ.get(name)
    if is_missing(value):
        return "unset"
    if prefix and not str(value).startswith(prefix):
        return "set_unexpected_prefix"
    return "set"


def env_is_usable(name: str, *, prefix: Optional[str] = None) -> bool:
    value = os.environ.get(name)
    if is_missing(value):
        return False
    return bool(not prefix or str(value).startswith(prefix))


def openai_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    block = as_dict(config.get("openai"))
    status = field_status(block.get("api_key"), prefix="sk-") if block else "missing"
    env = env_status("OPENAI_API_KEY", prefix="sk-")
    effective = "config" if status == "configured" else "env" if env_is_usable("OPENAI_API_KEY", prefix="sk-") else "unavailable"
    return {
        "block_present": bool(block),
        "api_key_status": status,
        "env_OPENAI_API_KEY": env,
        "effective_source": effective,
    }


def huggingface_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    block = as_dict(config.get("huggingface"))
    status = field_status(block.get("token"), prefix="hf_") if block else "missing"
    env = env_status("HUGGINGFACE_ACCESS_TOKEN", prefix="hf_")
    effective = "config" if status == "configured" else "env" if env_is_usable("HUGGINGFACE_ACCESS_TOKEN", prefix="hf_") else "unavailable"
    return {
        "block_present": bool(block),
        "token_status": status,
        "env_HUGGINGFACE_ACCESS_TOKEN": env,
        "effective_source": effective,
    }


def azure_field_summary(block: Dict[str, Any], field: str) -> str:
    return field_status(block.get(field))


def azure_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    block = as_dict(config.get("azure"))
    fields = {
        "api_key": azure_field_summary(block, "api_key"),
        "base_url": azure_field_summary(block, "base_url"),
        "deployment_name": azure_field_summary(block, "deployment_name"),
        "api_version": azure_field_summary(block, "api_version"),
    }
    configured = bool(block) and all(status == "configured" for status in fields.values())
    return {
        "block_present": bool(block),
        "field_status": fields,
        "effective_source": "config" if configured else "unavailable",
        "env_fallback_supported_by_source": False,
    }


def local_controller_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    block = as_dict(config.get("local"))
    endpoint_status = field_status(block.get("endpoint")) if block else "missing"
    return {
        "dev_enabled": bool(config.get("dev")),
        "block_present": bool(block),
        "endpoint_status": endpoint_status,
    }


def pick_api_type(config: Dict[str, Any]) -> str:
    if config.get("dev"):
        return "local"
    if isinstance(config.get("azure"), dict):
        return "azure"
    if isinstance(config.get("openai"), dict):
        return "openai"
    return "dynamic-server-only"


def completion_endpoint_name(use_completion: Any) -> str:
    return "completions" if bool(use_completion) else "chat/completions"


def local_endpoint_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    block = as_dict(config.get("local_inference_endpoint"))
    host = block.get("host")
    port = block.get("port")
    has_host = not is_missing(host)
    has_port = not is_missing(port)
    return {
        "present": bool(block),
        "host": host if has_host else None,
        "port": port if has_port else None,
        "url": f"http://{host}:{port}" if has_host and has_port else None,
    }


def http_listen_summary(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    block = as_dict(config.get("http_listen"))
    if not block:
        return None
    return {
        "host": block.get("host"),
        "port": block.get("port"),
    }


def append_if(warnings: list[str], condition: bool, message: str) -> None:
    if condition:
        warnings.append(message)


def warning_list(config: Dict[str, Any], summary: Dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    api_type = summary["api_type"]
    inference_mode = summary["inference_mode"]
    local_required = summary["local_model_server_required"]
    model = summary["model"]
    use_completion = summary["use_completion"]

    openai = summary["credentials"]["openai"]
    hf = summary["credentials"]["huggingface"]
    azure = summary["credentials"]["azure"]
    local_controller = summary["credentials"]["local_controller"]
    local_endpoint = summary["local_inference_endpoint"]

    append_if(
        warnings,
        api_type == "openai" and openai["effective_source"] == "unavailable",
        "OpenAI controller is selected but no usable sk- OpenAI key is present in config or OPENAI_API_KEY.",
    )
    append_if(
        warnings,
        hf["effective_source"] == "unavailable",
        "No usable hf_ Hugging Face token is present in config or HUGGINGFACE_ACCESS_TOKEN; remote model status/inference will fail.",
    )
    append_if(
        warnings,
        api_type == "azure" and azure["effective_source"] == "unavailable",
        "Azure controller is selected but one or more Azure config fields are missing or placeholders; source has no Azure env-var fallback.",
    )
    append_if(
        warnings,
        api_type == "local" and local_controller["endpoint_status"] != "configured",
        "dev/local controller mode is enabled but local.endpoint is not configured.",
    )
    append_if(
        warnings,
        api_type == "dynamic-server-only",
        "No openai/azure/dev controller block is present; CLI/test cannot start, and server routes must receive api_key, api_type, and api_endpoint per request.",
    )
    append_if(
        warnings,
        local_required and not local_endpoint["url"],
        "inference_mode is local or hybrid but local_inference_endpoint host/port is incomplete; awesome_chat.py will fail its /running check.",
    )
    append_if(
        warnings,
        local_required,
        "inference_mode is local or hybrid, so a separately validated local expert-model server must answer /running before chat startup.",
    )
    append_if(
        warnings,
        inference_mode == "huggingface",
        "Pure Hugging Face inference mode does not support source ControlNet tasks such as canny-control or canny-text-to-image.",
    )
    append_if(
        warnings,
        inference_mode == "huggingface" and summary["local_deployment"] not in (None, "minimal"),
        "local_deployment is set but ignored by the chat controller's remote-only startup gate; local features still are not available.",
    )
    append_if(
        warnings,
        bool(use_completion) and str(model).startswith(("gpt-3.5", "gpt-4")),
        "use_completion is true with a chat-model-looking controller; verify the provider supports this combination.",
    )
    append_if(
        warnings,
        not bool(use_completion) and str(model).startswith("text-davinci"),
        "use_completion is false with a completion-model-looking controller; verify the provider supports chat/completions for this model.",
    )
    append_if(
        warnings,
        config.get("proxy") not in (None, ""),
        "A proxy is configured; verify it is reachable and avoid embedding proxy credentials in shared configs.",
    )
    return warnings


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except FileNotFoundError:
        raise SystemExit(f"Config file not found: {path}")
    except yaml.YAMLError as exc:
        raise SystemExit(f"YAML parse error in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Config must contain a YAML mapping at top level: {path}")
    return data


def main() -> int:
    args = parse_args()
    config_path = resolve_config(args)
    config = load_yaml(config_path)

    inference_mode = config.get("inference_mode")
    local_required = inference_mode != "huggingface"
    api_type = pick_api_type(config)

    summary: Dict[str, Any] = {
        "config_file": config_path.name,
        "model": config.get("model"),
        "use_completion": config.get("use_completion"),
        "controller_endpoint_family": completion_endpoint_name(config.get("use_completion")),
        "api_type": api_type,
        "inference_mode": inference_mode,
        "local_deployment": config.get("local_deployment"),
        "device_present": not is_missing(config.get("device")),
        "http_listen": http_listen_summary(config),
        "local_inference_endpoint": local_endpoint_summary(config),
        "credentials": {
            "openai": openai_summary(config),
            "huggingface": huggingface_summary(config),
            "azure": azure_summary(config),
            "local_controller": local_controller_summary(config),
        },
        "local_model_server_required": local_required,
        "local_model_server_requirement_reason": (
            "awesome_chat.py checks local_inference_endpoint /running when inference_mode is local or hybrid"
            if local_required
            else "inference_mode is huggingface, so awesome_chat.py does not require local expert-model /running at startup"
        ),
        "safe_behavior": {
            "network_calls": False,
            "credential_values_printed": False,
            "imports_awesome_chat": False,
            "imports_models_server": False,
            "model_downloads": False,
        },
    }
    summary["warnings"] = warning_list(config, summary)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
