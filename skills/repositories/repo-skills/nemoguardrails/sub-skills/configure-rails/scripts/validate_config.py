#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

# Keep the validator local and quiet by default.
os.environ.setdefault("NEMO_GUARDRAILS_NO_USAGE_STATS", "1")
os.environ.setdefault("DO_NOT_TRACK", "1")


def _load_runtime():
    try:
        from nemoguardrails import LLMRails, RailsConfig
    except ImportError as exc:  # pragma: no cover - exercised manually
        raise ImportError(
            "Could not import `nemoguardrails` or one of its optional dependencies. "
            "Install the missing package or repair the environment, then rerun the validator."
        ) from exc

    return LLMRails, RailsConfig


def _format_counter(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counter.items()))


def _format_items(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    return ", ".join(values) if values else "none"


def _summarize_config(config) -> None:
    models = list(getattr(config, "models", []) or [])
    prompts = list(getattr(config, "prompts", []) or [])
    rails = getattr(config, "rails", None)
    flows = list(getattr(config, "flows", []) or [])

    model_types = Counter(getattr(model, "type", "<unknown>") for model in models)
    model_engines = Counter(getattr(model, "engine", "<unknown>") for model in models)
    prompt_tasks = [getattr(prompt, "task", "<unknown>") for prompt in prompts]

    print(f"colang_version: {config.colang_version}")
    print(f"models: total={len(models)} | by_type={_format_counter(model_types)} | by_engine={_format_counter(model_engines)}")
    print(f"colang_flows: total={len(flows)}")
    print("rail flows:")

    if rails is None:
        print("  input: none")
        print("  output: none")
        print("  retrieval: none")
        print("  dialog.single_call.enabled: none")
        print("  actions.instant_actions: none")
        print("  tool_input: none")
        print("  tool_output: none")
    else:
        print(f"  input: {_format_items(getattr(rails.input, 'flows', []))}")
        print(f"  output: {_format_items(getattr(rails.output, 'flows', []))}")
        print(f"  retrieval: {_format_items(getattr(rails.retrieval, 'flows', []))}")
        print(f"  dialog.single_call.enabled: {getattr(rails.dialog.single_call, 'enabled', None)}")
        print(f"  actions.instant_actions: {_format_items(getattr(rails.actions, 'instant_actions', []) or [])}")
        print(f"  tool_input: {_format_items(getattr(rails.tool_input, 'flows', []))}")
        print(f"  tool_output: {_format_items(getattr(rails.tool_output, 'flows', []))}")

    print(f"prompts: total={len(prompts)} | tasks={_format_items(prompt_tasks)}")


def _error_hint(message: str) -> str:
    lowered = message.lower()
    if "prompt template" in lowered:
        return "Check that the matching prompt task exists and that any $model or $variant suffix matches the enabled rail exactly."
    if "references model type" in lowered:
        return "Add the missing model under `models` or change the rail to reference an existing model type."
    if "streaming cannot apply" in lowered:
        return "Remove the rewriting rail from the streaming config, or set stream_first to false and context_size to 0."
    if "passthrough mode and the single call dialog" in lowered:
        return "Disable either passthrough mode or dialog single-call mode; they cannot be enabled together."
    if "does not exist" in lowered and "rail" in lowered:
        return "Check the flow name, Colang version, and whether the defining .co file was loaded."
    if "api key environment variable" in lowered:
        return "Set the referenced environment variable before loading the config, or remove api_key_env_var if you intentionally inline the key."
    return "Check YAML/Colang syntax, rail names, prompt names, model types, and optional dependency requirements."


def _load_config(config_path: Path):
    _, RailsConfig = _load_runtime()
    return RailsConfig.from_path(str(config_path))


def _instantiate(config):
    LLMRails, _ = _load_runtime()
    return LLMRails(config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Load a NeMo Guardrails config locally and print a concise summary.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a config directory or YAML file.",
    )
    parser.add_argument(
        "--instantiate",
        action="store_true",
        help="Instantiate LLMRails after loading the config, without generating a response.",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config).expanduser()
    display_path = config_path.resolve(strict=False)

    try:
        config = _load_config(config_path)
    except (ImportError, ValueError) as exc:
        print(f"config load failed: {exc}", file=sys.stderr)
        print(f"hint: {_error_hint(str(exc))}", file=sys.stderr)
        return 2

    print(f"config: {display_path}")
    _summarize_config(config)
    sys.stdout.flush()

    if args.instantiate:
        try:
            _instantiate(config)
        except (ImportError, ValueError) as exc:
            print(f"LLMRails instantiation failed: {exc}", file=sys.stderr)
            print(f"hint: {_error_hint(str(exc))}", file=sys.stderr)
            return 2
        print("LLMRails instantiation: success (no generation performed)")

    return 0


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())
