# Core API reference

## Content objects

| API | Use |
| --- | --- |
| `content_api.ProcessorPart(value, role='', substream_name='', mimetype=None, metadata=None)` | Wrap one text, bytes, PIL image, GenAI `Part`, `File`, function call/response, or existing part. Bytes require a MIME type. |
| `content_api.ProcessorContent(...)` | Gather many parts into a list-like content object. Use for whole prompts, full model responses, or cached payloads. |
| `content_api.ContentStream(parts=..., content=...)` | Async stream mixin with `.text()` and `.gather()`. `ProcessorStream` extends it with trace metadata. |
| `content_api.is_text`, `is_audio`, `is_image`, `is_video`, `is_dataclass`, `is_end_of_turn` | Validate part types before narrowing. |
| `content_api.to_genai_contents` | Convert gathered processor content back into Gemini SDK `Content` objects. |

Best practice: pass user inputs directly when possible. Strings, existing
`ProcessorPart`s, and lists of parts are normalized by the framework. Do not
wrap strings manually unless you need role, substream, MIME type, or metadata.

## Processor classes and decorators

| API | Use |
| --- | --- |
| `processor.Processor` | Subclass when logic sees a whole stream, keeps state, calls a model, or buffers context. Override `call(self, content)`. |
| `processor.PartProcessor` | Subclass when each part can be transformed independently. Override `match` and `call(self, part)`. |
| `@processor.processor_function` | Convert a stateless async stream function into a `Processor`. |
| `@processor.part_processor_function(match_fn=...)` | Convert a stateless async per-part function into a `PartProcessor`. Use `match_fn` for safety and performance. |
| `processor.create_filter(fn)` | Convert a part predicate into a filter processor. |
| `processor.yield_exceptions_as_parts` | Wrap a processor call so exceptions are yielded as error parts instead of escaping. |

Implementation signature differs from call signature: callers can pass broad
`ProcessorContentTypes`, but implementations receive a `ProcessorStream` and
yield broad `ProcessorPartTypes`.

## Composition and stream utilities

| API | Behavior |
| --- | --- |
| `p1 + p2` | Sequential chain; preferred for normal pipelines. |
| `part_p1 // part_p2` | Parallel per-part execution, concatenating results for each input part. |
| `processor.parallel_concat([p1, p2])` | Broadcast stream to processors concurrently, then concatenate outputs by processor order. |
| `streams.split(content, n=2, with_copy=False)` | Create independent iterators over one stream. Use `with_copy=True` if downstream mutates parts. |
| `streams.concat(a, b, ...)` | Compute streams concurrently but emit all of `a`, then all of `b`, etc. |
| `streams.merge(a, b, ..., stop_on_first=False)` | Emit whichever stream produces parts first; preserves order only within each stream. |
| `streams.enqueue` / `streams.dequeue` | Bridge queues and async streams for loops, external callbacks, or long-running apps. |
| `streams.endless_stream()` | Keep sources alive until cancelled; useful for live input pipelines. |

## Routing

- `switch.Switch(key_fn).case(key, processor).default(processor)` routes whole
  stream parts by a key such as MIME type or substream name.
- `switch.PartSwitch().case(match_fn, processor).default(processor)` does
  per-part concurrent routing and is useful in part-processor stacks.

## Prompt, template, structured-output helpers

- `core.preamble.Preamble(content=..., content_factory=...)` prepends content.
- `core.preamble.Suffix(content=..., content_factory=...)` appends content.
- `core.jinja_template.JinjaTemplate(template_str, content_varname='content')`
  renders prompts or verbalizations.
- `core.jinja_template.RenderDataClass`, `RenderJson`, and `RenderProtoMessage`
  convert structured parts into templated text.
- `core.constrained_decoding.StructuredOutputParser(schema)` parses streamed JSON
  text into dataclass or enum parts when models produce structured output.

## Caching and tracing

- `processor.CachedPartProcessor` caches each matching part separately and
  preserves streaming around independent transformations.
- `processor.CachedProcessor` buffers the full input and caches the whole result;
  use it for expensive full-context calls only.
- `cache.InMemoryCache` is volatile. `sql_cache.SqlCache` is persistent via
  SQLAlchemy and useful for long-running development loops.
- `dev.trace_file.SyncFileTrace(trace_dir=..., name=...)` records processor
  calls, inputs, outputs, nested traces, errors, and cancellations as JSON/HTML.
