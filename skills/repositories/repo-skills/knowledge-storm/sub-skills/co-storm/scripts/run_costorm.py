#!/usr/bin/env python3
"""Run or dry-run a noninteractive Co-STORM session from knowledge-storm.

Safe modes:
- --help uses only standard-library imports.
- --dry-run validates arguments and reports the selected model, embedding, and
  retriever environment plan. It does not import knowledge_storm, construct an
  encoder or retriever, call language models, query search APIs, or write run
  outputs.

Full runs require the public knowledge-storm package, model credentials,
embedding credentials for the Co-STORM Encoder, and retriever credentials for
credentialed search backends.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

OUTPUT_FILES = ["report.md", "report.txt", "instance_dump.json", "log.json"]

RETRIEVER_ENV = {
    "bing": ["BING_SEARCH_API_KEY"],
    "you": ["YDC_API_KEY"],
    "brave": ["BRAVE_API_KEY"],
    "serper": ["SERPER_API_KEY"],
    "duckduckgo": [],
    "tavily": ["TAVILY_API_KEY"],
    "searxng": ["SEARXNG_API_URL"],
}

SECRET_WORDS = ("api_key", "apikey", "token", "password", "secret", "credential")


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
    if lower.startswith("together/") or lower.startswith("together_ai/"):
        return [["TOGETHER_API_KEY"]]
    if lower.startswith("ollama"):
        return []
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
        "question_answering_lm": args.question_answering_model or args.model,
        "discourse_manage_lm": args.discourse_manage_model or args.model,
        "utterance_polishing_lm": args.utterance_polishing_model or args.model,
        "warmstart_outline_gen_lm": args.warmstart_outline_model or args.model,
        "question_asking_lm": args.question_asking_model or args.model,
        "knowledge_base_lm": args.knowledge_base_model or args.model,
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


def _apply_encoder_arg_env(args: argparse.Namespace) -> None:
    """Map CLI encoder settings into the environment read by knowledge_storm.encoder.Encoder."""
    if args.encoder_api_type:
        os.environ["ENCODER_API_TYPE"] = args.encoder_api_type
    encoder_type = (os.getenv("ENCODER_API_TYPE") or "").lower()
    if args.encoder_api_key_env and os.getenv(args.encoder_api_key_env):
        if encoder_type == "azure":
            os.environ["AZURE_API_KEY"] = os.getenv(args.encoder_api_key_env, "")
        elif encoder_type == "openai":
            os.environ["OPENAI_API_KEY"] = os.getenv(args.encoder_api_key_env, "")
    if args.encoder_api_base:
        os.environ["AZURE_API_BASE"] = args.encoder_api_base
    if args.encoder_api_version:
        os.environ["AZURE_API_VERSION"] = args.encoder_api_version


def _encoder_missing_env(args: argparse.Namespace) -> dict[str, bool]:
    encoder_type = (args.encoder_api_type or os.getenv("ENCODER_API_TYPE") or "").lower()
    if not encoder_type:
        return {"ENCODER_API_TYPE": True}
    if encoder_type == "openai":
        return {"OPENAI_API_KEY": True} if not os.getenv("OPENAI_API_KEY") else {}
    if encoder_type == "azure":
        required = ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"]
        return {name: True for name in required if not os.getenv(name)}
    return {"ENCODER_API_TYPE_supported_values_openai_or_azure": True}


def _retriever_missing_env(args: argparse.Namespace) -> dict[str, bool]:
    missing = {name: not bool(os.getenv(name)) for name in RETRIEVER_ENV[args.retriever]}
    if args.retriever == "searxng" and args.searxng_api_url:
        missing["SEARXNG_API_URL"] = False
    return {key: value for key, value in missing.items() if value}


def _runner_argument_plan(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "topic": args.topic,
        "retrieve_top_k": args.retrieve_top_k,
        "max_search_queries": args.max_search_queries,
        "total_conv_turn": args.total_conv_turn,
        "max_search_thread": args.max_search_thread,
        "max_search_queries_per_turn": args.max_search_queries_per_turn,
        "warmstart_max_num_experts": args.warmstart_max_num_experts,
        "warmstart_max_turn_per_experts": args.warmstart_max_turn_per_experts,
        "warmstart_max_thread": args.warmstart_max_thread,
        "max_thread_num": args.max_thread_num,
        "max_num_round_table_experts": args.max_num_round_table_experts,
        "moderator_override_N_consecutive_answering_turn": args.moderator_override_N_consecutive_answering_turn,
        "node_expansion_trigger_count": args.node_expansion_trigger_count,
        "disable_moderator": args.disable_moderator,
        "disable_multi_experts": args.disable_multi_experts,
        "rag_only_baseline_mode": args.rag_only_baseline_mode,
    }


def _validate_args(args: argparse.Namespace, *, full_run: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not args.topic.strip():
        errors.append("ERROR: --topic must be non-empty.")
    if args.secrets_file and not args.secrets_file.exists():
        errors.append(f"ERROR: --secrets-file does not exist: {args.secrets_file}")
    integer_fields = [
        "retrieve_top_k",
        "max_search_queries",
        "total_conv_turn",
        "max_search_thread",
        "max_search_queries_per_turn",
        "warmstart_max_num_experts",
        "warmstart_max_turn_per_experts",
        "warmstart_max_thread",
        "max_thread_num",
        "max_num_round_table_experts",
        "moderator_override_N_consecutive_answering_turn",
        "node_expansion_trigger_count",
    ]
    for field in integer_fields:
        if getattr(args, field) <= 0:
            errors.append(f"ERROR: --{field.replace('_', '-')} must be positive.")
    if args.observe_turns < 0:
        errors.append("ERROR: --observe-turns must be zero or positive.")
    if args.rag_only_baseline_mode and args.observe_turns > 0:
        warnings.append(
            "WARNING: rag-only Co-STORM turns are fragile in this package version; prefer normal mode for reports, or validate a patched runner before observing PureRAG turns."
        )
    if full_run:
        model_missing = _model_missing_env(args)
        encoder_missing = _encoder_missing_env(args)
        retriever_missing = _retriever_missing_env(args)
        if model_missing:
            errors.append("ERROR: missing model credential environment variables: " + json.dumps(model_missing, sort_keys=True))
        if encoder_missing:
            errors.append("ERROR: missing encoder credential/environment variables: " + ", ".join(sorted(encoder_missing)))
        if retriever_missing:
            errors.append("ERROR: missing retriever credential/environment variables: " + ", ".join(sorted(retriever_missing)))
    return errors, warnings


def _plan(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "topic": args.topic,
        "output_dir": str(args.output_dir),
        "expected_outputs": [str(args.output_dir / name) for name in OUTPUT_FILES],
        "models": _component_models(args),
        "model_missing_env": _model_missing_env(args),
        "encoder": {
            "encoder_api_type": args.encoder_api_type or os.getenv("ENCODER_API_TYPE"),
            "encoder_missing_env": _encoder_missing_env(args),
        },
        "retriever": args.retriever,
        "retriever_missing_env": _retriever_missing_env(args),
        "retriever_args": {
            "searxng_api_url_present": bool(args.searxng_api_url or os.getenv("SEARXNG_API_URL")),
            "duckduckgo_region": args.duckduckgo_region,
            "duckduckgo_safe_search": args.duckduckgo_safe_search,
        },
        "runner_argument": _runner_argument_plan(args),
        "step_plan": {
            "warm_start": True,
            "user_utterance_present": bool(args.user_utterance),
            "observe_turns": args.observe_turns,
            "generate_report": True,
            "enable_console_log": args.enable_console_log,
        },
        "note": "Dry-run performs no package import, Encoder construction, retriever construction, LLM call, search query, or output creation.",
    }


def _litellm_kwargs_for(model: str, args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"temperature": args.temperature, "top_p": args.top_p}
    lower = model.lower()
    if args.api_key_env and os.getenv(args.api_key_env):
        kwargs["api_key"] = os.getenv(args.api_key_env)
    elif lower.startswith("azure/") and os.getenv("AZURE_API_KEY"):
        kwargs["api_key"] = os.getenv("AZURE_API_KEY")
    elif (lower.startswith("openai/") or lower.startswith("gpt-")) and os.getenv("OPENAI_API_KEY"):
        kwargs["api_key"] = os.getenv("OPENAI_API_KEY")
    if args.api_base:
        kwargs["api_base"] = args.api_base
    elif lower.startswith("azure/") and os.getenv("AZURE_API_BASE"):
        kwargs["api_base"] = os.getenv("AZURE_API_BASE")
    if args.api_version:
        kwargs["api_version"] = args.api_version
    elif lower.startswith("azure/") and os.getenv("AZURE_API_VERSION"):
        kwargs["api_version"] = os.getenv("AZURE_API_VERSION")
    return kwargs


def _make_lm(LitellmModel: Any, model: str, max_tokens: int, args: argparse.Namespace):
    return LitellmModel(
        model=model,
        max_tokens=max_tokens,
        model_type=args.model_type,
        **_litellm_kwargs_for(model, args),
    )


def _build_lm_config(args: argparse.Namespace):
    from knowledge_storm.collaborative_storm.engine import CollaborativeStormLMConfigs
    from knowledge_storm.lm import LitellmModel

    models = _component_models(args)
    lm_config = CollaborativeStormLMConfigs()
    lm_config.set_question_answering_lm(_make_lm(LitellmModel, models["question_answering_lm"], args.question_answering_max_tokens, args))
    lm_config.set_discourse_manage_lm(_make_lm(LitellmModel, models["discourse_manage_lm"], args.discourse_manage_max_tokens, args))
    lm_config.set_utterance_polishing_lm(_make_lm(LitellmModel, models["utterance_polishing_lm"], args.utterance_polishing_max_tokens, args))
    lm_config.set_warmstart_outline_gen_lm(_make_lm(LitellmModel, models["warmstart_outline_gen_lm"], args.warmstart_outline_max_tokens, args))
    lm_config.set_question_asking_lm(_make_lm(LitellmModel, models["question_asking_lm"], args.question_asking_max_tokens, args))
    lm_config.set_knowledge_base_lm(_make_lm(LitellmModel, models["knowledge_base_lm"], args.knowledge_base_max_tokens, args))
    return lm_config


def _build_runner_argument(args: argparse.Namespace):
    from knowledge_storm.collaborative_storm.engine import RunnerArgument

    return RunnerArgument(**_runner_argument_plan(args))


def _build_retriever(args: argparse.Namespace, runner_argument: Any):
    from knowledge_storm.rm import BingSearch, BraveRM, DuckDuckGoSearchRM, SearXNG, SerperRM, TavilySearchRM, YouRM

    if args.retriever == "bing":
        return BingSearch(bing_search_api_key=os.getenv("BING_SEARCH_API_KEY"), k=runner_argument.retrieve_top_k)
    if args.retriever == "you":
        return YouRM(ydc_api_key=os.getenv("YDC_API_KEY"), k=runner_argument.retrieve_top_k)
    if args.retriever == "brave":
        return BraveRM(brave_search_api_key=os.getenv("BRAVE_API_KEY"), k=runner_argument.retrieve_top_k)
    if args.retriever == "serper":
        return SerperRM(
            serper_search_api_key=os.getenv("SERPER_API_KEY"),
            k=runner_argument.retrieve_top_k,
            query_params={"autocorrect": True, "num": max(10, runner_argument.retrieve_top_k), "page": args.serper_page},
        )
    if args.retriever == "duckduckgo":
        return DuckDuckGoSearchRM(k=runner_argument.retrieve_top_k, safe_search=args.duckduckgo_safe_search, region=args.duckduckgo_region)
    if args.retriever == "tavily":
        return TavilySearchRM(tavily_search_api_key=os.getenv("TAVILY_API_KEY"), k=runner_argument.retrieve_top_k, include_raw_content=args.tavily_include_raw_content)
    if args.retriever == "searxng":
        return SearXNG(
            searxng_api_url=args.searxng_api_url or os.getenv("SEARXNG_API_URL"),
            searxng_api_key=os.getenv(args.searxng_api_key_env),
            k=runner_argument.retrieve_top_k,
        )
    raise ValueError(f"Unsupported retriever: {args.retriever}")


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if any(word in str(key).lower() for word in SECRET_WORDS):
                out[key] = "<redacted>"
            else:
                out[key] = _redact(value)
        return out
    if isinstance(obj, list):
        return [_redact(item) for item in obj]
    return obj


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def run_full(args: argparse.Namespace) -> int:
    if args.secrets_file:
        _load_toml_env(args.secrets_file)
    _apply_encoder_arg_env(args)

    errors, warnings = _validate_args(args, full_run=True)
    for warning in warnings:
        print(warning, file=sys.stderr)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2

    from knowledge_storm.collaborative_storm.engine import CoStormRunner
    from knowledge_storm.collaborative_storm.modules.callback import LocalConsolePrintCallBackHandler
    from knowledge_storm.logging_wrapper import LoggingWrapper

    args.output_dir.mkdir(parents=True, exist_ok=True)

    lm_config = _build_lm_config(args)
    runner_argument = _build_runner_argument(args)
    logging_wrapper = LoggingWrapper(lm_config)
    retriever = _build_retriever(args, runner_argument)
    callback_handler = LocalConsolePrintCallBackHandler() if args.enable_console_log else None

    runner = CoStormRunner(
        lm_config=lm_config,
        runner_argument=runner_argument,
        logging_wrapper=logging_wrapper,
        rm=retriever,
        callback_handler=callback_handler,
    )

    runner.warm_start()
    if not runner.conversation_history:
        _write_json(args.output_dir / "log.json", runner.dump_logging_and_reset())
        raise RuntimeError("warm_start did not populate conversation_history; inspect log.json and provider/search errors")

    if args.user_utterance:
        guest_turn = runner.step(user_utterance=args.user_utterance)
        print(f"**{guest_turn.role}**: {guest_turn.utterance}\n", flush=True)

    for _ in range(args.observe_turns):
        conv_turn = runner.step()
        print(f"**{conv_turn.role}**: {conv_turn.utterance}\n", flush=True)

    runner.knowledge_base.reorganize()
    article = runner.generate_report()

    _write_text(args.output_dir / "report.md", article)
    _write_text(args.output_dir / "report.txt", article)
    _write_json(args.output_dir / "instance_dump.json", _redact(runner.to_dict()))
    _write_json(args.output_dir / "log.json", _redact(runner.dump_logging_and_reset()))
    print(json.dumps(_plan(args), indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or dry-run a noninteractive Co-STORM session.")
    parser.add_argument("--topic", required=True, help="Topic for the collaborative Co-STORM discourse.")
    parser.add_argument("--output-dir", type=Path, default=Path("./results/co-storm"), help="Directory for report.md, report.txt, instance_dump.json, and log.json.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the plan without importing knowledge_storm or making network/LLM calls.")
    parser.add_argument("--secrets-file", type=Path, help="Optional TOML file with environment variables such as OPENAI_API_KEY or BING_SEARCH_API_KEY.")

    parser.add_argument("--retriever", choices=sorted(RETRIEVER_ENV), default="bing", help="Internet retriever to use.")
    parser.add_argument("--searxng-api-url", help="SearXNG API URL; overrides SEARXNG_API_URL.")
    parser.add_argument("--searxng-api-key-env", default="SEARXNG_API_KEY", help="Environment variable holding the optional SearXNG API key.")
    parser.add_argument("--duckduckgo-region", default="us-en", help="DuckDuckGo region.")
    parser.add_argument("--duckduckgo-safe-search", default="On", choices=["On", "Moderate", "Off"], help="DuckDuckGo safe search setting.")
    parser.add_argument("--serper-page", type=int, default=1, help="Serper results page.")
    parser.add_argument("--tavily-include-raw-content", action="store_true", help="Ask Tavily for raw content when available.")

    parser.add_argument("--model", default="openai/gpt-4o", help="Default LiteLLM model string for every Co-STORM component.")
    parser.add_argument("--question-answering-model", help="Override model for grounded QA/query decomposition.")
    parser.add_argument("--discourse-manage-model", help="Override model for turn policy and expert management.")
    parser.add_argument("--utterance-polishing-model", help="Override model for utterance polishing.")
    parser.add_argument("--warmstart-outline-model", help="Override model for warm-start outline generation.")
    parser.add_argument("--question-asking-model", help="Override model for moderator/question generation.")
    parser.add_argument("--knowledge-base-model", help="Override model for mind-map insertion and report generation.")
    parser.add_argument("--api-key-env", help="Single env var to pass as api_key to all LitellmModel instances.")
    parser.add_argument("--api-base", help="Optional API base passed to LitellmModel.")
    parser.add_argument("--api-version", help="Optional API version passed to LitellmModel.")
    parser.add_argument("--model-type", choices=["chat", "text"], default="chat", help="LiteLLM model type.")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--question-answering-max-tokens", type=int, default=1000)
    parser.add_argument("--discourse-manage-max-tokens", type=int, default=500)
    parser.add_argument("--utterance-polishing-max-tokens", type=int, default=2000)
    parser.add_argument("--warmstart-outline-max-tokens", type=int, default=500)
    parser.add_argument("--question-asking-max-tokens", type=int, default=300)
    parser.add_argument("--knowledge-base-max-tokens", type=int, default=1000)

    parser.add_argument("--encoder-api-type", choices=["openai", "azure"], help="Set ENCODER_API_TYPE for Co-STORM's Encoder before constructing the runner.")
    parser.add_argument("--encoder-api-key-env", help="Env var to copy into OPENAI_API_KEY or AZURE_API_KEY for the Encoder.")
    parser.add_argument("--encoder-api-base", help="Set AZURE_API_BASE for the Encoder when using azure embeddings.")
    parser.add_argument("--encoder-api-version", help="Set AZURE_API_VERSION for the Encoder when using azure embeddings.")

    parser.add_argument("--observe-turns", type=int, default=1, help="Number of system-generated turns to observe after warm_start and optional user injection.")
    parser.add_argument("--user-utterance", default="", help="Optional human steering utterance to inject before observing system turns.")
    parser.add_argument("--enable-console-log", action="store_true", help="Enable LocalConsolePrintCallBackHandler progress messages.")

    parser.add_argument("--retrieve-top-k", "--retrieve_top_k", dest="retrieve_top_k", type=int, default=10)
    parser.add_argument("--max-search-queries", "--max_search_queries", dest="max_search_queries", type=int, default=2)
    parser.add_argument("--total-conv-turn", "--total_conv_turn", dest="total_conv_turn", type=int, default=20)
    parser.add_argument("--max-search-thread", "--max_search_thread", dest="max_search_thread", type=int, default=5)
    parser.add_argument("--max-search-queries-per-turn", "--max_search_queries_per_turn", dest="max_search_queries_per_turn", type=int, default=3)
    parser.add_argument("--warmstart-max-num-experts", "--warmstart_max_num_experts", dest="warmstart_max_num_experts", type=int, default=3)
    parser.add_argument("--warmstart-max-turn-per-experts", "--warmstart_max_turn_per_experts", dest="warmstart_max_turn_per_experts", type=int, default=2)
    parser.add_argument("--warmstart-max-thread", "--warmstart_max_thread", dest="warmstart_max_thread", type=int, default=3)
    parser.add_argument("--max-thread-num", "--max_thread_num", dest="max_thread_num", type=int, default=10)
    parser.add_argument("--max-num-round-table-experts", "--max_num_round_table_experts", dest="max_num_round_table_experts", type=int, default=2)
    parser.add_argument(
        "--moderator-override-N-consecutive-answering-turn",
        "--moderator_override_N_consecutive_answering_turn",
        dest="moderator_override_N_consecutive_answering_turn",
        type=int,
        default=3,
    )
    parser.add_argument("--node-expansion-trigger-count", "--node_expansion_trigger_count", dest="node_expansion_trigger_count", type=int, default=10)
    parser.add_argument("--disable-moderator", action="store_true")
    parser.add_argument("--disable-multi-experts", action="store_true")
    parser.add_argument("--rag-only-baseline-mode", action="store_true")
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
    _apply_encoder_arg_env(args)
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
    try:
        return run_full(args)
    except Exception as exc:
        print(f"ERROR: Co-STORM run failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
