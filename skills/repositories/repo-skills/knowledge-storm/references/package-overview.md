# knowledge-storm package overview

This reference is for operating the public `knowledge-storm` package without relying on the source checkout. Use it to choose the right workflow before opening a sub-skill.

## Package identity

- Distribution name: `knowledge-storm`.
- Import package: `knowledge_storm`.
- Public project: STORM, "Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking".
- Python support in package metadata: `>=3.10`; the repository CI evidence uses Python 3.11.
- Source metadata version observed during extraction: `setup.py` declares `1.1.1`; `knowledge_storm.__version__` reports `1.1.0`. Treat this as a staleness/version-warning signal, not an import failure.

## Core concepts

STORM and Co-STORM both curate knowledge by combining LLM calls with retrieval. They differ in interaction style:

| Workflow | Primary API | Interaction model | Main outputs | Use when |
| --- | --- | --- | --- | --- |
| STORM Wiki | `STORMWikiRunner` | Batch pipeline: research -> outline -> article -> polish. | `conversation_log.json`, outline/article text files, `run_config.json`, `llm_call_history.jsonl`. | The task is to generate or resume a Wikipedia-like article about one topic. |
| VectorRM corpus STORM | `VectorRM`, `QdrantVectorStoreManager`, `STORMWikiRunner` | Batch article pipeline grounded on a user CSV/local corpus instead of internet search. | Qdrant collection plus normal STORM article outputs. | The user has a CSV/local corpus and wants retrieval constrained to it. |
| Co-STORM | `CoStormRunner` | Collaborative discourse: warm start, user/system turns, mind map, report. | `report.md`, `report.txt`, `instance_dump.json`, `log.json`. | The user wants human-in-the-loop knowledge curation or discourse state/logging. |

## Major public modules

- `knowledge_storm.lm`: `LitellmModel` plus legacy model wrappers. Prefer `LitellmModel` for new workflows.
- `knowledge_storm.rm`: internet retrievers such as `BingSearch`, `YouRM`, `BraveRM`, `SerperRM`, `DuckDuckGoSearchRM`, `TavilySearchRM`, `SearXNG`, `AzureAISearch`, and corpus retriever `VectorRM`.
- `knowledge_storm.storm_wiki.engine`: `STORMWikiLMConfigs`, `STORMWikiRunnerArguments`, `STORMWikiRunner`.
- `knowledge_storm.collaborative_storm.engine`: `CollaborativeStormLMConfigs`, `RunnerArgument`, `CoStormRunner`.
- `knowledge_storm.logging_wrapper`: `LoggingWrapper` for Co-STORM pipeline-stage logs.
- `knowledge_storm.encoder`: `Encoder`, used by Co-STORM mind-map operations and configured through embedding environment variables.
- `knowledge_storm.utils`: Qdrant vector-store helpers, API-key TOML loading in native examples, and web-page utilities.

## Sub-skill boundaries

- Read `sub-skills/storm-wiki/` for STORM internet-search article generation, stage resume, output inspection, search-provider switching, and demo-light setup patterns.
- Read `sub-skills/vector-corpus/` for CSV schema checks, Kaggle arXiv conversion, offline/online Qdrant setup, `VectorRM`, and corpus-grounded STORM runs.
- Read `sub-skills/co-storm/` for collaborative warm start, `step(...)`, mind maps, final report generation, `LoggingWrapper`, state serialization, and Co-STORM output inspection.

## Useful bundled scripts

- `scripts/check_knowledge_storm_runtime.py`: package/runtime import and environment-status checker.
- `sub-skills/storm-wiki/scripts/run_storm_wiki.py`: safe STORM Wiki CLI with `--dry-run` and stage flags.
- `sub-skills/vector-corpus/scripts/validate_vector_corpus_csv.py`: standard-library CSV schema validation.
- `sub-skills/vector-corpus/scripts/process_kaggle_arxiv_abstract_dataset.py`: deterministic CSV conversion helper.
- `sub-skills/vector-corpus/scripts/run_storm_wiki_with_vector_rm.py`: corpus-grounded STORM helper with `--dry-run` and `--validate-only` modes.
- `sub-skills/co-storm/scripts/run_costorm.py`: noninteractive Co-STORM helper with `--dry-run`, turn count, user utterance, and state/log outputs.

## Operational defaults

- Start with small search/query/thread counts and low turn counts. STORM and Co-STORM can make many LLM and search calls.
- Use `LitellmModel` model strings such as `openai/gpt-4o`, `openai/gpt-4o-mini`, or `azure/<deployment-name>` rather than legacy provider-specific wrappers.
- Prefer `--dry-run` or `--validate-only` modes before full runs. These modes are designed to avoid package imports, model calls, network requests, and vector-store writes where possible.
- Keep secrets in environment variables or an explicit TOML file consumed by bundled helpers. Do not write keys into run artifacts.
