# Generation Troubleshooting

## `max_length` vs `max_new_tokens`

Symptoms:

- Output stops earlier than expected.
- Decoder-only generation appears to count prompt tokens against the limit.
- Warnings mention both `max_length` and `max_new_tokens`.

Fix:

- Prefer `max_new_tokens` for user-visible continuation length.
- Remove `max_length` unless you intentionally want prompt plus output total length.
- For decoder-only models, decode only `outputs[:, input_length:]` when presenting the continuation.

## Sampling Parameters Ignored or Invalid

Symptoms:

- Warning that `temperature`, `top_p`, or `top_k` is set while `do_sample=False`.
- Output remains deterministic despite sampling options.
- Validation fails for zero/negative temperature or out-of-range probabilities.

Fix:

- For greedy/beam deterministic output, remove sampling-only parameters.
- For creative output, set `do_sample=True` and use valid ranges: `temperature > 0`, `0 < top_p <= 1`, `top_k >= 0`.
- Validate first with `scripts/generation_config_smoke.py --strict`.

## Missing `pad_token_id` or EOS Warnings

Symptoms:

- Warnings about missing `pad_token_id` during open-ended generation.
- Batched decoder-only generation produces odd padding behavior.
- Tokenizer has no pad token.

Fix:

- For inference-only decoder generation, set `pad_token_id=tokenizer.eos_token_id` when appropriate.
- Ensure `eos_token_id` is set when generation should stop on EOS.
- For training or tokenizer design, route to `../tokenizers-processors/SKILL.md` before changing special tokens globally.

## Repetition and Logits Processor Interactions

Symptoms:

- Outputs are empty, repetitive, or unnaturally constrained.
- Custom processor plus `bad_words_ids`, `no_repeat_ngram_size`, or forced tokens blocks generation.
- Scores contain invalid values after processors.

Fix:

- Remove constraints one at a time until generation recovers.
- Check processor order in `LogitsProcessorList`.
- Avoid masking every valid token; keep EOS reachable unless a separate stopping condition is guaranteed.
- Consider `renormalize_logits=True` after score-changing processors.

## Streamer Hangs or Timeouts

Symptoms:

- Iteration over `TextIteratorStreamer` never ends.
- Exceptions in `model.generate(...)` are not visible in the streaming loop.
- UI receives partial text then stalls.

Fix:

- Run `model.generate(...)` in a background thread before iterating.
- Set `timeout` on `TextIteratorStreamer`.
- Join the generation thread and log model-thread exceptions.
- Verify `max_new_tokens` or stopping criteria guarantee termination.

## Chat Template Role or Content Errors

Symptoms:

- `apply_chat_template(...)` raises about missing fields or unsupported roles.
- Model responds as if prompt format is wrong.
- `continue_final_message` and `add_generation_prompt` conflict.

Fix:

- Use messages shaped like `{ "role": "user", "content": "..." }` unless the tokenizer template documents more fields.
- Use `add_generation_prompt=True` for a new assistant response.
- Use `continue_final_message=True` only to continue a final assistant prefix.
- Pass template-specific controls through supported `chat_template_kwargs`; do not invent roles or control tokens.
- Route template authoring or tokenizer changes to `../tokenizers-processors/SKILL.md`.

## Optional Dependency Import Errors

Symptoms:

- Importing model classes, tensor processors, or continuous batching raises an optional dependency `ImportError`.
- `torch`-dependent code fails in a minimal inspection environment.

Fix:

- Keep config-only checks on `GenerationConfig` separate from model-backed checks.
- Install the needed backend dependencies before testing `AutoModelForCausalLM`, tensor logits processors, or continuous batching.
- Avoid large model downloads in smoke tests; use tiny/local fixtures only when a verified model environment exists.

## Continuous Batching Backend Failures

Symptoms:

- Startup errors mention paged attention, unsupported attention implementation, KV cache sizing, tensor parallel head divisibility, or missing `flash-attn`.
- Requests stall or are rejected after `stop()`.
- Per-request `temperature` or `top_p` is ignored.

Fix:

- Use a paged attention backend such as `attn_implementation="paged|sdpa"`, `"paged|eager"`, or `"paged|flash_attention_2"`.
- Install backend packages required by the selected attention implementation.
- Lower `max_memory_percent`, `max_batch_tokens`, `block_size`, or `max_requests_per_batch` when cache/logits memory is too high.
- Enable `per_request_processors=True` and set non-default base generation values for request-specific sampling controls.
- Call `start()`, `stop()`, and `destroy()` according to manager lifecycle; do not submit new requests after shutdown.

## Config Smoke Script Failures

The bundled script intentionally catches common contradictions before model execution.

- `ERROR sampling option ... requires do_sample=True`: remove sampling controls or set `--do-sample`.
- `ERROR use max_new_tokens instead of combining ...`: remove the conflicting length field.
- `ERROR pad_token_id is required by --require-pad-token`: set a valid integer token ID.
- `ERROR config JSON must contain an object`: provide a JSON object, not a list/string.

Use `--print-json` to inspect the normalized `GenerationConfig` dictionary produced by Transformers.
