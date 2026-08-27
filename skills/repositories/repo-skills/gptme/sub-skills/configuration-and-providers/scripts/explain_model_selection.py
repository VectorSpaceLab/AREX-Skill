#!/usr/bin/env python3
"""Explain gptme model-selection priority without API calls.

The helper accepts explicit CLI/chat/global/env inputs plus optional TOML files.
It does not import gptme and never prints secret values.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    try:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore[assignment]

PROVIDER_API_KEYS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "requesty": "REQUESTY_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "xai": "XAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "azure": "AZURE_OPENAI_API_KEY",
}

AUTO_DETECT_ORDER = [
    "openai",
    "anthropic",
    "openrouter",
    "requesty",
    "gemini",
    "groq",
    "xai",
    "deepseek",
    "moonshot",
    "azure",
]

RECOMMENDED_MODELS: dict[str, str] = {
    "openai": "gpt-5",
    "openai-subscription": "gpt-5.6-sol",
    "openrouter": "deepseek/deepseek-v4-pro",
    "gemini": "gemini-2.5-pro",
    "anthropic": "claude-sonnet-4-6",
    "xai": "grok-4",
    "gptme": "claude-sonnet-4-6",
    "deepseek": "deepseek-chat",
    "groq": "llama-3.3-70b-versatile",
}

SUMMARY_MODELS: dict[str, str | None] = {
    "openai": "gpt-5-mini",
    "openrouter": "deepseek/deepseek-v4-flash",
    "gemini": "gemini-2.5-flash",
    "anthropic": "claude-haiku-4-5",
    "deepseek": "deepseek-chat",
    "xai": "grok-4-1-fast",
    "local": None,
}

BUILTIN_PROVIDERS = set(PROVIDER_API_KEYS) | {
    "local",
    "gptme",
    "openai-subscription",
    "grok-subscription",
    "mock",
}


@dataclass
class Candidate:
    priority: int
    name: str
    value: str | None
    source: str
    selected: bool = False
    note: str | None = None


@dataclass
class Explanation:
    selected_model: str | None
    selected_source: str | None
    provider: str | None
    resolved_model_for_provider_default: str | None
    summary_model: str | None
    candidates: list[Candidate]
    warnings: list[str]
    notes: list[str]


def parse_env_assignment(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("expected KEY=VALUE")
    key, value = raw.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError("environment key must not be empty")
    return key, value


def load_toml(path: str | None, warnings: list[str]) -> dict[str, Any]:
    if not path:
        return {}
    resolved = Path(path).expanduser()
    if not resolved.exists():
        warnings.append(f"TOML file is missing: {resolved}")
        return {}
    if tomllib is None:
        warnings.append("No TOML parser available; use Python 3.11+ or install tomli.")
        return {}
    try:
        data = tomllib.loads(resolved.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append(f"Could not parse {resolved}: {exc}")
        return {}
    return data if isinstance(data, dict) else {}


def section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def first_non_empty(*values: tuple[str | None, str]) -> tuple[str | None, str | None]:
    for value, source in values:
        if value:
            return value, source
    return None, None


def get_config_model_values(args: argparse.Namespace, warnings: list[str]) -> dict[str, tuple[str | None, str]]:
    global_config = load_toml(args.global_config, warnings)
    global_local = load_toml(args.global_local, warnings)
    project_config = load_toml(args.project_config, warnings)
    project_local = load_toml(args.project_local, warnings)
    chat_config = load_toml(args.chat_config, warnings)

    # Only the values needed for selection are merged here. Local override wins.
    global_models_default = first_non_empty(
        (args.models_default, "--models-default"),
        (str(section(global_local, "models").get("default")) if section(global_local, "models").get("default") else None, "global local [models].default"),
        (str(section(global_config, "models").get("default")) if section(global_config, "models").get("default") else None, "global [models].default"),
    )

    chat_model = first_non_empty(
        (args.chat_model, "--chat-model"),
        (str(section(chat_config, "chat").get("model")) if section(chat_config, "chat").get("model") else None, "chat [chat].model"),
    )

    env_model = first_non_empty(
        (args.model_env, "--model-env"),
        (args.env_map.get("GPTME_MODEL"), "supplied env:GPTME_MODEL"),
        (args.env_map.get("MODEL"), "supplied env:MODEL"),
        (str(section(chat_config, "env").get("MODEL")) if section(chat_config, "env").get("MODEL") else None, "chat [env].MODEL"),
        (str(section(project_local, "env").get("MODEL")) if section(project_local, "env").get("MODEL") else None, "project local [env].MODEL"),
        (str(section(project_config, "env").get("MODEL")) if section(project_config, "env").get("MODEL") else None, "project [env].MODEL"),
        (str(section(global_local, "env").get("MODEL")) if section(global_local, "env").get("MODEL") else None, "global local [env].MODEL"),
        (str(section(global_config, "env").get("MODEL")) if section(global_config, "env").get("MODEL") else None, "global [env].MODEL"),
    )

    return {
        "chat_model": chat_model,
        "models_default": global_models_default,
        "env_model": env_model,
    }


def provider_for_model(model: str | None, custom_defaults: dict[str, str]) -> str | None:
    if not model:
        return None
    if "/" in model:
        return model.split("/", 1)[0]
    if model in BUILTIN_PROVIDERS or model in custom_defaults:
        return model
    return None


def expanded_model(model: str | None, custom_defaults: dict[str, str]) -> str | None:
    if not model:
        return None
    provider = provider_for_model(model, custom_defaults)
    if provider is None:
        return model
    if "/" in model:
        return model
    if provider in custom_defaults:
        return f"{provider}/{custom_defaults[provider]}"
    rec = RECOMMENDED_MODELS.get(provider)
    return f"{provider}/{rec}" if rec else None


def explain(args: argparse.Namespace) -> Explanation:
    warnings: list[str] = []
    notes: list[str] = []
    config_values = get_config_model_values(args, warnings)

    custom_defaults: dict[str, str] = {}
    for item in args.custom_provider:
        name, default = parse_env_assignment(item)
        custom_defaults[name] = default

    candidates: list[Candidate] = []
    candidates.append(Candidate(1, "CLI --model", args.cli_model, "--cli-model"))
    chat_model, chat_source = config_values["chat_model"]
    candidates.append(Candidate(2, "per-chat model", chat_model, chat_source or "not supplied"))
    models_default, models_source = config_values["models_default"]
    candidates.append(Candidate(3, "[models].default", models_default, models_source or "not supplied"))
    env_model, env_source = config_values["env_model"]
    candidates.append(Candidate(4, "MODEL", env_model, env_source or "not supplied"))

    auto_model: str | None = None
    auto_source = "not available"
    configured_key_envs = set(args.api_key_env)
    for provider in AUTO_DETECT_ORDER:
        env_var = PROVIDER_API_KEYS[provider]
        if env_var in configured_key_envs or args.env_map.get(env_var) or args.env_map.get(f"GPTME_{env_var}"):
            auto_model = provider
            auto_source = f"auto-detected from {env_var}"
            break
    if auto_model is None and args.credential_provider:
        provider = sorted(args.credential_provider)[0]
        auto_model = provider
        auto_source = "auto-detected from credential store"
    if auto_model is None and args.oauth_provider:
        provider = args.oauth_provider[0]
        auto_model = provider
        auto_source = "auto-detected from OAuth token"
    candidates.append(Candidate(5, "auto-detect credentials", auto_model, auto_source))

    selected: Candidate | None = None
    for candidate in candidates:
        if candidate.value:
            selected = candidate
            candidate.selected = True
            break

    if models_default and env_model and models_default != env_model:
        warnings.append("[models].default and MODEL differ; [models].default has higher priority than MODEL.")
    if args.cli_model and chat_model and args.cli_model != chat_model:
        notes.append("CLI --model overrides the saved chat model for this run.")
    if chat_model and models_default and chat_model != models_default and not args.cli_model:
        notes.append("The saved per-chat model overrides [models].default when resuming this chat.")

    selected_model = selected.value if selected else None
    selected_source = selected.source if selected else None
    provider = provider_for_model(selected_model, custom_defaults)
    resolved = expanded_model(selected_model, custom_defaults)

    summary_model: str | None = None
    if provider:
        if provider in SUMMARY_MODELS:
            summary_name = SUMMARY_MODELS[provider]
            summary_model = f"{provider}/{summary_name}" if summary_name else resolved
            if provider == "local":
                notes.append("local provider has no separate summary model; gptme uses the selected local model for summaries.")
        elif provider in custom_defaults:
            summary_model = resolved
            notes.append("custom providers have no built-in summary model mapping in this static helper.")

    if selected_model and provider is None:
        warnings.append(f"Selected value {selected_model!r} has no recognized provider prefix in this static helper.")
    if provider == "local":
        has_base = any(
            key in args.env_map for key in ("OPENAI_BASE_URL", "GPTME_OPENAI_BASE_URL", "OPENAI_API_BASE", "GPTME_OPENAI_API_BASE")
        )
        if not has_base:
            warnings.append("local/... selected but no supplied OPENAI_BASE_URL or OPENAI_API_BASE was provided.")
    if provider == "azure" and not resolved:
        warnings.append("azure has no universal recommended model; provide a full azure/<deployment-or-model> value.")
    if provider in PROVIDER_API_KEYS:
        env_var = PROVIDER_API_KEYS[provider]
        if env_var not in configured_key_envs and env_var not in args.env_map and f"GPTME_{env_var}" not in args.env_map and provider not in args.credential_provider:
            warnings.append(f"Selected provider {provider!r} has no supplied {env_var} or credential-store source in this dry run.")

    if selected is None:
        warnings.append("No supplied source selected a model; interactive setup would be needed in an interactive gptme run.")

    return Explanation(
        selected_model=selected_model,
        selected_source=selected_source,
        provider=provider,
        resolved_model_for_provider_default=resolved,
        summary_model=summary_model,
        candidates=candidates,
        warnings=warnings,
        notes=notes,
    )


def print_human(explanation: Explanation) -> None:
    print("gptme model-selection explanation")
    print("=" * 34)
    print()
    print("Priority chain:")
    for candidate in explanation.candidates:
        marker = "=>" if candidate.selected else "  "
        value = candidate.value if candidate.value else "<not supplied>"
        print(f"{marker} {candidate.priority}. {candidate.name}: {value} ({candidate.source})")
    print()
    if explanation.selected_model:
        print("Selected:")
        print(f"- request: {explanation.selected_model}")
        print(f"- source: {explanation.selected_source}")
        print(f"- provider: {explanation.provider or 'unknown'}")
        if explanation.resolved_model_for_provider_default and explanation.resolved_model_for_provider_default != explanation.selected_model:
            print(f"- provider-default expansion: {explanation.resolved_model_for_provider_default}")
        if explanation.summary_model:
            print(f"- summary-model expectation: {explanation.summary_model}")
    else:
        print("Selected: <none>")
    if explanation.warnings:
        print()
        print("Warnings:")
        for warning in explanation.warnings:
            print(f"- {warning}")
    if explanation.notes:
        print()
        print("Notes:")
        for note in explanation.notes:
            print(f"- {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Explain gptme's model-selection priority from supplied CLI, chat, "
            "global config, MODEL env, and auto-detect inputs. No API calls."
        )
    )
    parser.add_argument("--cli-model", help="Model supplied by --model/-m for this run.")
    parser.add_argument("--chat-model", help="Model saved in the current chat config.")
    parser.add_argument("--models-default", help="Global [models].default value.")
    parser.add_argument("--model-env", help="MODEL/GPTME_MODEL value to include in the dry run.")
    parser.add_argument("--global-config", help="Optional global config.toml to read.")
    parser.add_argument("--global-local", help="Optional config.local.toml to read.")
    parser.add_argument("--project-config", help="Optional project gptme.toml to read for [env].MODEL.")
    parser.add_argument("--project-local", help="Optional project gptme.local.toml to read for [env].MODEL.")
    parser.add_argument("--chat-config", help="Optional chat config.toml to read for [chat].model and [env].MODEL.")
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Supply an env value for dry-run resolution; may be repeated. Secret-like values are not printed.",
    )
    parser.add_argument(
        "--api-key-env",
        action="append",
        default=[],
        metavar="ENVVAR",
        help="Mark an API-key env var as configured for auto-detection, without supplying its value.",
    )
    parser.add_argument(
        "--credential-provider",
        action="append",
        default=[],
        metavar="PROVIDER",
        help="Mark a provider as present in credentials.toml for auto-detection.",
    )
    parser.add_argument(
        "--oauth-provider",
        action="append",
        default=[],
        choices=["openai-subscription", "grok-subscription", "gptme"],
        help="Mark an OAuth/token provider as available for auto-detection.",
    )
    parser.add_argument(
        "--custom-provider",
        action="append",
        default=[],
        metavar="NAME=DEFAULT_MODEL",
        help="Declare a custom provider default for dry-run expansion; may be repeated.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON explanation.")
    args = parser.parse_args(argv)

    try:
        args.env_map = dict(parse_env_assignment(item) for item in args.env)
        for item in args.custom_provider:
            parse_env_assignment(item)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    explanation = explain(args)
    if args.json:
        payload = asdict(explanation)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(explanation)
    return 0 if explanation.selected_model else 1


if __name__ == "__main__":
    raise SystemExit(main())
