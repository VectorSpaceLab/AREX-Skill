# Benchmark Reference

CAMEL benchmark wrappers share the `BaseBenchmark` shape but differ in data sources, splits, optional dependencies, and evaluator behavior. Treat `download()`, `load(force_download=True)`, and `run()` as potentially network- or model-heavy unless you have already staged data and credentials.

## Base Pattern

`BaseBenchmark(name, data_dir, save_to, processes=1)` creates the data directory if needed and exposes:

- `download()`: fetch benchmark assets.
- `load(force_download=False)`: load split data into `_data`.
- `run(agent, on, randomize=False, subset=None, ...)`: evaluate a `ChatAgent` and populate `_results`.
- `train`, `valid`, `test`: split accessors; not every benchmark implements every split.
- `results`: detailed per-example output.

Recommended safe sequence:

1. Instantiate with a temporary or user-provided data/results directory.
2. Check whether local data exists before calling `download()`.
3. Run only tiny subsets first, e.g. `subset=1`, and set `processes=1` while debugging.
4. Save results to JSON/JSONL and include model/backend metadata outside the public skill content.

## Benchmark Matrix

| Benchmark | Main Use | Data/Dependency Constraints | Run Notes |
| --- | --- | --- | --- |
| `GAIABenchmark(data_dir, save_to, retriever=None, processes=1)` | General AI assistant tasks with files, retrieval, and multi-step reasoning. | Downloads `gaia-benchmark/GAIA` from Hugging Face; uses parquet metadata and a retriever. No train split. | `run(agent, on, level, randomize=False, subset=None)` requires `level` and may perform retrieval/tool-like work. |
| `APIBankBenchmark(save_to, processes=1)` | Tool-use conversations and API call/response quality. | Downloads the `api-bank` subdirectory from GitHub and mutates downloaded imports for local use. | `load(level)` accepts levels such as `level-1` and `level-2`; run uses chat histories and API call parsing. |
| `APIBenchBenchmark(data_dir, save_to, processes=1)` | API call generation for HuggingFace, TensorFlow Hub, and Torch Hub. | Downloads Hugging Face dataset and Gorilla eval data; requires tree-sitter parsing dependencies. | Dataset names map to `huggingface`, `tensorflowhub`, and `torchhub`; candidate code is AST-checked. |
| `NexusBenchmark(data_dir, save_to, processes=1)` | Function-calling benchmarks across security, places, climate, and nested/parallel calls. | Downloads multiple Nexusflow Hugging Face datasets; uses pandas/parquet/csv loaders. | `load(dataset_name)` must use a supported key such as `NVDLibrary`, `VirusTotal`, `PlacesAPI`, `ClimateAPI`, `OTX`, `VirusTotal-NestedCalls`, `VirusTotal-ParallelCalls`, or `NVDLibrary-NestedCalls`. |
| `BrowseCompBenchmark(...)` | Browser/content comprehension benchmark. | May require encrypted/source data files and model-based graders. | Treat as heavy and credential-sensitive; use only after data and grading model policy are approved. |
| `RAGBenchBenchmark(processes=1, subset="hotpotqa", split="test")` | RAG context relevancy and faithfulness evaluation. | Loads `rungalileo/ragbench` subsets; metric evaluation may require `ragas`, `sklearn`, and model-backed metrics. | Local helpers `rmse`, `auroc`, and `ragas_calculate_metrics` can be used once prediction fields exist. |

## RAGBench Helpers

- `annotate_dataset(dataset, context_call, answer_call)` adds `contexts` and/or `answer` fields by mapping user callbacks.
- `ragas_calculate_metrics(dataset, pred_context_relevance_field, pred_faithfulness_field, ...)` computes RMSE and AUROC from existing numeric prediction fields and ground-truth fields.
- `ragas_evaluate_dataset(dataset, contexts_field_name, answer_field_name, metrics_to_evaluate=None)` invokes RAGAS metrics and may require model/config setup.

## When To Avoid Native Benchmark Runs

Avoid direct benchmark runs when:

- The user did not approve downloads from Hugging Face or GitHub.
- Required API keys, model endpoints, browser services, retrievers, or grading models are missing.
- The requested check is only about local CAMEL wiring; use verifier/environment smoke tests instead.
- Dataset licenses, credentials, or cached private files are unclear.
- Results would be too slow or expensive without subset limits and checkpointing.

## Reporting Benchmark Results

For any benchmark run, record:

- CAMEL package version and benchmark class.
- Dataset name, split, level, subset size, and whether data was downloaded or pre-staged.
- Agent/model/backend configuration and credential source category, without exposing secrets.
- Wall time, retries, skipped samples, failed samples, and final metrics.
- Reproduction command and output file path chosen by the user.
