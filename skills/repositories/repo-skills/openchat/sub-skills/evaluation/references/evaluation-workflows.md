# OpenChat Evaluation Workflows

This reference covers OpenChat's installed benchmark harness at `python -m ochat.evaluation.run_eval`, its two completion paths, result fields, and HumanEval conversion. It intentionally does not cover prompt-template internals or API-server deployment; route those to the sibling prompting and serving sub-skills.

## Quick path selection

| Goal | Use this path | Main requirements | Notes |
| --- | --- | --- | --- |
| Evaluate an OpenChat or other local Hugging Face model | Local vLLM path | Installed `ochat`, vLLM, model weights, compatible GPU memory | Any `--model` value that does **not** start with `gpt-3.5-turbo` or `gpt-4` uses this path. |
| Evaluate GPT-3.5/GPT-4 as a judge or baseline | OpenAI API path | OpenAI-compatible credentials, network access, quota | Any `--model` beginning with `gpt-3.5-turbo` or `gpt-4` uses `openai.AsyncOpenAI`. |
| Convert generated HumanEval samples | EvalPlus conversion | Existing OpenChat result JSON with `coding/humaneval` rows | Conversion is local and does not execute code. Use EvalPlus separately for pass/fail. |
| Check answer parsing only | Matcher smoke checks | Installed `ochat` for actual matchers | `scripts/check_answer_matchers.py` is fast and does not run benchmarks. |

## `run_eval` CLI behavior

Use the bundled wrapper so future agents do not need to remember the module path:

```bash
scripts/run_eval.sh --help
```

Important arguments accepted by the upstream module:

| Argument | Default | Applies to | Meaning |
| --- | --- | --- | --- |
| `--model` | `None` | both paths | Model identifier. Prefixes `gpt-3.5-turbo` and `gpt-4` select the OpenAI API path; other values select local vLLM. |
| `--condition` | empty string | local vLLM | C-RLFT condition inserted into OpenChat conversation tokenization, such as `GPT4 Correct` or `Math Correct`. It is printed but not applied by the OpenAI API path. |
| `--system-msg` | empty string | local vLLM | System message passed into the local conversation template. It is printed but not applied by the OpenAI API path. |
| `--model-type` | `None` | local vLLM | OpenChat model config key. If omitted, the harness tries to read `openchat.json` from the model repository/cache. Supplying it avoids a metadata miss. |
| `--data-path` | `ochat/evaluation/eval_data` | fresh runs | Directory recursively scanned for `*.jsonl`; do not rely on this default existing in future workspaces. |
| `--eval-sets` | empty list | fresh runs | Prefix filters over task names such as `fs_cothub/mmlu`, `fs_cothub/mmlu/abstract_algebra`, `coding`, or `zs/gpqa`. Empty means all supported files under `--data-path`. |
| `--continue-from` | `None` | both paths | Load an existing result JSON and only complete rows whose `response` is empty. The data directory is not re-read. |
| `--output-file` | derived | both paths | Destination JSON. If omitted, the harness writes beside the data directory under an `eval_results` folder using the model basename and condition. |
| `--parallel` | `16` | OpenAI API path | Initial number of concurrent API workers. Retry cycles reduce parallelism if progress stalls. |
| `--tensor-parallel-size` | `1` | local vLLM | Tensor parallel degree passed to the vLLM `LLM` constructor. |

Supported installed model-type keys observed for this OpenChat version:

| Model type key | Notes |
| --- | --- |
| `openchat_3.6` | Llama 3 OpenChat 3.6 template, 8192 context. |
| `openchat_v3.2` | Earlier OpenChat V3.2 template, 4096 context. |
| `openchat_v3.2_mistral` | Mistral OpenChat 3.5-family template; serving alias `openchat_3.5`. |
| `openchat_v3.2_gemma_new` | Gemma OpenChat 3.5-family template; serving alias `openchat_3.5_gemma_new`. |
| `chatml_8192` | ChatML-style template. |
| `zephyr_mistral` | Zephyr/Mistral-style template. |
| `gemma_it` | Gemma instruction template. |
| `llama3_instruct` | Llama 3 instruct template. |

For template behavior, route to the prompting sub-skill.

## Local vLLM benchmark path

Use this when evaluating OpenChat or another local model through vLLM directly:

```bash
scripts/run_eval.sh \
  --model openchat/openchat-3.6-8b-20240522 \
  --model-type openchat_3.6 \
  --condition "GPT4 Correct" \
  --data-path ./eval_data \
  --eval-sets fs_cothub/mmlu fs_cothub/gsm8k \
  --output-file ./eval_results/openchat36_reasoning.json \
  --tensor-parallel-size 1
```

What the harness does internally:

1. Loads `MODEL_CONFIG_MAP[--model-type]`, or reads `openchat.json` from the model repo/cache when `--model-type` is omitted.
2. Builds an OpenChat `Conversation` per unanswered question with one user message and an empty assistant turn.
3. Applies the selected conversation template using `--condition` and `--system-msg`.
4. Starts a local vLLM `LLM` with `max_num_batched_tokens` and `max_model_len` set to the model config context length, plus the requested `--tensor-parallel-size`.
5. Generates deterministically with temperature `0`, OpenChat EOT stop tokens, and `ignore_eos=True`.
6. Strips one leading space from each generated response, then applies the task-family answer matcher.

Use explicit `--model-type` when the model directory or remote repository does not include an `openchat.json` metadata file.

## OpenAI API benchmark path

Use this when the selected model name starts with `gpt-3.5-turbo` or `gpt-4`:

```bash
OPENAI_API_KEY=... \
scripts/run_eval.sh \
  --model gpt-4-turbo \
  --data-path ./eval_data \
  --eval-sets zs/gpqa \
  --output-file ./eval_results/gpt4_gpqa.json \
  --parallel 8
```

The OpenAI path sends each question as a single user message with temperature `0`. In this path, OpenChat's `--condition`, `--system-msg`, `--model-type`, and `--tensor-parallel-size` are not used to build the prompt. The async client retries rate limits, internal server errors, and connection errors with exponential backoff; if a retry cycle makes no progress, the harness halves `--parallel` until it reaches one worker.

For OpenAI-compatible local API-server deployment, use the serving sub-skill rather than this benchmark harness.

## Resume or continue a partial run

`--continue-from` loads a previously written OpenChat result JSON. Rows with non-empty `response` are skipped for generation; rows with empty `response` are regenerated. Matchers are re-applied to all rows before the output file is written.

```bash
scripts/run_eval.sh \
  --model openchat/openchat-3.6-8b-20240522 \
  --model-type openchat_3.6 \
  --condition "GPT4 Correct" \
  --continue-from ./eval_results/openchat36_reasoning.partial.json \
  --output-file ./eval_results/openchat36_reasoning.resumed.json
```

A continuation file must already contain the fields the harness expects, especially `question`, `label`, `task_name`, `task_type`, and `response`.

## Output JSON fields

Each output file is a JSON array. Each row includes the input item fields, plus fields added by OpenChat:

| Field | Meaning |
| --- | --- |
| `task_name` | Relative task name derived from the JSONL path below the data directory, without the `.jsonl` suffix. |
| `task_type` | Directory portion of `task_name`; must be one of the supported matcher keys. |
| `response` | Raw generated text from local vLLM or the OpenAI API. |
| `is_matched` | Whether the task-family parser recognized an answer form. This is parser success, not benchmark correctness. |
| `answer` | Normalized matcher output. Type varies by task: option string, free-form string, boolean for `fs_cothub/math`, or a HumanEval sample object. |
| `is_correct` | Computed as `answer in label`, with exceptions mapped to `False`. For HumanEval, use EvalPlus execution instead of this field. |

Inspect unmatched rows first; high unmatched rates often indicate a prompt/condition mismatch or an incompatible data layout.

## HumanEval and EvalPlus conversion

OpenChat's `coding/humaneval` matcher extracts a completion object:

```json
{"task_id": "HumanEval/0", "completion": "...python code..."}
```

Convert result JSON files into EvalPlus sample JSONL files with the bundled converter:

```bash
scripts/convert_to_evalplus.py \
  --results-path ./eval_results \
  --output-path ./evalplus_codegen
```

The converter mirrors OpenChat's source behavior: for every result file, it writes one JSONL file containing `answer` objects from rows whose `task_type` is `coding/humaneval`. It does not execute code, install EvalPlus, or sandbox generated programs. Run EvalPlus separately in an environment appropriate for executing untrusted code.

## Reference-only orchestration

The repository also contains `conv_eval.py`-style orchestration for checkpoint discovery, MT-Bench, Vicuna Bench, and AlpacaEval. Treat that evidence as reference-only in this skill because it depends on external benchmark repositories, starts long-running API services, and contains environment-specific defaults. If a user requests those benchmarks, explain the external dependencies and route API-server setup to serving before attempting any run.
