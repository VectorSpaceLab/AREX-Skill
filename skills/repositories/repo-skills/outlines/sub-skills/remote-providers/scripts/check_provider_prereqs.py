#!/usr/bin/env python3
"""Read-only prerequisite probe for Outlines remote-provider integrations.

The script checks Python SDK importability and whether named environment
variables are present. It never instantiates provider clients, never calls
network services, and never prints secret values.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class EnvVar:
    name: str
    required: bool
    purpose: str
    placeholder: bool = False


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    modules: tuple[str, ...]
    env: tuple[EnvVar, ...]
    notes: str


PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec(
        name="openai",
        modules=("openai",),
        env=(
            EnvVar("OPENAI_API_KEY", True, "OpenAI API key"),
            EnvVar("OPENAI_BASE_URL", False, "Optional OpenAI-compatible base URL"),
        ),
        notes="Use from_openai for OpenAI/Azure/generic OpenAI-compatible APIs.",
    ),
    "azure-openai": ProviderSpec(
        name="azure-openai",
        modules=("openai",),
        env=(
            EnvVar("AZURE_OPENAI_API_KEY", True, "Azure OpenAI API key"),
            EnvVar("AZURE_OPENAI_ENDPOINT", True, "Azure OpenAI endpoint"),
            EnvVar("AZURE_OPENAI_API_VERSION", True, "Azure OpenAI API version placeholder"),
        ),
        notes="Azure uses the OpenAI SDK family and from_openai.",
    ),
    "anthropic": ProviderSpec(
        name="anthropic",
        modules=("anthropic",),
        env=(EnvVar("ANTHROPIC_API_KEY", True, "Anthropic API key"),),
        notes="Sync wrapper only in this Outlines source revision.",
    ),
    "gemini": ProviderSpec(
        name="gemini",
        modules=("google.genai",),
        env=(EnvVar("GEMINI_API_KEY", True, "Gemini API key per Outlines docs"),),
        notes="Sync wrapper only; Google client may also support other auth modes.",
    ),
    "mistral": ProviderSpec(
        name="mistral",
        modules=("mistralai",),
        env=(EnvVar("MISTRAL_API_KEY", True, "Mistral API key"),),
        notes="Use from_mistral(..., async_client=True) for async wrapper.",
    ),
    "ollama": ProviderSpec(
        name="ollama",
        modules=("ollama",),
        env=(EnvVar("OLLAMA_HOST", False, "Optional Ollama host/endpoint"),),
        notes="No default API key; service/model liveness is not checked.",
    ),
    "lmstudio": ProviderSpec(
        name="lmstudio",
        modules=("lmstudio",),
        env=(EnvVar("LMSTUDIO_HOST", False, "Optional app-defined LM Studio endpoint placeholder", True),),
        notes="LM Studio endpoint handling is SDK/app-specific; this placeholder is not an Outlines requirement.",
    ),
    "sglang": ProviderSpec(
        name="sglang",
        modules=("openai",),
        env=(
            EnvVar("SGLANG_BASE_URL", True, "SGLang OpenAI-compatible base URL placeholder", True),
            EnvVar("SGLANG_API_KEY", False, "Optional SGLang server token placeholder", True),
        ),
        notes="Uses the OpenAI SDK client but from_sglang for server-specific structured output fields.",
    ),
    "tgi": ProviderSpec(
        name="tgi",
        modules=("huggingface_hub",),
        env=(
            EnvVar("TGI_SERVER_URL", True, "TGI endpoint URL used by Outlines tests and examples"),
            EnvVar("HF_TOKEN", False, "Optional Hugging Face token for protected endpoints"),
        ),
        notes="Checks only client package and URL variable; no TGI server call is made.",
    ),
    "vllm": ProviderSpec(
        name="vllm",
        modules=("openai",),
        env=(
            EnvVar("VLLM_BASE_URL", True, "vLLM OpenAI-compatible base URL placeholder", True),
            EnvVar("VLLM_API_KEY", False, "Optional vLLM server token placeholder", True),
        ),
        notes="Uses from_vllm; structured output requires a compatible server version at live runtime.",
    ),
    "dottxt": ProviderSpec(
        name="dottxt",
        modules=("dottxt",),
        env=(
            EnvVar("DOTTXT_API_KEY", True, "Dottxt API key"),
            EnvVar("DOTTXT_MODEL", False, "Optional app-defined default Dottxt model id placeholder", True),
        ),
        notes="Dottxt requires a JSON-schema output_type and model id at runtime.",
    ),
}

ALIASES = {
    "azure": "azure-openai",
    "azure_openai": "azure-openai",
    "lm-studio": "lmstudio",
}


def module_available(module_name: str) -> bool:
    """Return whether a module can be found without importing provider clients."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def redact_env_status(var: EnvVar) -> dict[str, object]:
    value = os.environ.get(var.name)
    return {
        "name": var.name,
        "present": value is not None and value != "",
        "required": var.required,
        "purpose": var.purpose,
        "placeholder": var.placeholder,
        "value": "<set; redacted>" if value else "<unset>",
    }


def normalize_provider_names(names: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for raw in names:
        key = raw.strip().lower()
        if not key:
            continue
        key = ALIASES.get(key, key)
        if key == "all":
            return list(PROVIDERS)
        if key not in PROVIDERS:
            choices = ", ".join(sorted(PROVIDERS))
            raise SystemExit(f"Unknown provider {raw!r}. Choose from: {choices}, all")
        if key not in normalized:
            normalized.append(key)
    return normalized or list(PROVIDERS)


def inspect_provider(spec: ProviderSpec) -> dict[str, object]:
    modules = {module: module_available(module) for module in spec.modules}
    env = [redact_env_status(var) for var in spec.env]
    missing_required_env = [item["name"] for item in env if item["required"] and not item["present"]]
    missing_modules = [module for module, available in modules.items() if not available]
    return {
        "provider": spec.name,
        "modules": modules,
        "env": env,
        "ok_imports": not missing_modules,
        "ok_required_env": not missing_required_env,
        "missing_modules": missing_modules,
        "missing_required_env": missing_required_env,
        "notes": spec.notes,
    }


def print_text(results: list[dict[str, object]], *, summary: bool) -> None:
    for result in results:
        print(f"[{result['provider']}]")
        print("  modules:")
        for module, available in sorted(result["modules"].items()):  # type: ignore[index, union-attr]
            print(f"    - {module}: {'available' if available else 'missing'}")
        print("  environment variables / endpoint settings:")
        for item in result["env"]:  # type: ignore[index]
            required = "required" if item["required"] else "optional"
            placeholder = " placeholder" if item["placeholder"] else ""
            print(
                f"    - {item['name']}: {item['value']} "
                f"({required}{placeholder}; {item['purpose']})"
            )
        if not summary:
            print(f"  notes: {result['notes']}")
        print(
            "  status: "
            f"imports={'ok' if result['ok_imports'] else 'missing'}; "
            f"required_env={'ok' if result['ok_required_env'] else 'missing'}"
        )
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "No-network prerequisite checker for Outlines remote providers. "
            "Checks SDK module availability and whether named env vars are set; "
            "never calls services and never prints secret values."
        )
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["all"],
        help=(
            "Providers to check. Choices: all, "
            + ", ".join(sorted(PROVIDERS))
            + ". Aliases: azure, azure_openai, lm-studio."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON with secret values redacted.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Omit long notes in text output.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit non-zero if any selected provider has missing SDK modules or "
            "required env vars. Without --strict the script reports only."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    provider_names = normalize_provider_names(args.providers)
    results = [inspect_provider(PROVIDERS[name]) for name in provider_names]

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print_text(results, summary=args.summary)

    if args.strict and any(not (r["ok_imports"] and r["ok_required_env"]) for r in results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
