# Generation, Chat, and Endpoint Workflows

This reference covers inference-time workflows only. It assumes the user already has either a Hugging Face model folder, a Hugging Face Hub model id, or an endpoint. Producing the model by training belongs to `training-finetuning`.

## Choose the workflow

| User intent | Use | Required artifact | Side effects |
|---|---|---|---|
| Generate completions from prompts | Hugging Face generation helper or equivalent Transformers code | `name_or_path` as local HF folder or Hub id | May load large weights; Hub ids may download unless cached |
| Multi-turn terminal chat | Hugging Face chat helper or equivalent Transformers chat-template loop | chat-tuned model with tokenizer chat template | Loads weights; interactive stdin/stdout |
| Convert Composer checkpoint to HF | Composer-to-HF conversion | full Composer checkpoint, not just model weights | Writes HF folder; optional object-store/Hub upload |
| Export HF to ONNX | HF-to-ONNX export | local/cached HF model and tokenizer | Writes `model.onnx`; optional verification and object-store upload |
| Batch call a hosted completions API | endpoint generation helper | URL, auth, network, prompt inputs, output folder | Sends prompts over network; writes CSV |
| FasterTransformer conversion/runtime | Advanced reference only | MPT checkpoint plus FT build and GPUs | Large conversion/runtime; external native library |

## Hugging Face completion generation

The LLM Foundry HF generation helper loads `AutoConfig`, `AutoTokenizer`, and `AutoModelForCausalLM`, then calls `model.generate` for one or more prompts. When the helper script is available in the user's working project, its key invocation shape is:

```bash
python hf_generate.py \
  --name_or_path <local-hf-folder-or-hub-id> \
  --prompts "First prompt" "Second prompt" \
  --max_new_tokens 128 \
  --temperature 0.7 --top_k 50 --top_p 0.95 \
  --model_dtype bf16 \
  --device_map auto \
  --trust_remote_code true
```

Key flags and behavior:

- `--name_or_path` / `-n`: required local HF folder or Hub id. Prefer local folders for offline work.
- `--prompts` / `-p`: one or more literal prompt strings or prompt-file tokens using `file::<path>`.
- `--prompt-delimiter`: delimiter used when a `file::` prompt source should be split into multiple prompts. Without it, a prompt file is one prompt.
- `--max_seq_len`: if the config exposes `max_seq_len`, override it before loading. Useful for MPT ALiBi contexts.
- `--max_new_tokens`: generated continuation length.
- `--max_batch_size`: split prompt list into smaller batches.
- Sampling controls accept lists and are swept as a Cartesian product: `--temperature`, `--top_k`, `--top_p`, `--repetition_penalty`, `--no_repeat_ngram_size`, and `--seed`.
- `--do_sample`: boolean-like flag; when `temperature == 0`, the helper forces deterministic `do_sample=False`.
- `--use_cache`, `--eos_token_id`, `--pad_token_id`: passed into generation. If the tokenizer has no pad token, the helper uses the EOS token as pad.
- `--model_dtype`: `fp32`, `fp16`, or `bf16` for model load dtype. Default is fp32.
- `--autocast_dtype`: optional generation autocast dtype. If omitted, no autocast context is used.
- `--warmup`: runs one warmup generation before measuring the first actual batch.
- `--device`: move the whole model to a single explicit device such as `cpu` or `cuda:0`.
- `--device_map`: Hugging Face Accelerate device map such as `auto` or `balanced`. Default behavior is `device_map='auto'` when `--device` is unset.
- `--device` and `--device_map` are mutually exclusive.
- `--attn_impl`: for configs with `attn_config`, set attention implementation such as `torch` or `flash` before loading.
- `--trust_remote_code`, `--use_auth_token`, `--revision`: forwarded to Hugging Face `from_pretrained` calls.

Practical defaults:

- CPU smoke: set `--device cpu --model_dtype fp32 --max_new_tokens 8 --max_batch_size 1 --warmup false` and use a tiny local model.
- Single GPU MPT: use `--device cuda:0 --model_dtype bf16 --attn_impl torch` unless flash attention is installed and compatible.
- Multi-GPU large model: use `--device_map auto` and leave `--device` unset.

## Interactive chat

The chat helper loads the same HF model/tokenizer stack but wraps generation in a `Conversation` object. Current behavior uses the tokenizer's `apply_chat_template` with role dictionaries:

```text
{"role": "system", "content": <system prompt>}
{"role": "user", "content": <user turn>}
{"role": "assistant", "content": <assistant turn>}
```

Invocation shape:

```bash
python hf_chat.py \
  --name_or_path <local-chat-model-or-hub-id> \
  --max_new_tokens 512 \
  --temperature 0.3 --top_k 0 --top_p 1.0 \
  --model_dtype bf16 \
  --device_map auto \
  --trust_remote_code true \
  --system_prompt "You are a helpful assistant."
```

Key flags and behavior:

- Shares model-load controls with generation: `--name_or_path`, `--max_seq_len`, `--model_dtype`, `--autocast_dtype`, `--trust_remote_code`, `--use_auth_token`, `--revision`, `--device`, `--device_map`, and `--attn_impl`.
- Generation controls are scalar rather than list-swept: `--max_new_tokens`, `--temperature`, `--top_k`, `--top_p`, `--do_sample`, `--use_cache`, `--eos_token_id`, `--pad_token_id`, and `--seed`.
- `--system_prompt` sets the first system message.
- `--stop_tokens` is a space-separated token string; default stop tokens include common end-of-text and ChatML end markers.
- The current helper expects chat formatting to come from `tokenizer.chat_template`. If a model requires custom user/assistant wrappers, encode that format in the tokenizer chat template or write a small wrapper around `apply_chat_template`; do not assume legacy `user_msg_fmt` or `assistant_msg_fmt` flags exist.

REPL behavior:

- Press return twice to send a multi-line user message.
- `clear` resets conversation history while keeping the system prompt.
- `history` prints the internal role/content history.
- `history_fmt` prints the rendered tokenizer chat template.
- `system` prompts for a new system prompt.
- `quit` exits.

## Endpoint generation is reference-only

Endpoint generation sends prompts to an OpenAI-compatible text-completions service and writes a CSV with prompt/output rows. Treat it as reference-only until the user confirms network side effects and credentials.

Required pieces:

- endpoint URL from `--endpoint` or `ENDPOINT_URL`;
- optional API key from `ENDPOINT_API_KEY`;
- prompt inputs as literal strings, `file::<path>` prompt files, or object-store locations;
- `--output-folder` as local output file/folder target or object-store URI;
- Python dependencies for asynchronous HTTP, rate limiting, and CSV/dataframe handling;
- network egress to the service and authorization to send the prompts.

Important flags:

- `--inputs` / `-i`: prompt strings, `file::` prompt files, or object-store prompt sources.
- `--prompt-delimiter`: delimiter for prompt files; default newline.
- `--output-folder` / `-o`: required CSV output target.
- `--rate-limit`: maximum calls per second.
- `--batch-size`: prompts per request; it must not exceed the rate limit.
- `--max-tokens`, `--temperature`, `--top-k`, `--top-p`: forwarded generation parameters.

Before using endpoint generation, ask whether prompts may leave the machine, whether logs may contain prompts, and whether the service follows the expected completions response schema with `choices` and `usage` fields.
