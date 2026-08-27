# Workflows: Datagen and Verifier-Backed Evaluation

Start every workflow with a cheap local probe, then decide whether model calls, dataset downloads, or code execution are allowed.

## Deterministic Preflight

1. Run `python scripts/inspect_eval_components.py` from this sub-skill to inspect optional imports and local deterministic components.
2. Confirm package extras for the target area: datagen usually needs model/provider dependencies; datasets need `torch` and `datasets`; benchmarks often need `numpy`, `pandas`, `huggingface_hub`, `rouge`, `tree_sitter`, `ragas`, or retriever dependencies.
3. Validate schemas before generation: `DataPoint(question, final_answer)`, Source2Synth text records with `text` and `source`, collector-specific fields, and benchmark split names.
4. Decide whether generated code can run. If using `PythonVerifier`, require an explicit sandbox policy and short timeouts.

## Chain-of-Thought Data Generation

Use `CoTDataGenerator` when the user has questions and trusted golden answers and wants reasoning traces.

- Create generator and verifier `ChatAgent` instances from the sibling model/agent skills.
- Provide `golden_answers` keyed by exact question text.
- Keep `search_limit` small for smoke runs; increase only after output format and verification behavior are correct.
- Export generated solution trees to JSON after each batch so a failed or interrupted run can resume from completed questions.
- Do not treat CoT generation as deterministic; model temperature, backend retries, and prompt changes can alter traces.

## Self-Instruct and Evol-Instruct

Use self-instruct when starting from seed tasks and generating new instruction/instance pairs.

- Prepare JSONL seed tasks with at least `instruction`; keep a small seed file for a smoke run.
- Configure `InstructionFilter` for length, keyword, punctuation, non-English, and ROUGE similarity checks when deduplication matters.
- Set `num_machine_instructions` and `human_to_machine_ratio` low for tests, then scale in batches.
- Persist `data_output_path` per batch and preserve generated task IDs to avoid regenerating successful rows.

Use evol-instruct when transforming existing prompts.

- Select template methods or strategy names (`DEPTH`, `BREADTH`, or custom template strategies).
- Use `keep_original=True` when you need baseline comparisons.
- Provide a scorer when candidates must be ranked; native tests demonstrate a deterministic dummy scorer and mocked `ChatAgent`.
- Use `num_threads=1` when reproducibility is more important than throughput.

## Source2Synth

Use Source2Synth when the source material is text/code and the target output is multi-hop QA.

- For no-model checks, build `ProcessorConfig(use_ai_model=False, min_length=..., max_length=..., dataset_size=...)` and run `UserDataProcessor.process_text()` or `process_batch()` on a tiny record set.
- For model-backed generation, `use_ai_model=True` creates/uses a multi-hop generator agent; budget model calls and checkpoint each input record.
- Validate output QA records against `MultiHopQA`: question, reasoning steps, answer, supporting facts, and type.
- If records fail preprocessing, inspect text length, type, quality, source metadata, and `min_length`/`max_length` before rerunning generation.

## Dataset and Collector Pipeline

Use collectors to normalize external data, then route normalized records into datasets or generators.

- For Alpaca-style records, validate `instruction`, optional `input`, and `output` before collection.
- For ShareGPT-style conversations, validate role/content pairs and reject unsupported roles early.
- Convert final QA-style examples into `DataPoint` records with `question` and `final_answer` as strings.
- Use `StaticDataset(strict=True)` during development to expose schema problems; relax only for production ingestion with clear logging.

## Tiny Verifier-Backed Benchmark Harness

Use this pattern when the user wants a safe local benchmark without model calls.

1. Build a `StaticDataset` from a small list of `DataPoint` dictionaries.
2. Choose a deterministic verifier: `MathVerifier` for math expressions when `math-verify` is installed, or a custom `BaseVerifier` subclass for exact-match/no-exec checks.
3. Wrap the dataset and verifier in `SingleStepEnv`.
4. Reset with a fixed seed, pass an `Action(llm_response=...)`, and record `(observation, reward, done, info)`.
5. Save a result JSON with question IDs, expected answers, verifier statuses, rewards, and skipped cases.

This pattern exercises CAMEL evaluation contracts while avoiding network, API credentials, model calls, and dataset downloads.

## Task Generation and Evaluation Examples

The repo includes task-generation, evaluation, and environment examples that are useful as reference-only evidence:

- Task generation examples demonstrate `Task` objects and generated subtasks; cross-link to the sibling agent/workforce skill for orchestration.
- Single-agent evaluation examples are model-backed and should be treated as evaluation patterns, not deterministic checks.
- Environment examples show action formatting and reset/step loops; prefer `TicTacToeEnv` for local smoke tests because native tests cover it.
