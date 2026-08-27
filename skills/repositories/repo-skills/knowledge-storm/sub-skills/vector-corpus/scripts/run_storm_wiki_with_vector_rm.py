#!/usr/bin/env python3
"""Run STORM Wiki with VectorRM over a CSV/Qdrant corpus.

Safe modes:
- --help uses only standard-library imports.
- --dry-run validates arguments/CSV and prints the execution plan.
- --validate-only validates arguments/CSV and exits.

Dry-run and validate-only do not instantiate embeddings, connect to Qdrant, call
LLMs, or use the network.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = ("content", "url")
OPTIONAL_COLUMNS = ("title", "description")


def _is_blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _check_csv(path: Path, *, strict_unique_url: bool = True) -> tuple[list[str], list[str], int]:
    """Return (errors, warnings, row_count) for a VectorRM CSV without heavy imports."""
    errors: list[str] = []
    warnings: list[str] = []
    if path.suffix.lower() != ".csv":
        errors.append(f"ERROR: input path must end with .csv: {path}")
    if not path.exists():
        errors.append(f"ERROR: input path does not exist: {path}")
    if path.exists() and not path.is_file():
        errors.append(f"ERROR: input path is not a file: {path}")
    if errors:
        return errors, warnings, 0

    row_count = 0
    seen_urls: dict[str, int] = {}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                errors.append("ERROR: CSV has no header row. Required columns: content, url")
                return errors, warnings, row_count
            headers = [h.strip() if h is not None else "" for h in reader.fieldnames]
            missing = [column for column in REQUIRED_COLUMNS if column not in headers]
            if missing:
                errors.append("ERROR: missing required column(s): " + ", ".join(missing))
                return errors, warnings, row_count
            missing_optional = [column for column in OPTIONAL_COLUMNS if column not in headers]
            if missing_optional:
                warnings.append(
                    "WARNING: optional column(s) not present: " + ", ".join(missing_optional)
                )
            for row in reader:
                row_count += 1
                line_no = reader.line_num
                content = row.get("content")
                url = row.get("url")
                if _is_blank(content):
                    errors.append(f"ERROR: row {line_no} has empty content")
                if _is_blank(url):
                    errors.append(f"ERROR: row {line_no} has empty url")
                    continue
                normalized_url = str(url).strip()
                first_line = seen_urls.get(normalized_url)
                if first_line is not None:
                    message = (
                        f"duplicate url value {normalized_url!r} first seen at row "
                        f"{first_line}, repeated at row {line_no}"
                    )
                    if strict_unique_url:
                        errors.append("ERROR: " + message)
                    else:
                        warnings.append("WARNING: " + message)
                else:
                    seen_urls[normalized_url] = line_no
    except UnicodeDecodeError as exc:
        errors.append(f"ERROR: unable to decode CSV as UTF-8: {exc}")
    except csv.Error as exc:
        errors.append(f"ERROR: unable to parse CSV: {exc}")
    except OSError as exc:
        errors.append(f"ERROR: unable to read CSV: {exc}")
    return errors, warnings, row_count


def _load_toml_env(path: Path) -> None:
    """Load top-level TOML key/value pairs into os.environ."""
    try:
        import tomllib  # Python 3.11+

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


def _qdrant_key(args: argparse.Namespace) -> str | None:
    return args.qdrant_api_key or os.getenv("QDRANT_API_KEY")


def _selected_stages(args: argparse.Namespace) -> list[str]:
    stages = []
    if args.do_research:
        stages.append("research")
    if args.do_generate_outline:
        stages.append("generate_outline")
    if args.do_generate_article:
        stages.append("generate_article")
    if args.do_polish_article:
        stages.append("polish_article")
    return stages


def _validate_args(args: argparse.Namespace, *, full_run: bool) -> tuple[list[str], list[str], int | None]:
    errors: list[str] = []
    warnings: list[str] = []
    csv_rows: int | None = None

    if not args.collection_name.strip():
        errors.append("ERROR: --collection-name must be non-empty.")
    if args.chunk_overlap >= args.chunk_size:
        errors.append("ERROR: --chunk-overlap must be smaller than --chunk-size.")
    if args.embed_batch_size <= 0:
        errors.append("ERROR: --embed-batch-size must be positive.")
    if args.search_top_k <= 0 or args.retrieve_top_k <= 0:
        errors.append("ERROR: --search-top-k and --retrieve-top-k must be positive.")
    if args.max_thread_num <= 0:
        errors.append("ERROR: --max-thread-num must be positive.")

    if args.csv_file_path:
        csv_errors, csv_warnings, csv_rows = _check_csv(
            args.csv_file_path,
            strict_unique_url=not args.allow_duplicate_url,
        )
        errors.extend(csv_errors)
        warnings.extend(csv_warnings)
        if csv_rows == 0:
            warnings.append("WARNING: CSV has zero data rows after reading the header.")

    if args.vector_db_mode == "offline":
        if _is_blank(args.offline_vector_db_dir):
            errors.append("ERROR: offline mode requires --offline-vector-db-dir.")
        elif not args.csv_file_path and not args.offline_vector_db_dir.exists():
            errors.append(
                "ERROR: offline vector store path does not exist and no --csv-file-path "
                "was supplied to create/update it."
            )
    elif args.vector_db_mode == "online":
        if _is_blank(args.online_vector_db_url):
            errors.append("ERROR: online mode requires --online-vector-db-url.")
        if _is_blank(_qdrant_key(args)):
            if args.secrets_file:
                warnings.append(
                    "WARNING: QDRANT_API_KEY is not currently set; full runs will attempt "
                    "to load it from --secrets-file before contacting Qdrant."
                )
            else:
                errors.append("ERROR: online mode requires QDRANT_API_KEY or --qdrant-api-key.")
        if not args.csv_file_path:
            warnings.append(
                "WARNING: no --csv-file-path supplied; validate-only/dry-run cannot check "
                "whether the online collection already exists."
            )
    else:  # argparse choices should prevent this.
        errors.append("ERROR: --vector-db-mode must be offline or online.")

    if args.secrets_file and not args.secrets_file.exists():
        errors.append(f"ERROR: --secrets-file does not exist: {args.secrets_file}")

    if full_run:
        if _is_blank(args.topic):
            errors.append("ERROR: full run requires --topic.")
        if not _selected_stages(args):
            errors.append(
                "ERROR: No STORM stage selected. Add one or more of --do-research, "
                "--do-generate-outline, --do-generate-article, --do-polish-article."
            )
        if args.lm_api_key_env and _is_blank(os.getenv(args.lm_api_key_env)):
            if args.secrets_file:
                warnings.append(
                    f"WARNING: --lm-api-key-env {args.lm_api_key_env!r} is not currently set; "
                    "full runs will attempt to load it from --secrets-file."
                )
            else:
                errors.append(f"ERROR: --lm-api-key-env {args.lm_api_key_env!r} is not set.")

    return errors, warnings, csv_rows


def _print_plan(args: argparse.Namespace, csv_rows: int | None) -> None:
    print("VectorRM STORM plan")
    print(f"  mode: {args.vector_db_mode}")
    print(f"  collection: {args.collection_name}")
    print(f"  embedding_model: {args.embedding_model}")
    print(f"  device: {args.device}")
    print(f"  csv_file_path: {args.csv_file_path or '(reuse existing collection)'}")
    if csv_rows is not None:
        print(f"  csv_rows_checked: {csv_rows}")
    if args.vector_db_mode == "offline":
        print(f"  offline_vector_db_dir: {args.offline_vector_db_dir}")
    else:
        print(f"  online_vector_db_url: {args.online_vector_db_url}")
        print(f"  qdrant_api_key_present: {bool(_qdrant_key(args))}")
    print(f"  chunk_size: {args.chunk_size}")
    print(f"  chunk_overlap: {args.chunk_overlap}")
    print(f"  embed_batch_size: {args.embed_batch_size}")
    print(f"  topic: {args.topic or '(not provided)'}")
    print(f"  stages: {', '.join(_selected_stages(args)) or '(none selected)'}")
    print("  lm_models:")
    print(f"    conv_simulator: {args.conv_simulator_model}")
    print(f"    question_asker: {args.question_asker_model}")
    print(f"    outline_gen: {args.outline_gen_model}")
    print(f"    article_gen: {args.article_gen_model}")
    print(f"    article_polish: {args.article_polish_model}")
    print("No embedding, Qdrant, LLM, or network calls were performed in this mode.")


def _make_lm_factory(args: argparse.Namespace, LitellmModel: Any):
    api_key = os.getenv(args.lm_api_key_env) if args.lm_api_key_env else None
    shared_kwargs: dict[str, Any] = {
        "temperature": args.temperature,
        "top_p": args.top_p,
    }
    if api_key:
        shared_kwargs["api_key"] = api_key
    if args.lm_api_base:
        shared_kwargs["api_base"] = args.lm_api_base
    if args.lm_api_version:
        shared_kwargs["api_version"] = args.lm_api_version

    def make_lm(model: str, max_tokens: int):
        return LitellmModel(
            model=model,
            model_type=args.lm_model_type,
            max_tokens=max_tokens,
            **shared_kwargs,
        )

    return make_lm


def run_full(args: argparse.Namespace) -> int:
    if args.secrets_file:
        try:
            _load_toml_env(args.secrets_file)
        except Exception as exc:
            print(f"ERROR: unable to load --secrets-file: {exc}", file=sys.stderr)
            return 1

    try:
        from knowledge_storm import STORMWikiLMConfigs, STORMWikiRunner, STORMWikiRunnerArguments
        from knowledge_storm.lm import LitellmModel
        from knowledge_storm.rm import VectorRM
        from knowledge_storm.utils import QdrantVectorStoreManager
    except Exception as exc:
        print(
            "ERROR: unable to import knowledge_storm runtime dependencies. "
            "Install the public package with `python -m pip install knowledge-storm` "
            f"and retry. Import error: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        if args.csv_file_path:
            store_kwargs = {
                "collection_name": args.collection_name,
                "vector_db_mode": args.vector_db_mode,
                "file_path": str(args.csv_file_path),
                "content_column": args.content_column,
                "title_column": args.title_column,
                "url_column": args.url_column,
                "desc_column": args.desc_column,
                "batch_size": args.embed_batch_size,
                "chunk_size": args.chunk_size,
                "chunk_overlap": args.chunk_overlap,
                "embedding_model": args.embedding_model,
                "device": args.device,
            }
            if args.vector_db_mode == "offline":
                QdrantVectorStoreManager.create_or_update_vector_store(
                    vector_store_path=str(args.offline_vector_db_dir),
                    **store_kwargs,
                )
            else:
                QdrantVectorStoreManager.create_or_update_vector_store(
                    url=args.online_vector_db_url,
                    qdrant_api_key=_qdrant_key(args),
                    **store_kwargs,
                )

        engine_args = STORMWikiRunnerArguments(
            output_dir=str(args.output_dir),
            max_conv_turn=args.max_conv_turn,
            max_perspective=args.max_perspective,
            max_search_queries_per_turn=args.max_search_queries_per_turn,
            search_top_k=args.search_top_k,
            retrieve_top_k=args.retrieve_top_k,
            max_thread_num=args.max_thread_num,
        )

        rm = VectorRM(
            collection_name=args.collection_name,
            embedding_model=args.embedding_model,
            device=args.device,
            k=engine_args.search_top_k,
        )
        if args.vector_db_mode == "offline":
            rm.init_offline_vector_db(vector_store_path=str(args.offline_vector_db_dir))
        else:
            rm.init_online_vector_db(url=args.online_vector_db_url, api_key=_qdrant_key(args))

        try:
            count_result = rm.get_vector_count()
            print(f"Vector count: {getattr(count_result, 'count', count_result)}")
        except Exception as exc:
            print(f"WARNING: unable to read vector count before run: {exc}", file=sys.stderr)

        lm_configs = STORMWikiLMConfigs()
        make_lm = _make_lm_factory(args, LitellmModel)
        lm_configs.set_conv_simulator_lm(make_lm(args.conv_simulator_model, args.conv_simulator_max_tokens))
        lm_configs.set_question_asker_lm(make_lm(args.question_asker_model, args.question_asker_max_tokens))
        lm_configs.set_outline_gen_lm(make_lm(args.outline_gen_model, args.outline_gen_max_tokens))
        lm_configs.set_article_gen_lm(make_lm(args.article_gen_model, args.article_gen_max_tokens))
        lm_configs.set_article_polish_lm(make_lm(args.article_polish_model, args.article_polish_max_tokens))

        runner = STORMWikiRunner(engine_args, lm_configs, rm)
        runner.run(
            topic=args.topic,
            do_research=args.do_research,
            do_generate_outline=args.do_generate_outline,
            do_generate_article=args.do_generate_article,
            do_polish_article=args.do_polish_article,
            remove_duplicate=args.remove_duplicate,
        )
        runner.post_run()
        runner.summary()
    except Exception as exc:
        print(f"ERROR: STORM VectorRM run failed: {exc}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run or validate a STORM Wiki workflow grounded on a VectorRM/Qdrant corpus."
    )

    # Safe modes.
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the plan without embeddings, Qdrant, LLM, or network calls.")
    parser.add_argument("--validate-only", action="store_true", help="Validate arguments and CSV schema, then exit without embeddings, Qdrant, LLM, or network calls.")

    # Corpus/vector-store settings.
    parser.add_argument("--collection-name", default="my_documents", help="Qdrant collection name. Default: my_documents.")
    parser.add_argument("--embedding-model", "--embedding_model", dest="embedding_model", default="BAAI/bge-m3", help="Hugging Face embedding model for VectorRM. Default: BAAI/bge-m3.")
    parser.add_argument("--device", choices=("cpu", "cuda", "mps"), default="cpu", help="Embedding device. CPU is functionally sufficient; CUDA/MPS are acceleration only. Default: cpu.")
    parser.add_argument("--vector-db-mode", choices=("offline", "online"), default="offline", help="Qdrant mode. Default: offline.")
    parser.add_argument("--offline-vector-db-dir", type=Path, default=Path("./vector_store"), help="Local Qdrant directory for offline mode. Default: ./vector_store.")
    parser.add_argument("--online-vector-db-url", help="Qdrant server/cloud URL for online mode.")
    parser.add_argument("--qdrant-api-key", help="Qdrant API key for online mode. Prefer QDRANT_API_KEY environment variable.")
    parser.add_argument("--csv-file-path", type=Path, help="CSV corpus to create/update the vector store. Omit to reuse an existing collection.")
    parser.add_argument("--content-column", default="content", help="CSV content column name. Default: content.")
    parser.add_argument("--title-column", default="title", help="CSV title column name. Default: title.")
    parser.add_argument("--url-column", default="url", help="CSV URL/id column name. Default: url.")
    parser.add_argument("--desc-column", default="description", help="CSV description column name. Default: description.")
    parser.add_argument("--allow-duplicate-url", action="store_true", help="Allow duplicate CSV url values. Not recommended for indexing.")
    parser.add_argument("--embed-batch-size", type=int, default=64, help="Embedding/add-documents batch size. Default: 64.")
    parser.add_argument("--chunk-size", type=int, default=500, help="Text splitter chunk size. Default: 500.")
    parser.add_argument("--chunk-overlap", type=int, default=100, help="Text splitter chunk overlap. Default: 100.")

    # STORM stage/runtime settings.
    parser.add_argument("--topic", help="Topic for the STORM run. Required for a full run.")
    parser.add_argument("--output-dir", type=Path, default=Path("./results/vector_rm"), help="Directory for STORM outputs. Default: ./results/vector_rm.")
    parser.add_argument("--do-research", action="store_true", help="Run information-seeking conversation over the vector corpus.")
    parser.add_argument("--do-generate-outline", action="store_true", help="Generate an outline from collected information.")
    parser.add_argument("--do-generate-article", action="store_true", help="Generate the article from outline and references.")
    parser.add_argument("--do-polish-article", action="store_true", help="Polish the generated article.")
    parser.add_argument("--remove-duplicate", action="store_true", help="Ask the polishing stage to remove duplicate article content.")
    parser.add_argument("--max-conv-turn", type=int, default=3, help="Maximum conversational question-asking turns. Default: 3.")
    parser.add_argument("--max-perspective", type=int, default=3, help="Maximum perspectives for question asking. Default: 3.")
    parser.add_argument("--max-search-queries-per-turn", type=int, default=3, help="Maximum search queries per turn. Default: 3.")
    parser.add_argument("--search-top-k", type=int, default=3, help="Top vector chunks per search query. Default: 3.")
    parser.add_argument("--retrieve-top-k", type=int, default=3, help="Top collected references per section during article generation. Default: 3.")
    parser.add_argument("--max-thread-num", type=int, default=3, help="Maximum STORM worker threads. Lower for rate limits. Default: 3.")

    # LiteLLM model settings.
    parser.add_argument("--conv-simulator-model", default="openai/gpt-4o-mini", help="LiteLLM model for conversation simulator. Default: openai/gpt-4o-mini.")
    parser.add_argument("--question-asker-model", default="openai/gpt-4o-mini", help="LiteLLM model for question asker. Default: openai/gpt-4o-mini.")
    parser.add_argument("--outline-gen-model", default="openai/gpt-4o", help="LiteLLM model for outline generation. Default: openai/gpt-4o.")
    parser.add_argument("--article-gen-model", default="openai/gpt-4o", help="LiteLLM model for article generation. Default: openai/gpt-4o.")
    parser.add_argument("--article-polish-model", default="openai/gpt-4o", help="LiteLLM model for article polishing. Default: openai/gpt-4o.")
    parser.add_argument("--conv-simulator-max-tokens", type=int, default=500, help="Max tokens for conversation simulator. Default: 500.")
    parser.add_argument("--question-asker-max-tokens", type=int, default=500, help="Max tokens for question asker. Default: 500.")
    parser.add_argument("--outline-gen-max-tokens", type=int, default=400, help="Max tokens for outline generation. Default: 400.")
    parser.add_argument("--article-gen-max-tokens", type=int, default=700, help="Max tokens for article generation. Default: 700.")
    parser.add_argument("--article-polish-max-tokens", type=int, default=4000, help="Max tokens for article polishing. Default: 4000.")
    parser.add_argument("--temperature", type=float, default=1.0, help="Temperature passed to all LiteLLM models. Default: 1.0.")
    parser.add_argument("--top-p", type=float, default=0.9, help="Top-p passed to all LiteLLM models. Default: 0.9.")
    parser.add_argument("--lm-model-type", choices=("chat", "text"), default="chat", help="LiteLLM model type. Default: chat.")
    parser.add_argument("--lm-api-key-env", help="Optional environment variable name to pass as explicit api_key to all LitellmModel instances.")
    parser.add_argument("--lm-api-base", help="Optional api_base passed to all LitellmModel instances.")
    parser.add_argument("--lm-api-version", help="Optional api_version passed to all LitellmModel instances, useful for Azure-compatible endpoints.")
    parser.add_argument("--secrets-file", type=Path, help="Optional TOML file with top-level environment variables to load before a full run.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    full_run = not args.dry_run and not args.validate_only
    errors, warnings, csv_rows = _validate_args(args, full_run=full_run)

    for message in warnings:
        print(message, file=sys.stderr)
    for message in errors:
        print(message, file=sys.stderr)
    if errors:
        return 1

    if args.dry_run:
        _print_plan(args, csv_rows)
        return 0
    if args.validate_only:
        print("OK: VectorRM STORM configuration validated without embedding, Qdrant, LLM, or network calls.")
        if csv_rows is not None:
            print(f"OK: checked {csv_rows} CSV data row(s).")
        return 0
    return run_full(args)


if __name__ == "__main__":
    raise SystemExit(main())
