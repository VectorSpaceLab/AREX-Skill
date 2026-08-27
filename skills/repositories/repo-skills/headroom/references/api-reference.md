# Headroom public API overview

Use this reference to decide whether a task belongs to the Python/TypeScript SDK route or to a CLI/proxy route.

## Python package

The package is distributed as `headroom-ai` and imported as `headroom`. Public root exports include:

- `compress`, `compress_spreadsheet`, `CompressConfig`, `CompressResult`
- `HeadroomClient`, `Provider`, `OpenAIProvider`, `AnthropicProvider`
- `HeadroomConfig`, `HeadroomMode`, `SmartCrusherConfig`, `CacheAlignerConfig`, `CacheOptimizerConfig`, `RelevanceScorerConfig`
- `SharedContext`
- `CompressionHooks`, `CompressContext`, `CompressEvent`
- token counters, transforms, cache optimizers, relevance scorers, observability helpers, and error classes
- optional memory exports such as `with_memory`, `Memory`, `HierarchicalMemory`, `MemoryConfig`, and `EmbedderBackend`

### Local compression

Verified signature:

```text
compress(messages, model='claude-sonnet-4-5-20250929', model_limit=200000, optimize=True, hooks=None, config=None, **kwargs) -> CompressResult
```

`CompressConfig` controls whether user/system messages are compressed, how many recent messages are protected, the minimum message size, target ratio, Kompress model, frozen cache prefix, and named savings profile.

### Client wrapper

`HeadroomClient(original_client, provider, store_url=None, default_mode='audit', model_context_limits=None, cache_optimizer=None, enable_cache_optimizer=True, enable_semantic_cache=False, config=None)` wraps an existing provider client. Its `chat.completions` and `messages` sub-clients support create/simulate methods with Headroom-specific controls such as `headroom_mode`, `headroom_keep_turns`, `headroom_output_buffer_tokens`, and `headroom_tool_profiles`.

### Shared context

`SharedContext(model='claude-sonnet-4-5-20250929', ttl=3600, max_entries=100)` stores compressed inter-agent handoffs. `put(key, content, agent=...)` returns metadata; `get(key, full=True)` retrieves the original when needed; `stats()` reports token savings.

### Optional APIs

- `headroom.memory` provides persistent memory and wrappers; route detailed use to `sub-skills/memory`.
- `headroom.relevance` provides BM25, hybrid, and embedding scorers; BM25 is the dependency-light fallback.
- `headroom.image` provides image compression/OCR routing and is extra/model gated.
- `headroom.paths` is the canonical filesystem contract for config/workspace state.

## TypeScript package

The npm package `headroom-ai` requires Node `>=18.0.0` and exports:

- `compress`, `HeadroomClient`, `simulate`
- `detectFormat`, `toOpenAI`, `fromOpenAI`
- `CompressionHooks` and message/tool extraction helpers
- `SharedContext`
- error hierarchy, configuration/data types, SSE utilities, and path helpers

The TS client primarily talks to a running proxy. Route proxy/base URL problems to `sub-skills/proxy-wrap` rather than treating them as a pure npm import failure.
