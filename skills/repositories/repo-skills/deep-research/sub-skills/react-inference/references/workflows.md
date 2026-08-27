# Tongyi DeepResearch ReAct Inference Workflows

This reference summarizes the runtime behavior that future agents need for setup and troubleshooting without reopening the original source tree.

## Configuration Variables

The runtime loads a `.env` file before inference. The canonical example groups variables as follows.

### Multi-GPU / Torch / NCCL

These variables are mainly relevant to local multi-GPU serving: `TORCHDYNAMO_VERBOSE`, `TORCHDYNAMO_DISABLE`, `NCCL_IB_TC`, `NCCL_IB_SL`, `NCCL_IB_GID_INDEX`, `NCCL_SOCKET_IFNAME`, `NCCL_DEBUG`, `NCCL_IB_HCA`, `NCCL_IB_TIMEOUT`, `NCCL_IB_QPS_PER_CONNECTION`, `NCCL_MIN_NCHANNELS`, `NCCL_NET_PLUGIN`, and `GLOO_SOCKET_IFNAME`.

Do not assume the interface names in the example match the user's machine. If vLLM hangs before listening on ports, inspect GPU visibility, network-interface values, NCCL errors, and whether the machine actually has the eight GPUs that the launcher assumes.

### DeepResearch feature flags

The example sets these flags: `QWEN_DOC_PARSER_USE_IDP=false`, `QWEN_IDP_ENABLE_CSI=false`, `NLP_WEB_SEARCH_ONLY_CACHE=false`, `NLP_WEB_SEARCH_ENABLE_READPAGE=false`, `NLP_WEB_SEARCH_ENABLE_SFILTER=false`, `QWEN_SEARCH_ENABLE_CSI=false`, `SPECIAL_CODE_MODE=false`, and `PYTHONDONTWRITEBYTECODE=1`.

Keep them as defaults unless the user has a known service-side reason to change them. They are not substitutes for missing credentials.

### Model and rollout controls

| Variable | Meaning | Source default/example | Strictness |
|---|---|---:|---|
| `MODEL_PATH` | Local model weights path for local vLLM; provider model id when adapting to an OpenAI-compatible hosted model. | placeholder | Strict; launcher exits if empty or placeholder. |
| `DATASET` | JSON or JSONL input file consumed by `run_multi_react.py`. | placeholder | Strict; must be readable and have `.json` or `.jsonl` extension. |
| `OUTPUT_PATH` | Output base passed to `run_multi_react.py --output`. | placeholder | Strict; parent should be writable. |
| `ROLLOUT_COUNT` | Number of independent rollouts per question. | `3` | Must be a positive integer. |
| `TEMPERATURE` | Sampling temperature. | `0.85` | Float; exact value is a quality/cost trade-off. |
| `PRESENCE_PENALTY` | Passed to OpenAI-compatible completion calls. | `1.1` | Float; keep default unless tuning. |
| `MAX_WORKERS` | ThreadPool workers for concurrent question/rollout tasks. | `30` | Positive integer; too high can exceed service QPS. |

Caution: `run_multi_react.py` uses the `DATASET` argument both as the input filepath and as part of the output directory path. Relative dataset names give predictable nested output. Absolute dataset paths can collide with output layout because Python path joining treats an absolute component as the new root.

### External services

| Variable | Used by | Required when |
|---|---|---|
| `SERPER_KEY_ID` | `search` and `google_scholar` via Serper endpoints | The agent may perform web search or scholar search. |
| `JINA_API_KEYS` | `visit` page reading through Jina reader | The agent may visit webpages. |
| `API_KEY`, `API_BASE`, `SUMMARY_MODEL_NAME` | `visit` summarization through an OpenAI-compatible summary model | The agent may summarize webpage content; also relevant when adapting the main model call to a hosted OpenAI-compatible route. |
| `DASHSCOPE_API_KEY`, `DASHSCOPE_API_BASE`, `VIDEO_MODEL_NAME`, `VIDEO_ANALYSIS_MODEL_NAME` | File/video parsing path | The `parse_file` tool may be used. |
| `SANDBOX_FUSION_ENDPOINT` | `PythonInterpreter` | The agent may execute Python code. |
| `USE_IDP`, `IDP_KEY_ID`, `IDP_KEY_SECRET` | Optional IDP document parsing | Advanced file parsing is enabled. |

`SANDBOX_FUSION_ENDPOINT` may contain multiple comma-separated endpoints. The Python tool samples one endpoint per attempt.

## Route A: Local vLLM Inference

The shell launcher performs these steps:

1. Resolves an `.env` file one directory above the launcher.
2. Exits if `.env` is missing and tells the user to copy the example environment file.
3. Exports all values from `.env`.
4. Exits if `MODEL_PATH` is empty or still the example placeholder.
5. Starts eight background vLLM servers with `CUDA_VISIBLE_DEVICES=0` through `7` and ports `6001` through `6008`.
6. Polls `http://localhost:<port>/v1/models` for every port until all are ready or a `6000` second timeout occurs.
7. Changes into the inference working directory.
8. Runs `run_multi_react.py` with values from `.env`:

```bash
python -u run_multi_react.py \
  --dataset "$DATASET" \
  --output "$OUTPUT_PATH" \
  --max_workers "$MAX_WORKERS" \
  --model "$MODEL_PATH" \
  --temperature "$TEMPERATURE" \
  --presence_penalty "$PRESENCE_PENALTY" \
  --total_splits "${WORLD_SIZE:-1}" \
  --worker_split "$(( ${RANK:-0} + 1 ))" \
  --roll_out_count "$ROLLOUT_COUNT"
```

The launcher does not start or validate Serper, Jina, summary API, Dashscope, or SandboxFusion. Missing service credentials surface later as tool failures.

## Route B: OpenRouter or Other OpenAI-Compatible Model API

The README describes hosted usage as a source edit, not a separate turnkey script. For this route:

1. Do not start the eight local vLLM servers.
2. Adapt the ReAct model-call function in the working copy so the OpenAI client uses the provider API key and base URL.
3. Set the model name/id to the hosted Tongyi DeepResearch model id or equivalent provider id.
4. If the provider returns reasoning separately from final content, prepend or concatenate reasoning into `<think>...</think>` before the assistant content so the rest of the ReAct loop still sees the expected format.
5. Keep the same dataset, tool, and rollout validation steps. Hosted model inference does not remove the need for Serper, Jina, summary API, Dashscope, or SandboxFusion when those tools are called.

Use this route for users without local GPUs, but be explicit that tool credentials and provider billing/QPS are still required.

## `run_multi_react.py` Arguments

| Argument | Default | Meaning |
|---|---:|---|
| `--model` | empty | Model path or model id passed through to the agent and tokenizer. |
| `--output` | empty | Output base directory. |
| `--dataset` | `gaia` | Input `.json`/`.jsonl` file; also used in output path construction. |
| `--temperature` | `0.6` | Model sampling temperature. The `.env` example overrides this to `0.85`. |
| `--top_p` | `0.95` | Nucleus sampling. |
| `--presence_penalty` | `1.1` | Presence penalty for model calls. |
| `--max_workers` | `20` | ThreadPool concurrency. The `.env` example uses `30`. |
| `--roll_out_count` | `3` | Number of rollout files to produce. |
| `--total_splits` | `1` | Total distributed data splits. |
| `--worker_split` | `1` | One-based split index. Must be between `1` and `total_splits`. |

Data splitting uses `ceil(total_items / total_splits)`. With splits, output file names include `_split<worker_split>of<total_splits>`.

## Output Layout and Resume Behavior

For a relative dataset argument, the runner creates:

```text
OUTPUT_PATH/
  <basename(MODEL_PATH)>_sglang/
    <DATASET argument>/
      iter1.jsonl
      iter2.jsonl
      iter3.jsonl
```

With distributed splits:

```text
iter1_split1ofN.jsonl
iter2_split1ofN.jsonl
...
```

For each rollout file, the runner reads existing lines and treats any line with a `question` and no `error` field as already processed. Resume matching uses stripped question text, not an item id. Duplicate questions can therefore suppress work unexpectedly.

Each successful output line contains at least:

- `question`
- `answer`
- `messages`
- `prediction`
- `termination`

Error lines add `rollout_idx`, `rollout_id`, and `error`, and set `prediction` to `[Failed]`.

## ReAct Loop

The agent loop uses this pattern:

1. Build a system message from the ReAct system prompt plus the current date, then add the user question.
2. Call the model server for the assigned planning port. Local mode uses `http://127.0.0.1:<planning_port>/v1` with an OpenAI-compatible client and stop strings that prevent generated `<tool_response>` content from continuing.
3. Retry model calls up to ten times on API/network/timeout/empty-content failures with exponential backoff capped at about thirty seconds.
4. Append the assistant content after trimming any accidental `<tool_response>` tail.
5. If the content includes `<tool_call>...</tool_call>`:
   - Python calls are recognized by the word `python` and code is extracted from `<code>...</code>`.
   - Other tool calls are parsed with JSON5 and must contain `name` and `arguments`.
   - Tool output is appended as a user message wrapped in `<tool_response>...</tool_response>`.
6. If the content includes `<answer>...</answer>`, terminate with `termination="answer"` and extract the prediction from the answer tags.
7. Stop after `MAX_LLM_CALL_PER_RUN` calls, default `100`, or after about `150` minutes.
8. Count context tokens with the tokenizer loaded from `MODEL_PATH`. If messages exceed `110 * 1024` tokens, ask the model to stop tool calls and produce a final `<answer>`.
9. If no answer tags are produced, emit `prediction="No answer found."` and a termination reason such as `answer not found` or `exceed available llm calls`.

The default tool map includes `parse_file`, `google_scholar`, `visit`, `search`, and `PythonInterpreter`. The system prompt exposes all five tool signatures.
