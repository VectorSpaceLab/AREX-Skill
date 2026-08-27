#!/usr/bin/env python3
"""Run or dry-run the STORM Wiki article pipeline from knowledge-storm.

Safe modes:
- --help uses only standard-library imports.
- --dry-run validates arguments, credentials, resume prerequisites, and prints a
  JSON execution plan. It does not import knowledge_storm, instantiate retrievers,
  call language models, query search APIs, or create article outputs.

Full runs require the public knowledge-storm package and the selected model and
retriever credentials.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

OUTPUT_FILES_BY_STAGE = {
    "research": ["conversation_log.json", "raw_search_results.json"],
    "outline": ["direct_gen_outline.txt", "storm_gen_outline.txt"],
    "article": ["storm_gen_article.txt", "url_to_info.json"],
    "polish": ["storm_gen_article_polished.txt"],
    "post_run": ["run_config.json", "llm_call_history.jsonl"],
}

RETRIEVER_ENV = {
    "bing": ["BING_SEARCH_API_KEY"],
    "you": ["YDC_API_KEY"],
    "brave": ["BRAVE_API_KEY"],
    "serper": ["SERPER_API_KEY"],
    "duckduckgo": [],
    "tavily": ["TAVILY_API_KEY"],
    "searxng": ["SEARXNG_API_URL"],
    "azure_ai_search": [
        "AZURE_AI_SEARCH_API_KEY",
        "AZURE_AI_SEARCH_URL",
        "AZURE_AI_SEARCH_INDEX_NAME",
    ],
}


def _load_toml_env(path: Path) -> None:
    """Load top-level TOML key/value pairs into os.environ."""
    try:
        import tomllib

        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
        try:
            import toml
        except ModuleNotFoundError as exc:
            raise RuntimeError("--secrets-file requires Python 3.11+ tomllib or the toml package") from exc
        with path.open("r", encoding="utf-8") as handle:
            data = toml.load(handle)
    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)):
            os.environ[str(key)] = str(value)


def _topic_dir_name(topic: str) -> str:
    cleaned = topic.replace(" ", "_").replace("/", "_")
    return cleaned[:125]


def _article_dir(args: argparse.Namespace) -> Path:
    return args.output_dir / _topic_dir_name(args.topic)


def _selected_stages(args: argparse.Namespace) -> list[str]:
    stages: list[str] = []
    if args.do_research:
        stages.append("research")
    if args.do_generate_outline:
        stages.append("outline")
    if args.do_generate_article:
        stages.append("article")
    if args.do_polish_article:
        stages.append("polish")
    return stages


def _resume_prerequisites(args: argparse.Namespace) -> list[dict[str, Any]]:
    article_dir = _article_dir(args)
    prereqs: list[str] = []
    if args.do_generate_outline and not args.do_research:
        prereqs.append("conversation_log.json")
    if args.do_generate_article:
        if not args.do_research:
            prereqs.append("conversation_log.json")
        if not args.do_generate_outline:
            prereqs.append("storm_gen_outline.txt")
    if args.do_polish_article and not args.do_generate_article:
        prereqs.extend(["storm_gen_article.txt", "url_to_info.json"])
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for name in prereqs:
        if name in seen:
            continue
        seen.add(name)
        path = article_dir / name
        rows.append({"file": name, "exists": path.exists()})
    return rows


def _provider_env_options(model: str) -> list[list[str]]:
    """Return acceptable environment-variable groups for a LiteLLM model string."""
    lower = model.lower()
    if lower.startswith("azure/"):
        return [["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"], ["OPENAI_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"]]
    if lower.startswith("openai/") or lower.startswith("gpt-"):
        return [["OPENAI_API_KEY"]]
    if lower.startswith("anthropic/") or lower.startswith("claude"):
        return [["ANTHROPIC_API_KEY"]]
    if lower.startswith("gemini/") or lower.startswith("google/"):
        return [["GEMINI_API_KEY"], ["GOOGLE_API_KEY"]]
    if lower.startswith("groq/"):
        return [["GROQ_API_KEY"]]
    if lower.startswith("mistral/"):
        return [["MISTRAL_API_KEY"]]
    if lower.startswith("deepseek/"):
        return [["DEEPSEEK_API_KEY"]]
    if lower.startswith("ollama"):
        return []
    # Unknown LiteLLM provider; cannot infer a stable key name.
    return []


def _missing_env_group(groups: list[list[str]]) -> list[str] | None:
    if not groups:
        return None
    for group in groups:
        if all(os.getenv(name) for name in group):
            return None
    return groups[0]


def _component_models(args: argparse.Namespace) -> dict[str, str]:
    return {
        "conv_simulator_lm": args.conv_model or args.cheap_model,
        "question_asker_lm": args.question_model or args.cheap_model,
        "outline_gen_lm": args.outline_model or args.strong_model,
        "article_gen_lm": args.article_model or args.strong_model,
        "article_polish_lm": args.polish_model or args.strong_model,
    }


def _model_missing_env(args: argparse.Namespace) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    if args.api_key_env:
        if not os.getenv(args.api_key_env):
            for component in _component_models(args):
                missing[component] = [args.api_key_env]
        return missing
    for component, model in _component_models(args).items():
        group = _missing_env_group(_provider_env_options(model))
        if group:
            missing[component] = group
    return missing


def _retriever_missing_env(args: argparse.Namespace) -> dict[str, bool]:
    missing = {name: not bool(os.getenv(name)) for name in RETRIEVER_ENV[args.retriever]}
    if args.retriever == "searxng" and args.searxng_api_url:
        missing["SEARXNG_API_URL"] = False
    if args.retriever == "azure_ai_search":
        if args.azure_ai_search_api_key:
            missing["AZURE_AI_SEARCH_API_KEY"] = False
        if args.azure_ai_search_url:
            missing["AZURE_AI_SEARCH_URL"] = False
        if args.azure_ai_search_index_name:
            missing["AZURE_AI_SEARCH_INDEX_NAME"] = False
    return {key: value for key, value in missing.items() if value}


def _validate_args(args: argparse.Namespace, *, full_run: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not args.topic.strip():
        errors.append("ERROR: --topic must be non-empty.")
    if not _selected_stages(args):
        errors.append("ERROR: At least one STORM stage must be enabled.")
    if args.max_thread_num <= 0:
        errors.append("ERROR: --max-thread-num must be positive.")
    if args.max_conv_turn <= 0:
        errors.append("ERROR: --max-conv-turn must be positive.")
    if args.max_perspective <= 0:
        warnings.append("WARNING: --max-perspective is <= 0; STORM research may have no useful perspectives.")
    if args.search_top_k <= 0 or args.retrieve_top_k <= 0:
        errors.append("ERROR: --search-top-k and --retrieve-top-k must be positive.")
    if args.max_search_queries_per_turn <= 0:
        errors.append("ERROR: --max-search-queries-per-turn must be positive.")
    if args.secrets_file and not args.secrets_file.exists():
        errors.append(f"ERROR: --secrets-file does not exist: {args.secrets_file}")
    for prereq in _resume_prerequisites(args):
        if not prereq["exists"]:
            warnings.append(f"WARNING: resume prerequisite is missing: {prereq['file']}")
    if full_run:
        model_missing = _model_missing_env(args)
        retriever_missing = _retriever_missing_env(args)
        if model_missing and not args.secrets_file:
            errors.append("ERROR: missing model credential environment variables: " + json.dumps(model_missing, sort_keys=True))
        elif model_missing:
            warnings.append("WARNING: model credentials are not set now; full run will try --secrets-file first.")
        if retriever_missing and not args.secrets_file:
            errors.append("ERROR: missing retriever credential/environment variables: " + ", ".join(sorted(retriever_missing)))
        elif retriever_missing:
            warnings.append("WARNING: retriever credentials are not set now; full run will try --secrets-file first.")
    return errors, warnings


def _plan(args: argparse.Namespace) -> dict[str, Any]:
    article_dir = _article_dir(args)
    expected_outputs: list[str] = []
    for stage in _selected_stages(args):
        expected_outputs.extend(OUTPUT_FILES_BY_STAGE[stage])
    if _selected_stages(args):
        expected_outputs.extend(OUTPUT_FILES_BY_STAGE["post_run"])
    return {
        "topic": args.topic,
        "topic_directory_name": _topic_dir_name(args.topic),
        "article_output_dir": str(article_dir),
        "stages": _selected_stages(args),
        "stage_flags": {
            "do_research": args.do_research,
            "do_generate_outline": args.do_generate_outline,
            "do_generate_article": args.do_generate_article,
            "do_polish_article": args.do_polish_article,
            "remove_duplicate": args.remove_duplicate,
        },
        "resume_prerequisites": _resume_prerequisites(args),
        "expected_outputs": expected_outputs,
        "models": _component_models(args),
        "model_missing_env": _model_missing_env(args),
        "retriever": args.retriever,
        "retriever_missing_env": _retriever_missing_env(args),
        "retriever_args": {
            "searxng_api_url": args.searxng_api_url,
            "azure_ai_search_url_present": bool(args.azure_ai_search_url or os.getenv("AZURE_AI_SEARCH_URL")),
            "azure_ai_search_index_name_present": bool(args.azure_ai_search_index_name or os.getenv("AZURE_AI_SEARCH_INDEX_NAME")),
        },
        "thread_and_search": {
            "max_thread_num": args.max_thread_num,
            "max_conv_turn": args.max_conv_turn,
            "max_perspective": args.max_perspective,
            "max_search_queries_per_turn": args.max_search_queries_per_turn,
            "search_top_k": args.search_top_k,
            "retrieve_top_k": args.retrieve_top_k,
        },
        "note": "Dry-run performs no package import, retriever construction, LLM call, search query, or output creation.",
    }


def _make_lm_factory(args: argparse.Namespace, LitellmModel: Any):
    shared: dict[str, Any] = {"temperature": args.temperature, "top_p": args.top_p}
    if args.api_key_env and os.getenv(args.api_key_env):
        shared["api_key"] = os.getenv(args.api_key_env)
    if args.api_base:
        shared["api_base"] = args.api_base
    if args.api_version:
        shared["api_version"] = args.api_version

    def make_lm(model: str, max_tokens: int):
        return LitellmModel(model=model, max_tokens=max_tokens, model_type=args.model_type, **shared)

    return make_lm


def _build_retriever(args: argparse.Namespace, engine_args: Any):
    from knowledge_storm.rm import (
        AzureAISearch,
        BingSearch,
        BraveRM,
        DuckDuckGoSearchRM,
        SearXNG,
        SerperRM,
        TavilySearchRM,
        YouRM,
    )

    if args.retriever == "bing":
        return BingSearch(bing_search_api_key=os.getenv("BING_SEARCH_API_KEY"), k=engine_args.search_top_k)
    if args.retriever == "you":
        return YouRM(ydc_api_key=os.getenv("YDC_API_KEY"), k=engine_args.search_top_k)
    if args.retriever == "brave":
        return BraveRM(brave_search_api_key=os.getenv("BRAVE_API_KEY"), k=engine_args.search_top_k)
    if args.retriever == "serper":
        return SerperRM(
            serper_search_api_key=os.getenv("SERPER_API_KEY"),
            query_params={"autocorrect": True, "num": max(10, engine_args.search_top_k), "page": 1},
        )
    if args.retriever == "duckduckgo":
        return DuckDuckGoSearchRM(k=engine_args.search_top_k, safe_search="On", region=args.duckduckgo_region)
    if args.retriever == "tavily":
        return TavilySearchRM(tavily_search_api_key=os.getenv("TAVILY_API_KEY"), k=engine_args.search_top_k, include_raw_content=True)
    if args.retriever == "searxng":
        return SearXNG(
            searxng_api_url=args.searxng_api_url or os.getenv("SEARXNG_API_URL"),
            searxng_api_key=os.getenv("SEARXNG_API_KEY"),
            k=engine_args.search_top_k,
        )
    if args.retriever == "azure_ai_search":
        return AzureAISearch(
            azure_ai_search_api_key=args.azure_ai_search_api_key or os.getenv("AZURE_AI_SEARCH_API_KEY"),
            azure_ai_search_url=args.azure_ai_search_url or os.getenv("AZURE_AI_SEARCH_URL"),
            azure_ai_search_index_name=args.azure_ai_search_index_name or os.getenv("AZURE_AI_SEARCH_INDEX_NAME"),
            k=engine_args.search_top_k,
        )
    raise ValueError(f"Unsupported retriever: {args.retriever}")


def _verbose_callback_class():
    from knowledge_storm.storm_wiki.modules.callback import BaseCallbackHandler

    class VerboseCallback(BaseCallbackHandler):
        def on_identify_perspective_start(self, **kwargs):
            print("[storm] identifying perspectives", flush=True)

        def on_identify_perspective_end(self, perspectives: list[str], **kwargs):
            print(f"[storm] perspectives: {len(perspectives)}", flush=True)

        def on_information_gathering_start(self, **kwargs):
            print("[storm] gathering information", flush=True)

        def on_dialogue_turn_end(self, dlg_turn, **kwargs):
            urls = sorted({getattr(info, "url", "") for info in getattr(dlg_turn, "search_results", [])})
            print(f"[storm] dialogue turn complete; unique URLs: {len([u for u in urls if u])}", flush=True)

        def on_information_gathering_end(self, **kwargs):
            print("[storm] information gathering complete", flush=True)

        def on_information_organization_start(self, **kwargs):
            print("[storm] organizing information", flush=True)

        def on_direct_outline_generation_end(self, outline: str, **kwargs):
            print(f"[storm] direct outline chars: {len(outline)}", flush=True)

        def on_outline_refinement_end(self, outline: str, **kwargs):
            print(f"[storm] refined outline chars: {len(outline)}", flush=True)

    return VerboseCallback


def run_full(args: argparse.Namespace) -> int:
    if args.secrets_file:
        _load_toml_env(args.secrets_file)

    errors, warnings = _validate_args(args, full_run=True)
    for warning in warnings:
        print(warning, file=sys.stderr)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2

    from knowledge_storm import STORMWikiLMConfigs, STORMWikiRunner, STORMWikiRunnerArguments
    from knowledge_storm.lm import LitellmModel

    make_lm = _make_lm_factory(args, LitellmModel)
    models = _component_models(args)
    lm_configs = STORMWikiLMConfigs()
    lm_configs.set_conv_simulator_lm(make_lm(models["conv_simulator_lm"], args.conv_max_tokens))
    lm_configs.set_question_asker_lm(make_lm(models["question_asker_lm"], args.question_max_tokens))
    lm_configs.set_outline_gen_lm(make_lm(models["outline_gen_lm"], args.outline_max_tokens))
    lm_configs.set_article_gen_lm(make_lm(models["article_gen_lm"], args.article_max_tokens))
    lm_configs.set_article_polish_lm(make_lm(models["article_polish_lm"], args.polish_max_tokens))

    engine_args = STORMWikiRunnerArguments(
        output_dir=str(args.output_dir),
        max_conv_turn=args.max_conv_turn,
        max_perspective=args.max_perspective,
        max_search_queries_per_turn=args.max_search_queries_per_turn,
        search_top_k=args.search_top_k,
        retrieve_top_k=args.retrieve_top_k,
        max_thread_num=args.max_thread_num,
    )
    rm = _build_retriever(args, engine_args)
    runner = STORMWikiRunner(engine_args, lm_configs, rm)
    callback = _verbose_callback_class()() if args.verbose_callbacks else None

    runner.run(
        topic=args.topic,
        ground_truth_url=args.ground_truth_url,
        do_research=args.do_research,
        do_generate_outline=args.do_generate_outline,
        do_generate_article=args.do_generate_article,
        do_polish_article=args.do_polish_article,
        remove_duplicate=args.remove_duplicate,
        callback_handler=callback,
    )
    runner.post_run()
    runner.summary()
    print(json.dumps(_plan(args), indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or dry-run a STORM Wiki article workflow.")
    parser.add_argument("--topic", required=True, help="Topic to research and write about.")
    parser.add_argument("--output-dir", type=Path, default=Path("./storm-results"), help="Parent output directory.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the plan without importing knowledge_storm or making network/LLM calls.")
    parser.add_argument("--secrets-file", type=Path, help="Optional TOML file with environment variables such as OPENAI_API_KEY.")

    parser.add_argument("--retriever", choices=sorted(RETRIEVER_ENV), default="bing", help="Internet retriever to use.")
    parser.add_argument("--searxng-api-url", help="SearXNG API URL; overrides SEARXNG_API_URL.")
    parser.add_argument("--duckduckgo-region", default="us-en", help="DuckDuckGo region for DuckDuckGoSearchRM.")
    parser.add_argument("--azure-ai-search-api-key", help="Azure AI Search key; overrides AZURE_AI_SEARCH_API_KEY.")
    parser.add_argument("--azure-ai-search-url", help="Azure AI Search endpoint; overrides AZURE_AI_SEARCH_URL.")
    parser.add_argument("--azure-ai-search-index-name", help="Azure AI Search index; overrides AZURE_AI_SEARCH_INDEX_NAME.")

    parser.add_argument("--cheap-model", default="openai/gpt-4o-mini", help="Default model for conversation simulator and question asker.")
    parser.add_argument("--strong-model", default="openai/gpt-4o", help="Default model for outline/article/polish components.")
    parser.add_argument("--conv-model", help="Override conversation simulator model.")
    parser.add_argument("--question-model", help="Override question asker model.")
    parser.add_argument("--outline-model", help="Override outline generator model.")
    parser.add_argument("--article-model", help="Override article generator model.")
    parser.add_argument("--polish-model", help="Override article polish model.")
    parser.add_argument("--api-key-env", help="Single env var to pass as api_key to all LitellmModel instances.")
    parser.add_argument("--api-base", help="Optional API base passed to LitellmModel.")
    parser.add_argument("--api-version", help="Optional API version passed to LitellmModel.")
    parser.add_argument("--model-type", choices=["chat", "text"], default="chat", help="LiteLLM model type.")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--conv-max-tokens", type=int, default=500)
    parser.add_argument("--question-max-tokens", type=int, default=500)
    parser.add_argument("--outline-max-tokens", type=int, default=400)
    parser.add_argument("--article-max-tokens", type=int, default=700)
    parser.add_argument("--polish-max-tokens", type=int, default=4000)

    parser.set_defaults(do_research=True, do_generate_outline=True, do_generate_article=True, do_polish_article=True)
    parser.add_argument("--do-research", dest="do_research", action="store_true", help="Run the research stage (default).")
    parser.add_argument("--skip-research", dest="do_research", action="store_false", help="Skip research and load existing conversation_log.json.")
    parser.add_argument("--do-generate-outline", dest="do_generate_outline", action="store_true", help="Run outline generation (default).")
    parser.add_argument("--skip-generate-outline", dest="do_generate_outline", action="store_false", help="Skip outline generation and load storm_gen_outline.txt as needed.")
    parser.add_argument("--do-generate-article", dest="do_generate_article", action="store_true", help="Run article generation (default).")
    parser.add_argument("--skip-generate-article", dest="do_generate_article", action="store_false", help="Skip article generation and load storm_gen_article.txt/url_to_info.json as needed.")
    parser.add_argument("--do-polish-article", dest="do_polish_article", action="store_true", help="Run polishing (default).")
    parser.add_argument("--skip-polish-article", dest="do_polish_article", action="store_false", help="Skip polishing.")
    parser.add_argument("--remove-duplicate", action="store_true", help="Use the optional duplicate-removal polish pass.")
    parser.add_argument("--ground-truth-url", default="", help="Known reference URL to exclude from retrieval.")

    parser.add_argument("--max-conv-turn", type=int, default=3)
    parser.add_argument("--max-perspective", type=int, default=3)
    parser.add_argument("--max-search-queries-per-turn", type=int, default=3)
    parser.add_argument("--search-top-k", type=int, default=3)
    parser.add_argument("--retrieve-top-k", type=int, default=3)
    parser.add_argument("--max-thread-num", type=int, default=2)
    parser.add_argument("--verbose-callbacks", action="store_true", help="Print progress callbacks during full runs.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.secrets_file and args.dry_run:
        try:
            _load_toml_env(args.secrets_file)
        except Exception as exc:
            print(f"ERROR: unable to load --secrets-file: {exc}", file=sys.stderr)
            return 2
    if args.dry_run:
        errors, warnings = _validate_args(args, full_run=False)
        for warning in warnings:
            print(warning, file=sys.stderr)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 2
        print(json.dumps(_plan(args), indent=2, sort_keys=True))
        return 0
    return run_full(args)


if __name__ == "__main__":
    raise SystemExit(main())
