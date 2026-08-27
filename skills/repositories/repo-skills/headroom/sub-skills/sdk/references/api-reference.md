# Headroom SDK API reference

This reference covers the verified Python-facing and app-facing SDK pieces that future agents can use without reopening the source repository.

## Python one-function compression API

Verified signature:

```text
compress(messages, model='claude-sonnet-4-5-20250929', model_limit=200000, optimize=True, hooks=None, config=None, **kwargs) -> CompressResult
```

Verified `CompressConfig` defaults:

- `compress_user_messages=False`
- `compress_system_messages=True`
- `protect_recent=4`
- `protect_analysis_context=True`
- `frozen_message_count=0`
- `target_ratio=None`
- `min_tokens_to_compress=250`
- `kompress_model=None`
- `savings_profile=None`

`compress_spreadsheet(path, ...)` shares the same model/model_limit defaults and compresses spreadsheet-like inputs.

### Basic usage

```python
from headroom import compress, CompressConfig

cfg = CompressConfig(target_ratio=0.5, protect_recent=0)
result = compress(messages, config=cfg)
print(result.messages)
print(result.tokens_before, result.tokens_after, result.tokens_saved)
```

`CompressResult` includes the compressed `messages`, token counts, compression ratio, and `transforms_applied`.

## Python client wrapper

Verified `HeadroomClient` constructor shape:

```text
HeadroomClient(original_client, provider, store_url=None, default_mode='audit', model_context_limits=None, cache_optimizer=None, enable_cache_optimizer=True, enable_semantic_cache=False, config=None)
```

Verified methods:

- `get_stats()` -> `dict[str, Any]`
- `get_summary(start_time=None, end_time=None)` -> `dict[str, Any]`
- `get_metrics(start_time=None, end_time=None, model=None, mode=None, limit=100)` -> `list[RequestMetrics]`
- `validate_setup()` -> `dict[str, Any]`
- `close()`

Important sub-wrapper methods:

- `ChatCompletions.create(...)` accepts `headroom_mode`, `headroom_cache_prefix_tokens`, `headroom_output_buffer_tokens`, `headroom_keep_turns`, and `headroom_tool_profiles` in addition to the model/messages.
- `ChatCompletions.simulate(...)` returns a `SimulationResult`.
- `Messages.create(...)`, `Messages.stream(...)`, and `Messages.simulate(...)` mirror the Anthropic-style path.

## SharedContext

Verified signature:

```text
SharedContext(model='claude-sonnet-4-5-20250929', ttl=3600, max_entries=100)
```

Verified methods:

- `put(key, content, *, agent=None) -> ContextEntry`
- `get(key, *, full=False) -> str | None`
- `getEntry(key)` in the source object model is not part of the verified Python API exposed here; prefer the documented `get`/`stats` methods.
- `stats()` returns aggregate token savings.
- `clear()` clears stored entries.

## Relevance scoring

Verified factory and scorer signatures:

```text
create_scorer(tier='hybrid', **kwargs) -> RelevanceScorer
BM25Scorer(k1=1.5, b=0.75, normalize_score=True, max_score=10.0)
HybridScorer(alpha=0.5, adaptive=True, bm25_scorer=None, embedding_scorer=None)
EmbeddingScorer(model_name=None, cache_model=True)
```

Use `create_scorer('bm25')` for zero-dependency scoring, `create_scorer('hybrid')` for the default mixed strategy, and `create_scorer('embedding')` only when the optional embedding dependency is installed.

## Image helpers

Verified signature:

```text
ImageCompressor(model_id=None, use_siglip=True, device=None)
ImageCompressor.compress(messages, provider='openai') -> list[dict[str, Any]]
compress_images(messages, provider='openai') -> list[dict[str, Any]]
```

The image path depends on optional OCR and model packages; it should be described as an extra-gated feature, not a guaranteed base import path.

## Path helpers

Use `headroom.paths` when users ask where state lives:

- `config_dir()` / `workspace_dir()` are the canonical roots.
- Resource helpers include `settings_path()`, `savings_path()`, `savings_events_path()`, `toin_path()`, `subscription_state_path()`, `memory_db_path()`, `proxy_log_path()`, `models_config_path()`, and more.
- Resource-specific env vars win over the canonical roots.

## TypeScript SDK highlights

The package `headroom-ai` exposes these primary exports from `sdk/typescript/src/index.ts`:

- `compress`, `HeadroomClient`, `simulate`
- format conversion helpers such as `detectFormat`, `toOpenAI`, `fromOpenAI`
- `CompressionHooks`, `extractUserQuery`, `countTurns`, `extractToolCalls`
- `SharedContext`
- filesystem path helpers that mirror the Python path contract
- error hierarchy and public config/data model types

Use the TypeScript SDK docs for install and example details; the runtime skill should stay compact and route deeper API tables there.
