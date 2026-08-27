#!/usr/bin/env python3
"""Print concise PaperQA named Settings summaries without network calls."""

from __future__ import annotations

import argparse
import importlib.resources
import json
import sys
from collections.abc import Iterable
from typing import Any

ORDER = [
    "default",
    "fast",
    "high_quality",
    "debug",
    "clinical_trials",
    "search_only_clinical_trials",
    "contracrow",
    "wikicrow",
    "openreview",
    "tier1_limits",
    "tier2_limits",
    "tier3_limits",
    "tier4_limits",
    "tier5_limits",
]


def _import_paperqa():
    try:
        import paperqa.configs as configs
        from paperqa import Settings
    except Exception as exc:  # pragma: no cover - depends on runtime env
        print(f"ERROR: could not import paperqa Settings: {exc}", file=sys.stderr)
        sys.exit(2)
    return Settings, configs


def _bundled_names(configs: Any) -> list[str]:
    names = []
    try:
        for item in importlib.resources.files(configs).iterdir():
            if item.name.endswith(".json"):
                names.append(item.name.removesuffix(".json"))
    except Exception as exc:  # pragma: no cover - depends on package resources
        print(f"WARNING: could not enumerate bundled configs: {exc}", file=sys.stderr)
    ordered = [n for n in ORDER if n == "default" or n in names]
    extras = sorted(n for n in names if n not in ordered)
    return ordered + extras


def _rate_limit_summary(config: Any) -> Any:
    if not isinstance(config, dict) or "rate_limit" not in config:
        return None
    value = config["rate_limit"]
    if isinstance(value, dict):
        keys = sorted(str(k) for k in value)
        return {"count": len(keys), "models": keys[:8], "truncated": len(keys) > 8}
    return value


def _config_shape(config: Any) -> str:
    if config is None:
        return "default"
    if not isinstance(config, dict):
        return type(config).__name__
    parts: list[str] = []
    if "model_list" in config:
        model_list = config.get("model_list")
        parts.append(f"model_list[{len(model_list) if isinstance(model_list, list) else '?'}]")
    if "router_kwargs" in config:
        parts.append("router_kwargs")
    if "rate_limit" in config:
        parts.append("rate_limit")
    if not parts:
        parts.append("custom-dict")
    return "+".join(parts)


def _summarize(name: str, settings: Any) -> dict[str, Any]:
    return {
        "name": name,
        "llms": {
            "llm": settings.llm,
            "summary_llm": settings.summary_llm,
            "agent_llm": settings.agent.agent_llm,
            "temperature": settings.temperature,
        },
        "config_shapes": {
            "llm_config": _config_shape(settings.llm_config),
            "summary_llm_config": _config_shape(settings.summary_llm_config),
            "agent_llm_config": _config_shape(settings.agent.agent_llm_config),
            "embedding_config": _config_shape(settings.embedding_config),
        },
        "rate_limits": {
            "llm_config": _rate_limit_summary(settings.llm_config),
            "summary_llm_config": _rate_limit_summary(settings.summary_llm_config),
            "agent_llm_config": _rate_limit_summary(settings.agent.agent_llm_config),
            "embedding_config": _rate_limit_summary(settings.embedding_config),
        },
        "embedding": settings.embedding,
        "answer": {
            "evidence_k": settings.answer.evidence_k,
            "answer_max_sources": settings.answer.answer_max_sources,
            "max_concurrent_requests": settings.answer.max_concurrent_requests,
            "answer_length": settings.answer.answer_length,
            "evidence_summary_length": settings.answer.evidence_summary_length,
        },
        "parsing": {
            "use_doc_details": settings.parsing.use_doc_details,
            "defer_embedding": settings.parsing.defer_embedding,
            "multimodal": str(settings.parsing.multimodal),
            "reader_config": settings.parsing.reader_config,
        },
        "prompts": {"use_json": settings.prompts.use_json},
        "agent": {
            "agent_type": settings.agent.agent_type,
            "tool_names": sorted(settings.agent.tool_names) if isinstance(settings.agent.tool_names, set) else settings.agent.tool_names,
            "search_count": settings.agent.search_count,
            "rebuild_index": settings.agent.rebuild_index,
        },
    }


def _load(Settings: Any, name: str) -> Any:
    if name == "default":
        return Settings()
    return Settings.from_name(name)


def _print_table(rows: Iterable[dict[str, Any]]) -> None:
    for row in rows:
        llms = row["llms"]
        answer = row["answer"]
        agent = row["agent"]
        print(f"[{row['name']}]")
        print(
            "  llm={llm} summary_llm={summary_llm} agent_llm={agent_llm} temp={temperature}".format(
                **llms
            )
        )
        print(f"  embedding={row['embedding']}")
        print(
            "  answer: evidence_k={evidence_k} answer_max_sources={answer_max_sources} "
            "max_concurrent_requests={max_concurrent_requests}".format(**answer)
        )
        print(
            f"  agent: type={agent['agent_type']} tool_names={agent['tool_names']} "
            f"rebuild_index={agent['rebuild_index']}"
        )
        print(f"  config_shapes={row['config_shapes']}")
        active_limits = {k: v for k, v in row["rate_limits"].items() if v}
        if active_limits:
            print(f"  rate_limits={active_limits}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--names", nargs="+", help="Named configs to print; default is all bundled configs plus default.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable summary.")
    parser.add_argument("--list", action="store_true", help="Only list available bundled config names.")
    args = parser.parse_args(argv)

    Settings, configs = _import_paperqa()
    available = _bundled_names(configs)
    if args.list:
        print("\n".join(available))
        return 0

    names = args.names or available
    rows: list[dict[str, Any]] = []
    failed = False
    for name in names:
        try:
            rows.append(_summarize(name, _load(Settings, name)))
        except Exception as exc:
            failed = True
            rows.append({"name": name, "error": f"{type(exc).__name__}: {exc}"})

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True, default=str))
    else:
        errored = [r for r in rows if "error" in r]
        _print_table(r for r in rows if "error" not in r)
        for row in errored:
            print(f"[{row['name']}] ERROR: {row['error']}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
