# Core composition troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError` constructing `ProcessorPart` from bytes | bytes need a MIME type | pass `mimetype='image/png'`, `audio/l16;rate=16000`, `application/pdf`, etc. |
| `.text` raises on a part | part is image/audio/PDF/function call/response | guard with `content_api.is_text(part.mimetype)` or handle the non-text modality directly |
| Pipeline waits until input ends | a stage gathers the whole stream or `CachedProcessor` buffers input | iterate the stream directly or use `CachedPartProcessor` when per-part caching is enough |
| Branch output order is surprising | mixed use of concat/merge/parallel behavior | use `parallel_concat` for ordered branch blocks and `streams.merge` for interleaved earliest-ready output |
| Downstream branch sees mutated parts | `streams.split(..., with_copy=False)` shared the same objects | set `with_copy=True` before processors that mutate metadata/role/substream |
| Cache returns stale output | unchanged `key_prefix` after processor logic changed | version key prefixes, e.g. `extract-v2` |
| Trace files are huge | large image/audio/video parts were captured | set trace `max_size_bytes`, resize images, or trace a shorter fixture |
| Async task cancellation is confusing | generator yielded outside a task-group context or queue bridge was wrong | use processor composition primitives and `context.create_task` rather than ad-hoc background tasks |
| `typing_extensions` missing | runtime imports `override` / `TypedDict` from `typing_extensions` | install `typing_extensions` in the environment |

## Safe text handling

Do not flatten content to text early if a downstream model can handle images,
audio, files, function calls, or custom dataclasses. Flatten only at the output
boundary or when the task is explicitly text-only.

## Substreams

Substreams are routing metadata, not separate Python streams by themselves.
Keep the default substream (`''`) for ordinary prompt/model content and use
named substreams such as `realtime`, `function_call`, `status`, or UI-specific
names only when a processor expects them.

## Cache scope

Cache the most expensive deterministic processor, usually a model call or heavy
fetch/extract stage. Avoid caching prompt assembly or terminal/audio sources.

## Trace scope

Trace a bounded fixture first. For complete apps, trace only the stage under
investigation and keep generated trace artifacts outside the runtime skill tree.
