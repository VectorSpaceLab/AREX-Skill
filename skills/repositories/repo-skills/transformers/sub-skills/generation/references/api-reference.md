# Generation API Reference

This reference distills the generation APIs and option decisions needed by coding agents. It is self-contained and intentionally avoids requiring model downloads.

## Version and Package Facts

- Inspected Transformers version: `5.13.0.dev0`.
- Distribution and import name: `transformers`.
- Console script: `transformers -> transformers.cli.transformers:main`.
- Minimal inspection verified base imports only; PyTorch-backed model classes and tensor processors need optional dependencies.

## `GenerationConfig`

Use `GenerationConfig(**kwargs)` when generation defaults should be serializable, shared across calls, or validated independently from a model. Use direct `model.generate(..., **kwargs)` only for one-off overrides.

Common parameter groups:

| Group | Options | Decision notes |
| --- | --- | --- |
| Length | `max_new_tokens`, `max_length`, `min_new_tokens`, `min_length`, `early_stopping` | Prefer `max_new_tokens` for user prompts. `max_length` includes prompt length and can surprise decoder-only workflows. |
| Strategy | `do_sample`, `num_beams`, `num_beam_groups`, `penalty_alpha`, `dola_layers` | Pick greedy, sampling, beam, contrastive, or DoLa intentionally; avoid mixing unrelated strategies without checking docs. |
| Sampling | `temperature`, `top_k`, `top_p`, `min_p`, `typical_p`, `epsilon_cutoff`, `eta_cutoff` | Sampling controls only make sense with `do_sample=True`; otherwise remove them or enable sampling. |
| Repetition | `repetition_penalty`, `encoder_repetition_penalty`, `no_repeat_ngram_size`, `bad_words_ids`, `sequence_bias` | These interact through logits processors and can over-constrain short outputs. Test with realistic prompts. |
| Tokens | `pad_token_id`, `bos_token_id`, `eos_token_id`, `decoder_start_token_id`, `forced_bos_token_id`, `forced_eos_token_id` | Set pad/EOS explicitly for batched generation and seq2seq models. |
| Output | `return_dict_in_generate`, `output_scores`, `output_logits`, `output_attentions`, `output_hidden_states` | Diagnostic outputs can increase memory; enable only for analysis. |
| Cache | `use_cache`, `cache_implementation`, `cache_config`, `return_legacy_cache` | Caches speed decoding but may need architecture/backend support. |
| Constraints | `constraints`, `force_words_ids`, `prefix_allowed_tokens_fn`, `renormalize_logits` | Useful for structured outputs but easy to make unsatisfiable. |

Durable pattern:

```python
from transformers import GenerationConfig

generation_config = GenerationConfig(
    max_new_tokens=128,
    do_sample=True,
    temperature=0.7,
    top_p=0.9,
    repetition_penalty=1.05,
    pad_token_id=tokenizer.eos_token_id,
    eos_token_id=tokenizer.eos_token_id,
)
outputs = model.generate(**inputs, generation_config=generation_config)
```

## `generate(...)` Option Precedence

`GenerationMixin.generate(...)` combines settings from model defaults, `model.generation_config`, a passed `generation_config`, and explicit generation kwargs. In practical agent work:

1. Start with the model's default generation config.
2. Override persistent application defaults with a `GenerationConfig` object.
3. Override request-specific values with explicit kwargs such as `max_new_tokens=32`.
4. Validate that explicit kwargs do not silently contradict the selected decoding family.

Decoder-only models usually return prompt tokens plus generated tokens. To decode only the new continuation, slice output IDs after the input length.

## Decoding Strategy Matrix

| Goal | Minimal settings | Avoid |
| --- | --- | --- |
| Deterministic completion | `do_sample=False`, `num_beams=1`, set `max_new_tokens` | `temperature`, `top_p`, `top_k` unless sampling is enabled |
| Creative chat/story | `do_sample=True`, `temperature≈0.7-1.0`, `top_p≈0.9`, set `max_new_tokens` | Very low `temperature` with high creativity expectations |
| Focused low-variance answer | `do_sample=True`, `temperature≈0.2-0.5`, optionally `top_p` | Assuming `temperature` works with `do_sample=False` |
| Input-grounded translation/summarization | `num_beams>1`, `do_sample=False`, set `max_new_tokens` | Large beams for latency-sensitive chat |
| Diverse alternatives | `num_return_sequences>1` with sampling or beams | Returning more sequences than available beams |
| Strict constraints | `force_words_ids`, `bad_words_ids`, `prefix_allowed_tokens_fn` | Constraints that block every possible next token |

## Streamers

`TextIteratorStreamer(tokenizer, skip_prompt=False, timeout=None, **decode_kwargs)` converts generated token IDs into text chunks that can be consumed from an iterator while generation runs in another thread.

Safe usage pattern:

```python
from threading import Thread
from transformers import TextIteratorStreamer

streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, timeout=10.0)
generation_kwargs = dict(**inputs, streamer=streamer, max_new_tokens=128)
thread = Thread(target=model.generate, kwargs=generation_kwargs)
thread.start()
for text in streamer:
    handle_chunk(text)
thread.join(timeout=20.0)
```

Operational checks:

- Use `timeout` so the iterator can surface generation-thread failures instead of hanging forever.
- Start `model.generate(...)` in a background thread before iterating.
- Pass decoding kwargs such as `skip_special_tokens=True` to the streamer when desired.
- Ensure the tokenizer is compatible with incremental decoding for the intended language and special tokens.

## Logits Processors and Stopping Criteria

Use custom processors when generation needs token-level intervention not expressible with config fields.

- `LogitsProcessor(input_ids, scores)` transforms next-token scores before token selection.
- `LogitsProcessorList([...])` applies processors in order; order matters when processors mask, bias, or renormalize scores.
- `StoppingCriteria(input_ids, scores, **kwargs)` returns a boolean-like signal to stop generation.
- `StoppingCriteriaList([...])` stops when configured criteria are satisfied.

Guidelines:

- Prefer built-in config knobs before custom processors.
- Keep processors deterministic and side-effect-light.
- Beware combining `bad_words_ids`, `no_repeat_ngram_size`, `force_words_ids`, and custom masks; over-constraint can produce poor outputs or errors.
- If a processor changes score normalization, consider `renormalize_logits=True` when compatible.

## Chat Templates

For chat-tuned models, generate from structured messages rather than raw strings:

```python
messages = [
    {"role": "system", "content": "You are concise."},
    {"role": "user", "content": "Explain KV caching."},
]
inputs = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_tensors="pt",
)
```

Important switches:

- `add_generation_prompt=True` adds tokens that mark the assistant response start.
- `continue_final_message=True` continues an existing final assistant message; do not combine casually with `add_generation_prompt`.
- `chat_template_kwargs` may pass template-specific controls such as reasoning mode when the tokenizer template supports them.
- Each message needs valid `role` and `content` fields unless the model's template documents additional schema.

## Pipeline Touchpoint

`pipeline(...)` accepts generation options through pipeline call kwargs or model kwargs. Its inspected signature includes `task`, `model`, `config`, `tokenizer`, processors, `device`, `device_map`, `dtype='auto'`, `trust_remote_code`, `model_kwargs`, `pipeline_class`, and `**kwargs`. Use this sub-skill for generation options; use `../inference-pipelines/SKILL.md` for pipeline construction and device routing.
