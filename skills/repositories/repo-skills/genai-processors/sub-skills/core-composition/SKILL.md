---
name: core-composition
description: "Build GenAI Processors pipelines with content, streams, routing,
  caching, and tracing."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Core composition

Use this sub-skill for the mechanics of GenAI Processors: content wrappers,
custom processors, stream transformations, branching, caching, and debugging.

## Read when

- The task asks how to create a `Processor` or `PartProcessor`.
- The task mentions `ProcessorPart`, `ProcessorContent`, `ContentStream`,
  MIME types, roles, metadata, or substreams.
- The task needs `+`, `//`, `parallel_concat`, `Switch`, `PartSwitch`,
  `streams.split`, `streams.merge`, or queue-based stream wiring.
- The task needs `CachedProcessor`, `CachedPartProcessor`, `SqlCache`, tracing,
  or a safe local smoke check.

## Boundaries

This sub-skill owns library plumbing and reusable processor patterns. It does
not own model credentials, audio/video device setup, or full example app wiring:

- Route model wrappers and tool calling to `../model-backends/`.
- Route audio/video/PDF/web/Drive/GitHub sources to `../multimodal-i-o/`.
- Route CLI demos, AI Studio applets, and full applications to
  `../examples-and-apps/`.

## Core workflow

1. Start with content shape: text-only, multimodal, dataclass/proto, function
   call/response, or device/document parts.
2. Pick `Processor` for stream-wide/stateful logic, or `PartProcessor` for
   independent per-part logic.
3. Accept broad inputs at call sites; implement against `processor.ProcessorStream`.
4. Use `+` for sequential chains and `//` only for independent part processors.
5. Use `parallel_concat` or `streams.split`/`merge` only when the ordering and
   concurrency behavior matches the user-visible result.
6. Add `Switch` / `PartSwitch` for substream or mimetype routing.
7. Add cache/tracing last, after the uncached pipeline is correct.
8. Validate with `scripts/smoke_core.py` or the root `scripts/check_install.py`.

## References and scripts

- `references/api-reference.md` lists the public core classes, decorators,
  stream utilities, and helper modules.
- `references/workflows.md` gives end-to-end patterns for custom processors,
  stream routing, caching, and tracing.
- `references/troubleshooting.md` covers common mistakes with MIME types,
  `.text`, caches, task groups, and trace size.
- `scripts/smoke_core.py` runs a safe in-process processor/stream smoke test.

## Native evidence anchors

Behavior is backed by the core package source and tests such as
`content_api_test.py`, `processor_test.py`, `streams_test.py`, `switch_test.py`,
`cache_test.py`, `sql_cache_test.py`, `map_processor_test.py`,
`mime_types_test.py`, `context_test.py`, `debug_test.py`, `preamble_test.py`,
`constrained_decoding_test.py`, and `trace_file_test.py`.

## Usability checkpoints

A good answer using this sub-skill should:

- Preserve multimodal parts unless the user explicitly wants text only.
- State when an operation buffers a stream versus preserving streaming behavior.
- Show concrete imports and processor composition code.
- Include validation steps that do not require remote models or hardware.
- Link to sibling sub-skills only when the task crosses into models, I/O, or
  complete examples.
