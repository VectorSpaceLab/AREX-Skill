# Core composition workflows

## Define a stateless processor

Use `@processor.processor_function` when the processor consumes a stream and
may need to buffer, combine, or inspect multiple parts.

```python
from collections.abc import AsyncIterable
from genai_processors import content_api, processor

@processor.processor_function
async def only_text(content: processor.ProcessorStream) -> AsyncIterable[content_api.ProcessorPartTypes]:
    async for part in content:
        if content_api.is_text(part.mimetype):
            yield part
```

## Define a per-part processor

Use `PartProcessor` or `@processor.part_processor_function` when each part is
independent. A match function prevents accidental handling of images, audio, or
function responses as text.

```python
def is_text(part: content_api.ProcessorPart) -> bool:
    return content_api.is_text(part.mimetype)

@processor.part_processor_function(match_fn=is_text)
async def shout(part: content_api.ProcessorPart):
    yield part.text.upper()
```

## Compose without losing streaming

```python
pipeline = only_text + shout
async for part in pipeline(["hello", " ", "world"]):
    print(part.text, end="")
```

Prefer `+` for sequential pipelines. Use `await pipeline(input).gather()` or
`await pipeline(input).text()` only when the caller actually needs a complete
result. Iteration keeps time-to-first-part low.

## Branch and recombine streams

Use `processor.parallel_concat` when every branch needs the same full prompt and
branch order in the final output matters:

```python
combined = processor.parallel_concat([agent_a, agent_b])
```

Use `streams.split` and `streams.merge` when you need interleaved output from
whichever branch responds first:

```python
from genai_processors import streams

s1, s2 = streams.split(input_stream, n=2)
merged = streams.merge(model_a(s1), model_b(s2))
```

## Route by MIME type or substream

```python
from genai_processors import switch

router = (
    switch.Switch(content_api.mime_type)
    .case(content_api.is_audio, audio_processor)
    .default(text_processor)
)
```

For per-part pipelines, use `PartSwitch` so separate modalities can be processed
concurrently without head-of-line blocking.

## Add tracing

```python
from genai_processors.dev import trace_file

async with trace_file.SyncFileTrace(trace_dir="traces", name="demo"):
    result = await pipeline("hello").text()
```

Keep traces outside the runtime skill tree. For video/audio-heavy pipelines,
set size limits or downsample images to avoid large trace files.

## Add caching

Use caches around the expensive stage, not around every preprocessing step.

```python
from genai_processors import cache, processor

processor.CachedProcessor.set_cache(cache.InMemoryCache(ttl_hours=1))
cached_model = processor.CachedProcessor(model, key_prefix="model-v1")
```

Change `key_prefix` when the wrapped logic changes. Do not use
`CachedProcessor` for infinite live streams because it buffers the full input.

## Validate locally

Run this sub-skill's smoke script from an installed environment:

```bash
python sub-skills/core-composition/scripts/smoke_core.py
```

The script exercises content normalization, processor decorators, and stream
composition without network or hardware.
