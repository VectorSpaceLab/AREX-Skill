# Client API Reference

## Main entry points

- `AutoDistributedConfig.from_pretrained(model_name_or_path, *args, revision=None, **kwargs)` resolves a Transformers config, checks Petals model-family support, and returns the matching distributed config class.
- `AutoDistributedModel.from_pretrained(...)` returns a base distributed model without a language-model head.
- `AutoDistributedModelForCausalLM.from_pretrained(...)` returns a Transformers-compatible causal LM wrapper with remote transformer blocks.
- `AutoDistributedModelForSequenceClassification.from_pretrained(..., num_labels=N)` returns a classification wrapper with a local classifier head.
- `AutoDistributedSpeculativeModel.from_pretrained(..., small_model=...)` is for supported Llama speculative generation.
- `RemoteSequential(config, dht=None, start_block=None, end_block=None, sequence_manager=None, **kwargs)` represents a chain or slice of remote transformer blocks.

## Client configuration fields

Important fields include `initial_peers`, `dht_prefix`, `show_route`, `allowed_servers`, `blocked_servers`, `use_server_to_server`, `connect_timeout`, `request_timeout`, `update_period`, `max_retries`, `min_backoff`, `max_backoff`, `ban_timeout`, `active_adapter`, `max_pinged`, and `ping_timeout`.

Use `initial_peers` for private swarms. Use `dht_prefix` when the served model's DHT keys must be disambiguated from the model identifier. Use `allowed_servers`/`blocked_servers` only when the user intentionally constrains routing.

## Generation and session constraints

`generate(inputs=None, *args, session=None, **kwargs)` wraps Transformers generation. If no active session exists, Petals creates one and needs exactly one of `max_length` or `max_new_tokens` to reserve remote attention cache. In an active session, repeated calls can use `generate(None, max_new_tokens=...)` to continue from previously generated tokens.

Petals model forwards generally do not support arbitrary custom attention masks, head masks, hidden-state output capture, or non-consecutive position IDs. Keep masks absent or all ones for ordinary generation.

## Model-family notes

Petals registers distributed variants for BLOOM, Llama, Falcon, and Mixtral families in this snapshot. Llama configs derive a DHT prefix from the final repo name and append `-hf` when needed. BLOOM historically uses a `-petals` suffix. Mixtral and Falcon have their own distributed config wrappers. Unsupported Transformers `model_type` values raise a Petals-specific unsupported-model error.
