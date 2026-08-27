# MiniMind inference-serving troubleshooting

Use this matrix when local inference, serving, tool calls, thinking output, or conversion fails.

## Quick triage order

1. Classify the model artifact:

```bash
python scripts/check_model_artifacts.py --model-dir MODEL_DIR --expect auto --json
python scripts/check_model_artifacts.py --weights-dir WEIGHTS_DIR --tokenizer-dir TOKENIZER_DIR --expect raw-torch --json
```

2. Verify dependency imports for the chosen surface:

```bash
python - <<'PY'
mods = ["torch", "transformers", "pydantic", "fastapi", "uvicorn", "openai", "streamlit"]
for name in mods:
    try:
        __import__(name)
        print(f"OK {name}")
    except Exception as exc:
        print(f"MISSING {name}: {exc}")
PY
```

3. Debug parser behavior independently of model quality:

```bash
python scripts/toolcall_smoke.py --execute --json
```

4. Probe API behavior with a single request:

```bash
python scripts/openai_chat_once.py --base-url http://127.0.0.1:8998/v1 --model minimind --prompt "ping" --no-stream
```

## Failure matrix

| Symptom | Likely cause | Diagnostic | Fix |
| --- | --- | --- | --- |
| `config.json` not found | Passing raw checkpoint directory as a Transformers model directory | `scripts/check_model_artifacts.py --model-dir MODEL_DIR --expect transformers` | Use raw-torch workflow or convert raw `.pth` to Transformers. |
| `.pth` checkpoint not found | Wrong `--weight`, hidden size, MoE suffix, or weights directory | `scripts/check_model_artifacts.py --weights-dir WEIGHTS_DIR --weight full_sft --hidden-size 768 --moe/--no-moe` | Match filename pattern `<weight>_<hidden_size>[_moe].pth`; set `--moe` for MoE checkpoints. |
| LoRA file not found | Inconsistent LoRA layout | Artifact checker reports both candidate paths | Try `WEIGHTS_DIR/<lora>_<hidden>.pth` and `WEIGHTS_DIR/lora/<lora>_<hidden>.pth`; merge before export. |
| Model loads as raw when a Transformers directory was intended | Ambiguous path naming; evidence used substring `model` to choose raw path | Check whether `MODEL_DIR` has `config.json` and weight files | Prefer explicit wrapper flags; do not infer artifact type from a path containing `model`. |
| `ModuleNotFoundError: fastapi` or `uvicorn` | API server deps absent from minimal requirements | import probe above | Install `fastapi uvicorn`; these are server-only deps. |
| `ModuleNotFoundError: openai` | Client probe dependency missing | import probe above | Install `openai` or use `curl`. |
| `ModuleNotFoundError: streamlit` | WebUI dependency missing | import probe above | Install `streamlit`; avoid WebUI for non-interactive automation. |
| `Qwen3Config` or `Qwen3MoeConfig` import fails | Transformers too old or incompatible | `python -c 'from transformers import Qwen3Config, Qwen3ForCausalLM, Qwen3MoeConfig, Qwen3MoeForCausalLM'` | Use a Transformers version that includes Qwen3/Qwen3MoE classes; inspection evidence confirmed availability in `4.57.6`. |
| `AutoModelForCausalLM` refuses custom MiniMind directory | MiniMind custom export requires remote/custom code trust | Check `config.json` for `model_type: minimind` or `auto_map` | Use `trust_remote_code=True`, install MiniMind classes, or export to Qwen3-compatible format. |
| `RuntimeError` around CPU half operations | Model was forced to `.half()` on CPU | Check device and dtype | On CPU, load/generate with float32 or `torch_dtype=torch.float32`; use `.half()` only on CUDA-capable devices. |
| CUDA out of memory | Model/context too large, `max_tokens` too high, or server concurrent load | Reduce `max_tokens`, context, batch/concurrency | Use smaller model, quantization, vLLM memory controls, or CPU only for tiny probes. |
| CUDA not available but expected | Host/backend mismatch | `python -c 'import torch; print(torch.cuda.is_available())'` | Select `--device cpu` for smoke only, install CUDA build intentionally, or move to a GPU host. |
| Output includes literal `<think>` tags in `content` | Parser not applied or third-party server does not split reasoning | Test with `scripts/toolcall_smoke.py --text TEXT --json` | Post-process tags into `reasoning_content`, or use the MiniMind-compatible parser contract. |
| `reasoning_content` never appears | `open_thinking` not enabled, model did not close `</think>`, or server/client ignores custom field | Send `extra_body={"chat_template_kwargs":{"open_thinking": true}}`; inspect stream deltas | Enable top-level or template-level switch; handle dangling `</think>`; do not require reasoning for every response. |
| Tool call is plain text, not `tool_calls` | Runtime preserves tags but does not parse OpenAI tool objects | Look for `<tool_call>...</tool_call>` in content | Parse tags with the MiniMind parser; third-party engines may need a wrapper. |
| Tool call JSON ignored | Malformed JSON inside `<tool_call>` | `python scripts/toolcall_smoke.py --text '...' --json` | Ensure double-quoted JSON object with `name` and object-valued `arguments`; avoid Python dict syntax or trailing comments. |
| Tool arguments arrive as a JSON string | OpenAI function-call convention | Inspect `message.tool_calls[].function.arguments` | `json.loads(arguments)` before executing the tool. |
| Tool loop never terminates | Model keeps issuing calls, observation not appended correctly, or task impossible | Count tool turns and inspect messages | Append `tool` role observations with the matching `tool_call_id`; enforce a strict loop cap. |
| Thinking + tool calling is unstable | Known data limitation for combined reasoning and tool-call samples | Compare `open_thinking=false` tool request vs `true` | Disable explicit thinking during tool turns when reliability matters. |
| Chat template error on `tools` or `open_thinking` | Wrong tokenizer or template missing MiniMind tags | Artifact checker reports chat template features | Use MiniMind tokenizer files; export tokenizer with the model; do not substitute a generic tokenizer. |
| `messages[0]` template error | Empty message list or missing expected first message in custom wrapper | Reproduce with one user message | Always send at least one user message; include system first only when needed. |
| WebUI says no models found | UI scan cannot see a weight file in scanned child directories | Artifact checker against selected model path | Use an explicit model path or place a Transformers-format directory where the UI scans. |
| vLLM refuses model | Export is MiniMind custom format or unsupported architecture | Check `model_type` and Qwen3 class availability | Prefer Qwen3-compatible export and start with `--model-impl transformers`. |
| llama.cpp converter rejects tokenizer | Tokenizer pre-tokenizer not recognized | Converter error references vocab/pre-tokenizer | Configure a compatible fallback such as `qwen2`, then validate generated GGUF. |
| Ollama responds but tool calls are not structured | Ollama template preserves text tags but not OpenAI tool objects | Inspect raw generated text | Include MiniMind tag template and parse `<tool_call>` externally if structured calls are required. |
| Streaming client hangs | Client waits for `[DONE]` that lightweight server does not emit | Inspect raw SSE stream | Treat final chunk with empty delta and `finish_reason` as terminal, or add adapter that emits `[DONE]`. |
| Non-streaming response lacks `usage` | Lightweight server does not emit full OpenAI metadata | Inspect JSON | Do not require `usage`; compute token counts separately if needed. |
| `finish_reason` is `tool_calls` with empty content | Expected when assistant only requests tool execution | Inspect `message.tool_calls` | Execute tools, append observations, and call again. |
| Long-context request degrades or OOMs | `max_tokens`/tokenizer max length exceeds trained capability or memory | Reduce prompt and generation length | RoPE scaling only helps positional extrapolation; validate task quality. |

## Chat-template mismatch checklist

A valid MiniMind tokenizer configuration for inference-serving should support:

- BOS/EOS markers similar to `<|im_start|>` and `<|im_end|>`.
- A `chat_template` that accepts `tools=...` and `open_thinking=...`.
- Tool instructions wrapped in `<tools>...</tools>`.
- Assistant tool calls rendered as `<tool_call>{...}</tool_call>`.
- Tool observations rendered as `<tool_response>{...}</tool_response>`.
- Assistant thinking rendered as `<think>...</think>`.

Use:

```bash
python scripts/check_model_artifacts.py --model-dir MODEL_DIR --expect transformers --json
```

and inspect `chat_template_features` in the output.

## Malformed tool-call examples

Bad: Python dict syntax and unquoted key.

```text
<tool_call>{name: calculate_math, arguments: {'expression': '2+2'}}</tool_call>
```

Good: JSON object with string `name` and object `arguments`.

```text
<tool_call>{"name":"calculate_math","arguments":{"expression":"2+2"}}</tool_call>
```

Smoke:

```bash
python scripts/toolcall_smoke.py --text '<tool_call>{"name":"calculate_math","arguments":{"expression":"2+2"}}</tool_call>' --execute --json
```

## Dependency matrix by surface

| Surface | Needed packages | Not needed |
| --- | --- | --- |
| Artifact checking | Python standard library; optional `transformers` for class import check | torch model load, network downloads |
| Tool parser smoke | Python standard library | model weights, torch, transformers |
| Transformers local inference | `torch`, `transformers` | FastAPI/Uvicorn unless serving |
| Raw PyTorch inference | `torch`, `transformers`, MiniMind model modules | FastAPI/Uvicorn unless serving |
| OpenAI-compatible server | `fastapi`, `uvicorn`, `pydantic`, `torch`, `transformers` | Streamlit |
| OpenAI client probe | `openai` | model modules on client side |
| Streamlit WebUI | `streamlit`, `torch`, `transformers` | FastAPI/Uvicorn unless it talks to a separate server |
| vLLM/SGLang | Engine-specific CUDA stack and Transformers model dir | Raw `.pth` without conversion |
| llama.cpp/Ollama | GGUF artifacts and engine binaries | Python model modules at inference time |

## Hard-case usability tests to add later

1. **Streaming thinking plus delayed tool call:** mock an SSE stream where reasoning chunks arrive, final content contains a valid `<tool_call>`, and the final chunk has `finish_reason="tool_calls"`; assert the client collects reasoning separately and still executes the tool.
2. **LoRA export ambiguity:** provide a raw base checkpoint path, two possible LoRA locations, and a Transformers export target; assert the agent validates dimensions, picks merge-before-export for third-party serving, and refuses to call vLLM on the raw `.pth`.
