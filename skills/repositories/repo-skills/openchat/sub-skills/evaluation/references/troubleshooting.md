# Evaluation Troubleshooting

Use this guide to separate quick parser checks from expensive benchmark failures. Parser checks do not load a model, call an API, or prove benchmark accuracy; benchmark runs may require credentials, network access, GPU memory, model weights, and a correctly shaped data directory.

## Fast preflight checks

| Check | Command | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Upstream CLI import/help | `scripts/run_eval.sh --help` | The installed `ochat.evaluation.run_eval` module and its dependencies can at least load. | Model weights, data layout, API credentials, or GPU capacity. |
| Matcher smoke tests | `scripts/check_answer_matchers.py` | Selected answer matcher functions can parse representative multiple-choice, GSM8K, and HumanEval responses. | Benchmark correctness or HumanEval execution correctness. |
| EvalPlus conversion help | `scripts/convert_to_evalplus.py --help` | The bundled converter script is available. | That result JSON contains `coding/humaneval` rows. |

If `scripts/check_answer_matchers.py` cannot import OpenChat because optional evaluation dependencies are missing, install the package with its evaluation/runtime dependencies in the active Python environment. The script also has a `--standalone` mode for validating the bundled smoke-test logic only; do not treat standalone mode as proof that the installed OpenChat matchers are importable.

## Data and matcher problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Assertion failure for unknown task type | JSONL files are not under one of the supported `task_type` directories. | Reorganize data under `zs/...`, `fs_cothub/...`, or `coding/humaneval` as documented in `eval-data-layout.md`. |
| No questions are evaluated | `--eval-sets` prefix does not match any `task_name`, or the data path has no JSONL files. | Print/find the local data directory and select prefixes like `fs_cothub/mmlu`, `zs/gpqa`, or `coding`. |
| High `is_matched=false` rate | Prompt style does not produce the answer phrase expected by the matcher. | Align task prompts with matcher patterns: `answer is`, `The answer is`, boxed math answers, or `The correct answer is`. |
| GSM8K answer is the wrong number | Matcher returns the last decimal-looking number in the response. | Ensure prompts tell the model to end with the final answer and avoid trailing unrelated numbers. |
| MMLU or BBH multiple-choice rows default to `(C)` or unmatched text | The model did not emit the expected option token shape. | Make the prompt request final choices as `(A)`, `(B)`, `(C)`, `(D)` for COT Hub MMLU/BBH. |
| `fs_cothub/math` fails before generation or matching | `_metadata.solution` is missing or lacks a boxed/fboxed final answer. | Add `_metadata.solution` with the ground truth answer in `\boxed{...}` or `\fbox{...}` form. |
| HumanEval conversion emits no samples | The result JSON has no rows with `task_type == "coding/humaneval"`, or the matcher did not produce `answer` objects. | Run/evaluate a `coding/humaneval` data prefix first, inspect rows for `answer.task_id` and `answer.completion`, then rerun conversion. |

## Local vLLM path problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `openchat.json` or model config lookup fails | `--model-type` was omitted and the model repository/cache lacks OpenChat metadata. | Provide `--model-type`, for example `openchat_3.6` or `openchat_v3.2_mistral`. |
| CUDA/vLLM import or initialization failure | Active environment lacks compatible CUDA, vLLM, PyTorch, or GPU driver support. | Verify the installed runtime, then retry with a smaller model or a compatible vLLM/CUDA stack. |
| Out of memory during model load or generation | Model weights exceed available GPU memory, context length is large, or tensor parallel degree is wrong. | Use a smaller model, reduce competing GPU load, or set `--tensor-parallel-size` to match available GPUs. |
| Bad outputs after using the wrong `--condition` | The model was prompted with a condition different from its expected OpenChat mode. | Use `GPT4 Correct` for default OpenChat 3.5/3.6-style evaluation and `Math Correct` for math-mode evaluation when appropriate; route template details to prompting. |
| Need an OpenAI-compatible server instead of direct vLLM | `run_eval` local path instantiates vLLM directly, not the OpenChat API server. | Route API server startup, ports, keys, and deployment flags to the serving sub-skill. |

## OpenAI API path problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Authentication error | Missing or invalid API key in the active environment. | Set the expected OpenAI-compatible API credentials before running. |
| Rate limit, internal server error, or connection errors | API service throttling or transient network failure. | Lower `--parallel`; the harness also retries and halves parallelism when progress stalls. |
| Condition/system prompt appears ignored | The OpenAI path sends only a single user message per question. | Put all required instructions in the `question` text itself, or use the local OpenChat path for condition/system templating. |
| Unexpected API endpoint | The default OpenAI client settings are used. | Configure the OpenAI-compatible client environment variables expected by the installed `openai` package before running. |

## Output and resume problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Output path directory does not exist | Custom `--output-file` parent is absent. | The harness creates the parent directory, but ensure the path is writable. |
| Default output name is surprising | The default path uses the data directory's parent, model basename, and condition string. | Pass an explicit `--output-file` for reproducible paths. |
| Resume regenerates too much or too little | `--continue-from` only skips rows with non-empty `response`. | Inspect the continuation JSON and clear only the rows that should be regenerated. |
| `is_correct` is false for HumanEval despite valid code | OpenChat does not execute HumanEval tests; it only extracts samples. | Convert with `scripts/convert_to_evalplus.py` and run EvalPlus in a sandbox. |

## Benchmark orchestration caveats

MT-Bench, Vicuna Bench, AlpacaEval, and checkpoint-sweeping orchestration are outside this runtime sub-skill. They require external benchmark repositories, service lifecycle management, and often paid judge APIs. Treat repository orchestration scripts for those workflows as reference evidence only, and ask the user for explicit benchmark repository paths, credentials, and runtime budget before attempting them elsewhere.
