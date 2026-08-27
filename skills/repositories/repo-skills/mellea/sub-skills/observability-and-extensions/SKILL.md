---
name: observability-and-extensions
description: "Operate and extend Mellea 0.8 observability safely across plugins,
  hooks, logging, metrics, tracing, custom components, and contribution
  boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Mellea observability and extensions

Use this skill for Mellea 0.8.0.dev0 tasks involving plugins, hook ordering or
scope, built-in debug plugins, logging, OpenTelemetry metrics or traces,
generation usage metadata, custom components, extension packaging, or
contribution-safe integration.

## Route first

- Route construction of generative programs, requirements, sampling behavior,
  async execution, and workflow-local components to `generative-programming`.
  Return here when the task is instrumentation or a reusable extension.
- Route `m serve`, service processes, endpoint health, deployment configuration,
  and production CLI operations to `serving-and-cli`. This skill owns the
  library-side signal and exporter boundary, not deployment.
- Read only what the task needs:
  - [plugin and hook API](references/plugin-and-hook-api.md) for registration,
    modes, priority, payload policy, lifecycle, scope, and debug plugins;
  - [telemetry](references/telemetry.md) for logging, metrics, tracing,
    exporters, context, signal timing, and generation metadata;
  - [extension patterns](references/extension-patterns.md) for custom
    components, plugins, backends, packaging, and contribution checks;
  - [troubleshooting](references/troubleshooting.md) for missing dependencies,
    duplicate registration, stale configuration, missing signals, import
    cycles, and API drift.

## Safe operating workflow

1. Establish the lifecycle owner and correlation key before choosing a hook.
   Decide whether the behavior observes, transforms, blocks, or records in the
   background.
2. Check the optional boundary without activating it. Run
   `uv run python scripts/check_telemetry_install.py --require base`; use `hooks` or
   `telemetry` only when that capability is required. The script forces all
   exporters and sinks off.
3. Choose the narrowest registration lifetime. Prefer `plugin_scope(...)`, a
   scoped `PluginSet`, or `start_session(..., plugins=[...])`; use global
   `register(...)` only for process infrastructure with explicit teardown.
4. Use `async def` handlers. Set the execution mode and distinct priorities
   when behavior depends on order. Lower numbers run first within a mode, but
   mode phase precedes numeric priority and equal-priority order is unspecified.
5. Treat hook payloads as immutable. Return `modify(payload, ...)` only from a
   modifying mode and only for fields allowed by that hook's payload policy.
6. Open a span in a pre/start hook, correlate middle events by lifecycle id,
   and close on every success and error/end path. A completion-only hook can
   record a counter or histogram but cannot retrospectively anchor a span.
7. Keep signal setup at the application boundary. Set flags before importing
   Mellea, keep content capture off by default, and never configure an exporter,
   webhook, or file sink in library import code or an availability probe.
8. Test with typed payloads, precomputed thunks, fake backends, in-memory signal
   providers, and deterministic teardown before any provider-backed or
   collector-backed integration case.

## Non-negotiable contracts

- `cpex` is optional and gates registration, payload construction, and plugin
  execution. OpenTelemetry is optional and gates telemetry providers. Base
  Mellea and custom components must remain usable without either dependency.
- Registration state and telemetry providers are process-global. A
  session-owned registration is primarily a teardown lifetime, not proof of
  concurrent-session dispatch isolation.
- Automatic tracing and metrics are hook-fired plugins. Do not add direct
  metric/span calls to core or backend paths when an existing lifecycle plugin
  owns that signal. The narrow exception is synchronous code that cannot safely
  fire a paired hook on the same task.
- Generation metadata must preserve `generation.model` and
  `generation.provider`; `generation.usage` is `None` when unavailable or an
  OpenAI-shaped mapping containing `prompt_tokens`, `completion_tokens`, and
  `total_tokens`. Streaming machinery owns `streaming` and `ttfb_ms`.
- Built-in generation debug plugins log prompt and response previews
  independently of `MELLEA_TRACES_CONTENT`. Treat debug logging as content
  disclosure and scope it deliberately.
- Do not depend on private registry/provider state in an extension. Private
  reset helpers are acceptable only in tightly controlled package tests and
  must be rechecked on version changes.

## Completion report

Report the Mellea version, optional dependency status, signal flags read before
import, plugin registration lifetime, hook modes and priorities, writable-field
use, correlation and error closure, metadata assertions, exporter/content
boundary, teardown, checks run, and any deferred backend or collector evidence.
