# Headroom SDK workflows

## Compress messages before calling any LLM client

```python
from headroom import compress
from openai import OpenAI

messages = [
    {"role": "user", "content": "Summarize the relevant errors."},
    {"role": "tool", "content": big_tool_output},
]
compressed = compress(messages, model="gpt-4o")
response = OpenAI().chat.completions.create(
    model="gpt-4o",
    messages=compressed.messages,
)
```

Use `optimize=False` only for smoke tests or A/B passthrough checks; it returns the same messages without compressing.

## Tune compression for documents or RAG

```python
from headroom import CompressConfig, compress

cfg = CompressConfig(
    compress_user_messages=True,
    protect_recent=0,
    target_ratio=0.5,
    min_tokens_to_compress=100,
)
result = compress(messages, model="claude-sonnet-4-5-20250929", config=cfg)
```

Use `compress_user_messages=True` for documents or RAG chunks in user messages. For coding agents, keep the default `False` unless tool outputs are embedded in user messages.

## Use a client wrapper

The Python `HeadroomClient` wraps an existing provider client and exposes OpenAI-style and Anthropic-style sub-clients. Use it when the application already has an SDK client object and wants Headroom metrics/simulations around calls.

```python
from openai import OpenAI
from headroom import HeadroomClient, OpenAIProvider

client = HeadroomClient(OpenAI(), OpenAIProvider(), default_mode="optimize")
result = client.chat.completions.simulate(model="gpt-4o", messages=messages)
print(result.tokens_saved)
```

## Spreadsheet and table compression

Run the bundled no-network demo first:

```bash
python scripts/tabular_compression_demo.py
```

Then use the API:

```python
from headroom import compress_spreadsheet

result = compress_spreadsheet("input.xlsx", model="gpt-4o")
print(result.tokens_saved)
```

Install the `spreadsheet` extra when `.xlsx` / `.xls` ingestion is needed.

## Relevance scoring

```python
from headroom.relevance import create_scorer

scorer = create_scorer("bm25")        # zero-dependency
hybrid = create_scorer("hybrid")      # default, falls back when embeddings unavailable
scores = scorer.score_batch(items, "find production errors")
```

Use embedding scoring only when optional dependencies and model caches are available.

## Image compression

```python
from headroom.image import compress_images

messages = compress_images(messages, provider="openai")
```

Image compression can require optional OCR/model assets. Do not run it as a default smoke on a cold network-constrained machine.

## TypeScript application compression

```typescript
import { compress } from "headroom-ai";

const result = await compress(messages, {
  model: "gpt-4o",
  baseUrl: "http://127.0.0.1:8787",
});
```

Unlike Python local compression, the TypeScript client primarily calls a running Headroom proxy. If the proxy is not reachable, check whether the caller enabled fallback behavior and route to `proxy-wrap` for proxy setup.

## Hooks

Use hooks when the application needs to modify messages, compute per-message biases, or observe results:

```typescript
import { CompressionHooks, compress } from "headroom-ai";

class MyHooks extends CompressionHooks {
  computeBiases(messages, ctx) {
    return { 0: 2.0 };
  }
  postCompress(event) {
    console.log(event.tokensSaved);
  }
}

await compress(messages, { model: "gpt-4o", hooks: new MyHooks() });
```

Python hooks follow the same conceptual pipeline but use Python classes from `headroom.hooks`.
