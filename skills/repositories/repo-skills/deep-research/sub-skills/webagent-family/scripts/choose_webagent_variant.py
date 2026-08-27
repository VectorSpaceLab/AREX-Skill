#!/usr/bin/env python3
"""Choose DeepResearch/WebAgent/Agent family routes from task signals.

This stdlib-only helper is safe to run from the generated skill tree. It does
not import the source repository, read local configuration, or require network
access.
"""

from __future__ import annotations

import argparse
import json
import re
import textwrap
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Set, Tuple


SIBLING_REACT = "../react-inference/"
SIBLING_EVAL = "../benchmark-evaluation/"


@dataclass(frozen=True)
class Route:
    name: str
    tags: Set[str]
    summary: str
    prerequisites: Tuple[str, ...]
    blockers: Tuple[str, ...]
    status: str
    sibling: str = ""
    avoid: str = ""


ROUTES: Sequence[Route] = (
    Route(
        "DeepResearch root ReAct",
        {"react", "inference", "root", "openrouter", "dataset", "tools", "web_search"},
        "Tongyi DeepResearch 30B-A3B ReAct inference and hosted/local API adaptation.",
        ("Python 3.10 recommended", "root inference config", "JSON/JSONL questions", "web/search/page/file tool services"),
        ("model weights or hosted endpoint", "API credentials", "local run assumes eight vLLM ports/GPUs"),
        "Reroute for detailed configuration.",
        SIBLING_REACT,
        "Do not use this family router for exact .env/tool/data instructions.",
    ),
    Route(
        "WebDancer",
        {"react", "inference", "training", "sft", "rl", "trajectory", "web_search"},
        "ReAct-based autonomous information-seeking model plus four-stage training paradigm.",
        ("Python 3.12", "sglang[all]", "qwen-agent", "WebDancer model", "Search/Visit keys"),
        ("GPU/model serving", "Google/Serper, Jina, Dashscope credentials", "training uses external LLaMA-Factory/verl"),
        "Partially runnable demo/deploy with prerequisites.",
    ),
    Route(
        "WebSailor",
        {"react", "inference", "complex_browse", "training", "sft", "rl", "dupo", "browsecomp", "web_search"},
        "Post-training method for high-uncertainty complex web navigation and information seeking.",
        ("Python 3.11", "sglang[all]", "qwen-agent", "WebSailor weights", "summary model", "official datasets"),
        ("GPU/model serving", "Google/Serper and Jina keys", "some large-model/trajectory assets may be external"),
        "Partially runnable evaluation/inference with heavyweight prerequisites.",
    ),
    Route(
        "WebSailor-V2",
        {"training", "sft", "rl", "synthetic_data", "dupo", "dual_environment", "complex_browse"},
        "Second-generation synthetic-data/SFT/RL methodology with dual-environment RL.",
        ("paper/model evidence", "SailorFog-QA-2 concept", "Qwen3-30B-A3B backbone note"),
        ("no local runnable implementation inspected", "data/checkpoints may be external"),
        "Method note in this checkout.",
    ),
    Route(
        "WebShaper",
        {"synthetic_data", "data", "formalization", "training", "web_search", "is"},
        "Formalization-driven information-seeking QA/data synthesis.",
        ("local 500-example JSONL data", "fields: id/question/formalization/answer/urls"),
        ("full training pipeline not present", "not an inference-serving route"),
        "Data/reference available.",
    ),
    Route(
        "WebWatcher",
        {"multimodal", "visual", "image", "vqa", "web_search", "benchmark", "browsecomp_vl"},
        "Vision-language deep research with image search, text search, visit, OCR/code-style tooling.",
        ("trained VLM", "summary model", "image folders", "vLLM", "image/text search and Jina keys"),
        ("large image archives", "optional OSS credentials", "vendored qwen-agent fork", "GPU split for model and summary service"),
        "Partially runnable; multimodal route with major data/model blockers.",
    ),
    Route(
        "WebResearcher",
        {"report", "iterative", "summarization", "tts", "fusion", "long_horizon"},
        "Iterative deep-research paradigm using Think/Report/Action rounds and last-k-fusion.",
        ("method description", "report-memory design", "RFT/RLVR and TTS concepts"),
        ("no runnable local code inspected", "demos described as pending"),
        "Conceptual route.",
    ),
    Route(
        "WebResummer / ReSum",
        {"summarization", "context", "react", "inference", "rl", "grpo", "long_horizon", "resume"},
        "Restartable ReAct exploration through periodic conversation compression and ReSumTool summaries.",
        ("sglang[all]", "qwen-agent", "inference model", "visit-summary model", "ReSum tool", "datasets"),
        ("ReSumTool release may be pending", "multi-vLLM setup", "Search/Jina/Dashscope credentials"),
        "Partially runnable when summary-tool/model endpoints exist.",
    ),
    Route(
        "WebWeaver",
        {"report", "outline", "writing", "citations", "open_ended", "planner", "writer", "deep_research"},
        "Planner/writer framework for open-ended deep reports with dynamic outlines and memory-grounded synthesis.",
        ("Python 3.12", "vLLM 0.10.2", "modelscope", "summary model", "planner/writer API", "Serper/ScraperAPI/Dashscope"),
        ("README states at least 4x80G GPUs for summary model", "long-context tool-calling quality", "service credentials"),
        "Most actionable report-writing route, but heavyweight.",
    ),
    Route(
        "WebWalker",
        {"web_traversal", "rag", "benchmark", "webwalkerqa", "crawl4ai", "evaluation"},
        "Web traversal benchmark, WebWalkerQA, RAG baseline, and Streamlit demo.",
        ("Python 3.10", "crawl4ai setup/doctor", "qwen-agent", "provider API keys", "WebWalkerQA data"),
        ("provider and judge credentials", "dataset acquisition", "crawl4ai/browser setup"),
        "Runnable for RAG/demo with services; route metrics to benchmark sibling.",
        SIBLING_EVAL,
    ),
    Route(
        "WebLeaper",
        {"efficient", "entity", "is", "training", "rl", "grpo", "web_search", "wide_search"},
        "Efficient entity-intensive information seeking with ISR/ISE and Basic/Union/Reverse-Union tasks.",
        ("method description", "entity-intensive task design", "Qwen3-30B-A3B-Thinking backbone note"),
        ("no runnable local pipeline inspected", "training data/model details may be external"),
        "Method reference.",
    ),
    Route(
        "AgentFold",
        {"summarization", "context", "compression", "long_horizon", "react", "inference"},
        "Proactive context-management agent that compresses previous steps while running Search/Visit rollouts.",
        ("OpenAI-compatible local endpoints", "transformers tokenizer", "Search/Visit tools", "dataset JSONL"),
        ("hard-coded placeholders", "multiple vLLM endpoints", "model/tokenizer paths", "tool credentials"),
        "Experimental runnable code; inspect before execution.",
    ),
    Route(
        "ParallelMuse",
        {"tts", "convergence", "aggregation", "parallel", "fusion", "rollouts", "test_time_scaling"},
        "Parallel rollout thinking plus report-based convergence/answer integration.",
        ("rollout JSONL", "AsyncOpenAI endpoint", "high context model", "vLLM TP4 helper"),
        ("TODO placeholders", "rough source edges", "requires multiple completed rollouts"),
        "Experimental pattern for aggregation; route metrics to benchmark sibling.",
        SIBLING_EVAL,
    ),
    Route(
        "NestBrowse",
        {"nested", "browser", "click", "fill", "mcp", "web_traversal", "long_horizon"},
        "Nested browser-use learning with Search, Visit, Click, and Fill tools through a browser MCP server.",
        ("browser MCP server URL", "local model endpoint", "tokenizer path", "benchmark JSONL", "128K context"),
        ("external browser service", "model/tokenizer placeholders", "data/results setup"),
        "Experimental route for browser-use tasks.",
    ),
    Route(
        "AgentFounder",
        {"continual_pretraining", "cpt", "training", "scaling", "data", "open_world_memory"},
        "Agentic continual pretraining with 32K/128K contexts and planning/reasoning/decision action synthesis.",
        ("method description", "AgentFounder-30B model/result notes"),
        ("no full local training code inspected", "large-scale data/compute required"),
        "Method reference.",
    ),
    Route(
        "AgentScaler",
        {"environment_scaling", "function_calling", "training", "simulated_environment", "agentic_intelligence"},
        "Environment scaling for general function-calling agents using simulated heterogeneous scenarios.",
        ("method description", "tau-bench/tau2-Bench/ACEBench context"),
        ("no full local environment-generation code inspected", "not a web-search inference route"),
        "Method reference.",
    ),
)

SIGNAL_PATTERNS: Dict[str, Sequence[str]] = {
    "react": (r"\breact\b", r"search/visit", r"tool[- ]?use", r"rollout", r"openrouter", r"\.env", r"vllm", r"inference"),
    "inference": (r"infer", r"serve", r"demo", r"run", r"endpoint"),
    "training": (r"train", r"post[- ]?train", r"fine[- ]?tun", r"sft", r"rl\b", r"rft", r"grpo", r"dupo", r"dapo", r"rlvr"),
    "synthetic_data": (r"synthetic", r"data synthesis", r"qa generation", r"formalization", r"sailorfog"),
    "multimodal": (r"multimodal", r"vision", r"visual", r"image", r"vqa", r"ocr", r"browsecomp[-_ ]?vl", r"mmsearch", r"livevqa"),
    "report": (r"report", r"write", r"citation", r"outline", r"open[- ]ended", r"deep report", r"planner", r"writer"),
    "summarization": (r"summari[sz]", r"context", r"compress", r"restart", r"resum", r"memory", r"unlimited exploration"),
    "efficient": (r"efficient", r"entity", r"isr", r"ise", r"wide ?search", r"reverse[- ]?union", r"union"),
    "web_traversal": (r"webwalker", r"traversal", r"crawl4ai", r"rag", r"webwalkerqa"),
    "benchmark": (r"benchmark", r"evaluat", r"judge", r"metric", r"pass@", r"hle", r"browsecomp", r"gaia", r"xbench"),
    "tts": (r"test[- ]?time", r"tts", r"fusion", r"converge", r"aggregate", r"parallel", r"multiple rollouts", r"last[- ]?k"),
    "nested": (r"nested", r"browser", r"click", r"fill", r"mcp"),
    "continual_pretraining": (r"continual", r"cpt", r"pretrain", r"128k", r"32k", r"open[- ]?world memory", r"agentfounder"),
    "environment_scaling": (r"environment scaling", r"simulated environment", r"function[- ]?calling", r"tau[- ]?bench", r"acebench", r"agentscaler"),
}

FLAG_TO_SIGNAL = {
    "react": "react",
    "post_training": "training",
    "data_synthesis": "synthetic_data",
    "multimodal": "multimodal",
    "report_writing": "report",
    "summarization": "summarization",
    "efficient_is": "efficient",
    "web_traversal_rag": "web_traversal",
    "benchmark": "benchmark",
    "test_time_scaling": "tts",
    "nested_browser": "nested",
    "continual_pretraining": "continual_pretraining",
    "environment_scaling": "environment_scaling",
}


def detect_signals(text: str, enabled_flags: Iterable[str]) -> Set[str]:
    lowered = text.lower()
    signals: Set[str] = set()
    for signal, patterns in SIGNAL_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            signals.add(signal)
    for flag in enabled_flags:
        signal = FLAG_TO_SIGNAL.get(flag)
        if signal:
            signals.add(signal)
    # Useful expansions.
    if "benchmark" in signals and "web_traversal" in signals:
        signals.add("evaluation")
    if "report" in signals:
        signals.add("deep_research")
    if "training" in signals:
        signals.add("data")
    return signals


def rank_routes(signals: Set[str]) -> List[Tuple[int, Route, List[str]]]:
    ranked: List[Tuple[int, Route, List[str]]] = []
    for route in ROUTES:
        matched = sorted(route.tags.intersection(signals))
        score = len(matched)
        # Make exact high-value singleton routes win.
        if route.name == "WebWatcher" and "multimodal" in signals:
            score += 3
        if route.name == "WebWeaver" and "report" in signals:
            score += 3
        if route.name == "NestBrowse" and "nested" in signals:
            score += 3
        if route.name == "ParallelMuse" and "tts" in signals:
            score += 3
        if route.name == "WebWalker" and "web_traversal" in signals:
            score += 3
        if route.name == "AgentFounder" and "continual_pretraining" in signals:
            score += 3
        if route.name == "AgentScaler" and "environment_scaling" in signals:
            score += 3
        if route.name == "DeepResearch root ReAct" and "react" in signals and "root" in signals:
            score += 2
        if score > 0:
            ranked.append((score, route, matched))
    ranked.sort(key=lambda item: (-item[0], item[1].name.lower()))
    return ranked


def bullet(items: Sequence[str]) -> str:
    return "; ".join(items) if items else "none"


def as_json(signals: Set[str], ranked: Sequence[Tuple[int, Route, List[str]]], limit: int) -> str:
    chosen = ranked if limit <= 0 else ranked[:limit]
    data = {
        "signals": sorted(signals),
        "routes": [
            {
                "name": route.name,
                "score": score,
                "matched_signals": matched,
                "summary": route.summary,
                "status": route.status,
                "prerequisites": list(route.prerequisites),
                "blockers": list(route.blockers),
                "sibling_sub_skill": route.sibling or None,
                "avoid": route.avoid or None,
            }
            for score, route, matched in chosen
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def as_markdown(signals: Set[str], ranked: Sequence[Tuple[int, Route, List[str]]], limit: int) -> str:
    if not signals:
        signals_text = "No strong signals detected; start from family-map.md and ask the user which deliverable they need."
    else:
        signals_text = ", ".join(sorted(signals))
    chosen = ranked if limit <= 0 else ranked[:limit]
    lines = [
        "# WebAgent Family Route Suggestions",
        "",
        f"Detected signals: {signals_text}",
        "",
    ]
    if not chosen:
        lines.extend([
            "No route scored above zero.",
            "Try adding flags such as --react, --multimodal, --report-writing, --test-time-scaling, or --nested-browser.",
        ])
        return "\n".join(lines)

    for index, (score, route, matched) in enumerate(chosen, 1):
        lines.extend([
            f"## {index}. {route.name} (score {score})",
            f"- Why: {route.summary}",
            f"- Matched signals: {', '.join(matched) if matched else 'flag/priority match'}",
            f"- Status: {route.status}",
            f"- Prerequisites: {bullet(route.prerequisites)}",
            f"- Blockers: {bullet(route.blockers)}",
        ])
        if route.sibling:
            lines.append(f"- Sibling sub-skill: {route.sibling}")
        if route.avoid:
            lines.append(f"- Avoid when: {route.avoid}")
        lines.append("")

    lines.extend([
        "Next steps:",
        "1. Read references/family-map.md for capability boundaries.",
        "2. Read references/family-workflows.md before recommending commands, dependencies, GPUs, or credentials.",
        "3. Use references/troubleshooting.md for missing checkpoints/data, credential, image/archive, SDK, or path-confusion blockers.",
        "4. Route detailed root ReAct setup to ../react-inference/ and official metric mechanics to ../benchmark-evaluation/.",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Map a free-text task to likely DeepResearch/WebAgent/Agent family routes.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("task", nargs="*", help="Free-text task description.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum routes to print; use 0 for all matched routes.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON instead of Markdown.")
    for flag in sorted(FLAG_TO_SIGNAL):
        parser.add_argument(f"--{flag.replace('_', '-')}", action="store_true", help=f"Add the {FLAG_TO_SIGNAL[flag]!r} signal.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    text = " ".join(args.task)
    enabled_flags = [flag for flag in FLAG_TO_SIGNAL if getattr(args, flag)]
    signals = detect_signals(text, enabled_flags)
    ranked = rank_routes(signals)
    output = as_json(signals, ranked, args.limit) if args.json else as_markdown(signals, ranked, args.limit)
    print(textwrap.dedent(output).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
