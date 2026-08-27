#!/usr/bin/env python3
"""Validate PaperQA Settings JSON without calling LLMs, embeddings, or network services."""

from __future__ import annotations

import argparse
import importlib.resources
import importlib.util
import json
import os
import sys
import warnings
from collections.abc import Mapping
from pathlib import Path
from typing import Any

OPTIONAL_EXTRA_IMPORTS = {
    "local": ["sentence_transformers"],
    "qdrant": ["qdrant_client"],
    "office": ["unstructured"],
    "zotero": ["pyzotero"],
    "openreview": ["openreview"],
}


def _import_paperqa():
    try:
        import paperqa.configs as configs
        from paperqa import Settings
        from paperqa.settings import AgentSettings, ParsingSettings
    except Exception as exc:  # pragma: no cover - depends on runtime env
        print(f"ERROR: could not import paperqa Settings: {exc}", file=sys.stderr)
        sys.exit(2)
    return Settings, AgentSettings, ParsingSettings, configs


def _load_json_file(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    try:
        text = path.read_text()
    except OSError as exc:
        return None, [f"could not read file: {exc}"]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, [f"malformed JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"]
    if not isinstance(data, dict):
        errors.append("settings JSON must be an object at the top level")
        return None, errors
    return data, errors


def _load_named_config(name: str, configs: Any) -> tuple[dict[str, Any], list[str]]:
    if name == "default":
        return {}, []
    try:
        resource = importlib.resources.files(configs) / f"{name}.json"
        text = resource.read_text()
    except Exception as exc:
        return {}, [f"could not read bundled config {name!r}: {exc}"]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {}, [f"bundled config {name!r} has malformed JSON: {exc}"]
    if not isinstance(data, dict):
        return {}, [f"bundled config {name!r} is not a JSON object"]
    return data, []


def _model_provider_key(model: str) -> str | None:
    m = model.strip()
    if not m:
        return None
    low = m.lower()
    if low.startswith(("gpt-", "o1", "text-embedding-", "openai/")):
        return "OPENAI_API_KEY"
    if low.startswith("claude-") or low.startswith("anthropic/"):
        return "ANTHROPIC_API_KEY"
    if low.startswith("gemini/"):
        return "GEMINI_API_KEY"
    return None


def _local_embedding_extra(embedding: str) -> list[str]:
    e = embedding.strip()
    if e.startswith("hybrid-"):
        return _local_embedding_extra(e[len("hybrid-") :])
    if e.startswith("st-"):
        return ["local"]
    return []


def _has_nested(raw: Mapping[str, Any], dotted: str) -> bool:
    cur: Any = raw
    for part in dotted.split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return False
        cur = cur[part]
    return True


def _unknown_top_level(raw: Mapping[str, Any], Settings: Any) -> list[str]:
    allowed = set(Settings.model_fields)
    return sorted(k for k in raw if k not in allowed and not k.startswith("_"))


def _router_warnings(config: Any, label: str) -> list[str]:
    notes: list[str] = []
    if config is None:
        return notes
    if not isinstance(config, dict):
        notes.append(f"{label} is {type(config).__name__}, expected a dict if supplied")
        return notes
    if "model_list" in config:
        model_list = config["model_list"]
        if not isinstance(model_list, list) or not model_list:
            notes.append(f"{label}.model_list should be a non-empty list")
        else:
            for i, item in enumerate(model_list):
                if not isinstance(item, dict):
                    notes.append(f"{label}.model_list[{i}] should be an object")
                    continue
                if "model_name" not in item:
                    notes.append(f"{label}.model_list[{i}] is missing model_name")
                params = item.get("litellm_params")
                if not isinstance(params, dict) or "model" not in params:
                    notes.append(f"{label}.model_list[{i}].litellm_params.model is missing")
    elif "litellm_params" in config or "model_name" in config:
        notes.append(f"{label} looks like a single-model config; wrap custom routes in model_list for LiteLLM Router use")
    elif "rate_limit" in config:
        notes.append(f"{label} contains rate_limit only; that is useful for throttling but not for custom provider routing")
    else:
        notes.append(f"{label} lacks model_list; verify the shape before live provider calls")
    return notes


def _check_optional_extra(extra: str) -> tuple[bool, list[str]]:
    modules = OPTIONAL_EXTRA_IMPORTS[extra]
    missing = [m for m in modules if importlib.util.find_spec(m) is None]
    return not missing, missing


def _sanitize_summary(settings: Any) -> dict[str, Any]:
    return {
        "llm": settings.llm,
        "summary_llm": settings.summary_llm,
        "agent_llm": settings.agent.agent_llm,
        "embedding": settings.embedding,
        "temperature": settings.temperature,
        "answer": {
            "evidence_k": settings.answer.evidence_k,
            "answer_max_sources": settings.answer.answer_max_sources,
            "max_concurrent_requests": settings.answer.max_concurrent_requests,
        },
        "parsing": {
            "use_doc_details": settings.parsing.use_doc_details,
            "defer_embedding": settings.parsing.defer_embedding,
            "multimodal": str(settings.parsing.multimodal),
            "reader_config": settings.parsing.reader_config,
        },
        "agent": {
            "agent_type": settings.agent.agent_type,
            "tool_names": sorted(settings.agent.tool_names) if isinstance(settings.agent.tool_names, set) else settings.agent.tool_names,
        },
    }


def _analyze(raw: dict[str, Any], settings: Any, Settings: Any, AgentSettings: Any, ParsingSettings: Any, requested_extras: list[str]) -> tuple[list[str], list[str]]:
    warnings_out: list[str] = []
    info: list[str] = []

    unknown = _unknown_top_level(raw, Settings)
    if unknown:
        warnings_out.append(
            "unknown top-level keys will be ignored by Settings: " + ", ".join(unknown)
        )

    roles = {
        "llm": settings.llm,
        "summary_llm": settings.summary_llm,
        "agent.agent_llm": settings.agent.agent_llm,
        "embedding": settings.embedding,
    }
    if hasattr(settings.parsing, "enrichment_llm"):
        roles["parsing.enrichment_llm"] = settings.parsing.enrichment_llm

    for label, model in roles.items():
        if not isinstance(model, str):
            continue
        key = _model_provider_key(model)
        if key and not os.environ.get(key):
            warnings_out.append(f"{label}={model!r} usually requires {key}, which is not set in this process")

    if _has_nested(raw, "llm"):
        if not _has_nested(raw, "summary_llm"):
            warnings_out.append("llm is set but summary_llm is not set; summary_llm may still use the default provider")
        if not _has_nested(raw, "agent.agent_llm"):
            warnings_out.append("llm is set but agent.agent_llm is not set; the agent may still use the default provider")
        if not _has_nested(raw, "embedding"):
            warnings_out.append("llm is set but embedding is not set; embeddings may still use the default provider")

    for label, config in [
        ("llm_config", settings.llm_config),
        ("summary_llm_config", settings.summary_llm_config),
        ("embedding_config", settings.embedding_config),
        ("agent.agent_llm_config", settings.agent.agent_llm_config),
    ]:
        warnings_out.extend(_router_warnings(config, label))
    if hasattr(settings.parsing, "enrichment_llm_config"):
        warnings_out.extend(_router_warnings(settings.parsing.enrichment_llm_config, "parsing.enrichment_llm_config"))

    for label, model in roles.items():
        if isinstance(model, str) and model.startswith(("o1", "gpt-5")) and settings.temperature != 1:
            warnings_out.append(f"{label} is a reasoning model but temperature is {settings.temperature}; set temperature=1")

    extras = set(requested_extras)
    extras.update(_local_embedding_extra(settings.embedding))
    for extra in sorted(extras):
        ok, missing = _check_optional_extra(extra)
        if ok:
            info.append(f"optional extra check {extra}: import probes passed")
        else:
            warnings_out.append(f"optional extra {extra} appears missing; could not import {', '.join(missing)}")

    # Check class availability without instantiating optional service clients.
    if importlib.util.find_spec("qdrant_client") is None and "qdrant" in requested_extras:
        warnings_out.append("QdrantVectorStore requires qdrant-client; not instantiating it during validation")

    return warnings_out, info


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Settings JSON files to validate.")
    parser.add_argument("--named", action="append", default=[], help="Also validate a bundled named config by name.")
    parser.add_argument("--check-extra", choices=sorted(OPTIONAL_EXTRA_IMPORTS), action="append", default=[], help="Probe an optional dependency import without network calls.")
    parser.add_argument("--print-normalized", action="store_true", help="Print a sanitized summary of validated settings.")
    parser.add_argument("--strict-warnings", action="store_true", help="Return non-zero when configuration warnings are emitted.")
    args = parser.parse_args(argv)

    if not args.paths and not args.named:
        parser.error("provide at least one JSON path or --named CONFIG")

    Settings, AgentSettings, ParsingSettings, configs = _import_paperqa()
    overall_errors = 0
    overall_warnings = 0

    items: list[tuple[str, dict[str, Any] | None, list[str]]] = []
    for path in args.paths:
        data, errors = _load_json_file(path)
        items.append((str(path), data, errors))
    for name in args.named:
        data, errors = _load_named_config(name, configs)
        items.append((f"named:{name}", data, errors))

    for label, raw, load_errors in items:
        print(f"== {label} ==")
        if load_errors or raw is None:
            overall_errors += 1
            for err in load_errors:
                print(f"ERROR: {err}")
            continue

        caught: list[warnings.WarningMessage]
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                settings = Settings.model_validate(raw)
        except Exception as exc:
            overall_errors += 1
            print(f"ERROR: Settings validation failed: {type(exc).__name__}: {exc}")
            continue

        config_warnings, info = _analyze(raw, settings, Settings, AgentSettings, ParsingSettings, args.check_extra)
        warning_texts = [str(w.message) for w in caught] + config_warnings
        overall_warnings += len(warning_texts)
        print("OK: Settings validation passed")
        for line in info:
            print(f"INFO: {line}")
        for line in warning_texts:
            print(f"WARNING: {line}")
        if args.print_normalized:
            print(json.dumps(_sanitize_summary(settings), indent=2, sort_keys=True, default=str))
        print()

    if overall_errors:
        return 1
    if args.strict_warnings and overall_warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
