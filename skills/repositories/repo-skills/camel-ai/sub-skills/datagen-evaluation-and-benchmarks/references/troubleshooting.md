# Troubleshooting: Datagen, Evaluation, and Benchmarks

## Optional Dependencies and Imports

Symptoms: importing `camel.datagen`, `camel.benchmarks`, `camel.datasets`, `camel.verifiers`, or `camel.environments` fails with missing packages such as `openai`, `torch`, `datasets`, `numpy`, `pandas`, `math_verify`, `tree_sitter`, `huggingface_hub`, `ragas`, or game/environment libraries.

Actions:

- Install only the optional dependencies needed for the requested workflow; do not install all extras by default.
- Run `scripts/inspect_eval_components.py` to separate import availability from deterministic local component behavior.
- If model provider imports are missing, route provider setup to the sibling model/backend skill instead of patching datagen code.
- If an import fails only for benchmark-specific extras, still use source schemas and local deterministic harnesses where possible.

## Model Call Cost and Long Runs

Symptoms: self-instruct, CoT, evol-instruct, Source2Synth, or benchmark evaluation is slow, expensive, rate-limited, or non-reproducible.

Actions:

- Start with one or two records, small `search_limit`, small `num_machine_instructions`, and `processes=1`.
- Set deterministic seeds where available, but do not promise identical outputs for model-backed generations.
- Checkpoint per input record with status: `pending`, `running`, `succeeded`, `failed`, `skipped`.
- Persist raw model outputs, parsed outputs, verifier outcomes, and retry counts separately so failed parsing can be retried without regenerating successful records.
- Resume by reading the checkpoint and rerunning only failed or pending records.

## Benchmark Datasets and Credentials

Symptoms: `download()` fails, `load()` cannot find metadata, Hugging Face access is denied, GitHub downloads fail, retrievers have empty stores, or benchmark runs ask for API keys.

Actions:

- Confirm whether downloads are allowed before calling `download()` or `load(force_download=True)`.
- For GAIA, check that the expected `2023/validation` and `2023/test` directories and metadata parquet files exist.
- For APIBank, verify the `api_bank` folder and requested `level` files exist after download.
- For APIBench and Nexus, verify supported dataset names before loading.
- For BrowseComp and RAGBench, confirm grading/retrieval/model dependencies before running full evaluations.
- Use tiny subsets and write explicit skip reasons when credentials or datasets are unavailable.

## Verifier and Extractor Configuration

Symptoms: verifier returns `ERROR`, extracted answer is empty, math expressions do not parse, Python output mismatches despite looking equivalent, or timeouts occur.

Actions:

- Add the right `BaseExtractor` pipeline before verification; use `BoxedStrategy` for `\boxed{...}` math and Python literal strategies for list/dict/set/tuple normalization.
- For `MathVerifier`, install the optional `math-verify` dependency and tune `float_rounding`, `numeric_precision`, and `enable_wrapping`.
- For `PythonVerifier`, set short `timeout`, minimal `required_packages`, and `float_tolerance` when comparing numeric structures.
- Always inspect `VerificationResult.status`, `error_message`, and `metadata`; do not treat non-empty `result` as success.
- Call `cleanup()` in `finally` to remove verifier resources.

## Python Verifier Safety

`PythonVerifier` executes supplied Python in a generated environment. That is useful for code-answer tasks but unsafe for arbitrary untrusted outputs.

Use it only when:

- The caller approves code execution.
- Required packages are minimal and trusted.
- Timeouts are short.
- Network and filesystem access are externally sandboxed if the generated code is untrusted.
- Outputs and exceptions are captured as data, not blindly executed in the main process.

For untrusted synthetic data checks, prefer exact-match, math, schema, or AST-only validation.

## Dataset Schema and Column Failures

Symptoms: `StaticDataset` skips rows, collectors drop records, Source2Synth returns no examples, or `DataPoint` validation fails.

Actions:

- Ensure `DataPoint` fields `question` and `final_answer` are strings.
- Use `StaticDataset(strict=True)` while debugging to fail on the first invalid row.
- For JSON/JSONL input, verify file extension, JSON validity, and one record per line for JSONL.
- For Source2Synth, check text type, `min_length`, `max_length`, `complexity_threshold`, and source metadata.
- For collectors, validate source-specific fields before conversion and record row IDs for skipped samples.

## Environment Reset and Step Contracts

Symptoms: `reset()` fails, `step()` raises because setup was skipped, actions are marked illegal, or episode state leaks between runs.

Actions:

- Use async lifecycle: `await env.setup()`, `await env.reset()`, `await env.step(Action(...))`, `await env.close()`.
- For `SingleStepEnv`, finish all states in a batch before calling `reset()` again.
- For `TicTacToeEnv`, wrap moves as `<Action>1</Action>` through `<Action>9</Action>`; bare numbers can fail extraction.
- Check `done` before sending another action; reset after terminal states.
- Read `info` and `rewards_dict` for details instead of relying only on total reward.
