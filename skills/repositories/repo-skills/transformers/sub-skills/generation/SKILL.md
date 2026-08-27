---
name: generation
description: "Configure Transformers text/chat generation, GenerationConfig,
  decoding controls, streamers, logits processors, stopping criteria, and
  continuous batching concepts without requiring model downloads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Generation

## Use This Sub-skill When

Use this sub-skill for Transformers workflows that need to design, validate, or troubleshoot text and chat generation behavior without downloading large models.

- Configure `GenerationConfig` or `model.generate(...)` arguments for greedy, sampling, beam, constrained, or custom generation.
- Decide between `max_new_tokens`, `max_length`, `do_sample`, `temperature`, `top_p`, `top_k`, `num_beams`, `repetition_penalty`, EOS, and padding controls.
- Format chat messages with tokenizer chat templates before generation.
- Add or reason about `LogitsProcessor`, `LogitsProcessorList`, `StoppingCriteria`, and `StoppingCriteriaList`.
- Stream generated text with `TextIteratorStreamer` or related streamer classes.
- Explain continuous batching concepts, request lifecycle, paged KV cache, scheduling, compile/offload options, and per-request sampling.
- Validate generation config JSON safely using the bundled smoke script.

## Route Elsewhere

- For `pipeline(...)` task selection, device placement, and pipeline-only kwargs, use `../inference-pipelines/SKILL.md`.
- For tokenizer loading, padding side, special tokens, processors, and chat-template authoring details, use `../tokenizers-processors/SKILL.md`.
- For `transformers chat`, `transformers serve`, HTTP serving, and OpenAI-compatible endpoints, use `../serving-cli/SKILL.md`.
- For quantized generation, bitsandbytes, GPTQ, AWQ, Quanto, or device-memory tradeoffs, use `../quantization-integrations/SKILL.md`.
- For fine-tuning, `Trainer`, `TrainingArguments`, or dataset preprocessing, use `../training/SKILL.md`.
- For adding new model classes or custom architectures, use `../model-extension/SKILL.md`.

## Fast Generation Checklist

1. Prefer `max_new_tokens` for user-facing generation length; avoid relying on defaults.
2. Choose one decoding family first: greedy (`do_sample=False`, `num_beams=1`), sampling (`do_sample=True`), beam (`num_beams>1`), or beam sampling (`num_beams>1`, `do_sample=True`).
3. Only use sampling-only controls such as `temperature`, `top_p`, and `top_k` when `do_sample=True`.
4. Set `pad_token_id` for batched decoder-only generation when the tokenizer has no pad token, commonly to `eos_token_id` for inference.
5. For chat models, pass structured messages through `tokenizer.apply_chat_template(...)` instead of raw concatenated strings.
6. Put durable defaults in `GenerationConfig`; use per-call kwargs for one-off overrides.
7. Treat PyTorch-backed model generation, streamers that consume real model output, and continuous batching as optional-dependency workflows that require `torch` and model weights.

## Primary APIs

- `GenerationConfig(**kwargs)` stores generation parameters and can be saved/loaded with `save_pretrained(...)` and `from_pretrained(...)`.
- `GenerationMixin.generate(...)` is the generation entrypoint on compatible model classes.
- `TextIteratorStreamer(tokenizer, skip_prompt=False, timeout=None, **decode_kwargs)` supports iterator-style streaming from a background generation thread.
- `LogitsProcessor` and `StoppingCriteria` customize token selection and stopping rules.
- `ContinuousBatchingConfig` and `ContinuousBatchingManager` configure paged-KV continuous batching for serving-like generation.

See `references/api-reference.md` for parameter groups and API decision notes.

## Safe No-download Validation

Use the bundled smoke script to validate config shape and common contradictions without loading a model:

```bash
python scripts/generation_config_smoke.py \
  --max-new-tokens 64 --do-sample --temperature 0.7 --top-p 0.9
```

Validate an existing JSON file:

```bash
python scripts/generation_config_smoke.py \
  --config-json generation_config.json --strict
```

Expected success signal: the script prints `OK generation config validated` plus a normalized summary. Expected failure signal: it exits non-zero with `ERROR` and names the conflicting option.

## Common Workflows

- Draft deterministic or creative generation settings: `references/workflows.md#choose-a-decoding-strategy`.
- Build chat prompts safely: `references/workflows.md#chat-generation-with-templates`.
- Stream generation without deadlocks: `references/workflows.md#streaming-generation`.
- Add custom logits or stopping controls: `references/workflows.md#custom-logits-processors-and-stopping-criteria`.
- Plan continuous batching: `references/continuous-batching.md`.
- Diagnose warnings and config conflicts: `references/troubleshooting.md`.

## Integrated Routing Notes

When generation settings appear inside serving, pipeline, quantization, or chat-template requests, keep this sub-skill responsible for decoding semantics and route the outer workflow to the relevant sibling. For example, a serving/chat request with `reasoning` or `chat_template_kwargs` needs this sub-skill for `GenerationConfig` and chat generation choices, plus `../serving-cli/SKILL.md` for endpoint behavior.

## Optional Dependency Boundary

A minimal Transformers import can inspect `GenerationConfig` and many config utilities without PyTorch. Real `AutoModelForCausalLM`, `model.generate(...)`, streamers attached to model execution, logits processors that operate on tensors, and continuous batching require backend dependencies such as `torch`; missing backends raise optional dependency `ImportError`s. When writing agent instructions or tests, keep no-download config validation separate from model-backed generation checks.
