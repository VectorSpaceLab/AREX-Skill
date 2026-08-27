# Plugin and hook operating reference

This reference targets the public Mellea 0.8.0.dev0 plugin surface. Use typed
Mellea APIs; do not couple an extension to ContextForge registry internals.

## Optional dependency boundary

The public facade is importable from a base installation:

```python
from mellea.plugins import (
    HookType,
    Plugin,
    PluginMode,
    PluginSet,
    PluginViolationError,
    block,
    hook,
    modify,
    plugin_scope,
    register,
    unregister,
)
```

Defining `Plugin` subclasses and decorating async functions does not require
ContextForge. Registration, unregistration, payload construction, `modify()`,
`block()`, and actual dispatch require `cpex`, supplied by the `hooks` extra:

```bash
uv add 'mellea[hooks]'
```

`MelleaPlugin` is the lower-level framework-aware base and is imported from
`mellea.plugins.base`, not from the facade. Instantiating it also requires
`cpex`. Prefer a standalone hook or `Plugin` subclass unless framework
configuration/lifecycle is truly needed.

## Choose a plugin shape

| Need | Shape | Important contract |
| --- | --- | --- |
| One observer, gate, or transform | standalone `@hook` coroutine | Registered name is its module-qualified function name. |
| Several hooks sharing state | named `Plugin` subclass | Each decorated method is registered through its own adapter. Make shared `initialize()`/`shutdown()` idempotent because it can be called once per method adapter. |
| Reusable composition | `PluginSet(name, items, priority=...)` | Inert until registered; nested sets flatten recursively. An outer non-`None` priority overrides nested item priorities. |
| Framework config or typed accessors | `MelleaPlugin` | Requires a framework `PluginConfig`; full backend/session/context objects exist only when the firing site put them in global context. Do not assume they are always present. |
| Temporary activation | `plugin_scope(...)`, a plugin context manager, or a `PluginSet` context manager | Registers on entry and deregisters in `finally` on exit. Do not concurrently or recursively enter the same plugin/set instance. |

A lightweight standalone observer:

```python
from typing import Any

from mellea.plugins import HookType, PluginMode, hook


@hook(HookType.GENERATION_POST_CALL, mode=PluginMode.AUDIT, priority=60)
async def observe_completion(payload: Any, context: Any) -> None:
    usage = payload.model_output.generation.usage
    if usage is not None:
        print(usage.get("total_tokens"))
```

Handlers must be `async def`; the decorator rejects a regular function at
definition time. Returning `None` is a no-op. Return `modify(...)` for a
permitted transform or `block(...)` for an enforcing gate.

## Registration lifetime and scope

| API | Lifetime | Use it for |
| --- | --- | --- |
| `register(item)` | Global until explicit unregister or manager shutdown | Process infrastructure configured once by the application. |
| `unregister(item)` | Removes an item's registered adapter name(s) | Global teardown; silently ignores a known item that is already absent. |
| `with plugin_scope(items):` | One sync or async block | Safest default for a diagnostic, test, or bounded operation. |
| `with PluginSet(...):` / `with Plugin(...):` | One sync or async block | Reusable grouped or stateful behavior. The same instance may be reused only after exit. |
| `start_session(..., plugins=[...])` | Registration through `session.cleanup()` | Session-owned teardown. Registration occurs after backend construction and `session_pre_init`, but before `session_post_init`. |
| `register(item, session_id=sid)` | Until the matching session-id deregistration | Low-level ownership mechanism used by the scoped APIs. |

A session id tags registered names for later deregistration. In this version it
is not a per-invocation predicate: a tagged plugin resides in the same
process-global manager and may observe dispatches while it is registered. Do
not use it as proof of isolation between concurrently active sessions. If
strict tenant/session filtering is required, inspect the typed payload's
session/request metadata inside the handler and reject unrelated events, or use
separate processes.

`start_session(..., plugins=[...])` does not let those plugins modify session
pre-initialization because backend setup has already begun. Register a truly
process-level `session_pre_init` transform before calling `start_session`, and
unregister it deterministically.

## Execution modes, phase order, and enforcement

Dispatch phases run in this order, regardless of numeric priorities in another
phase:

```text
SEQUENTIAL -> TRANSFORM -> AUDIT -> CONCURRENT -> FIRE_AND_FORGET
```

| Mode | Serial/parallel | Modify allowed | Block allowed | Typical use |
| --- | --- | --- | --- | --- |
| `SEQUENTIAL` | Serial, chained | Yes, subject to field policy | Yes; stops later phases | Policy gates and ordered mutation. |
| `TRANSFORM` | Serial, chained | Yes, subject to field policy | No; a block result is suppressed | Deterministic request rewriting. |
| `AUDIT` | Serial | No | No; violations are observational | Ordered logging/audit work. |
| `CONCURRENT` | Parallel within the phase | No, to avoid races | Yes | Independent fail-fast checks. |
| `FIRE_AND_FORGET` | Background task | No | No | Non-blocking metrics or best-effort observers. |

Within one mode, lower numeric priority runs first. Effective priority is:

```text
PluginSet override > @hook priority > Plugin class priority > 50
```

Equal-priority order is unspecified. If one handler must see another handler's
accepted transform, put both in a modifying mode and assign distinct
priorities. A priority cannot move an audit handler ahead of a transform
handler because mode phase comes first.

Fire-and-forget completion occurs after the main invocation can return. A test
must opt into manager background-result collection and drain it before
asserting side effects. Do not make production metrics sequential just to make
a test deterministic.

## Immutable payload and writable-field policy

Payloads derive from frozen `MelleaBasePayload` values. Base metadata includes
`session_id`, `request_id`, `timestamp`, `hook`, and `user_metadata`. Treat both
the payload and nested user-owned values as immutable; use copy-on-write.

Mellea applies two gates to a proposed update:

1. only `SEQUENTIAL` and `TRANSFORM` modes can modify;
2. the hook-specific policy accepts only listed fields.

The 0.8.0.dev0 writable set is:

| Hook | Writable fields |
| --- | --- |
| `session_pre_init` | `model_id`, `model_options` |
| `component_pre_execute` | `requirements`, `model_options`, `format`, `strategy`, `tool_calls_enabled` |
| `generation_pre_call` | `model_options`, `tool_calls`, `format` |
| `generation_batch_pre_call` | `model_options`, `tool_calls`, `format` |
| `validation_pre_check` | `requirements`, `model_options` |
| `validation_post_check` | `results`, `all_validations_passed` |
| `sampling_loop_start` | `loop_budget` |
| `tool_pre_invoke` | `model_tool_call` |
| `tool_post_invoke` | `tool_output` |

Every unlisted hook is observe-only under the default-deny policy. Attempts to
change read-only fields are discarded, often without an exception. Inspect the
payload returned by dispatch rather than assuming the requested copy became
authoritative.

```python
from typing import Any

from mellea.plugins import HookType, PluginMode, hook, modify


@hook(HookType.GENERATION_PRE_CALL, mode=PluginMode.TRANSFORM, priority=20)
async def add_temperature(payload: Any, context: Any) -> Any:
    options = dict(payload.model_options)
    options.setdefault("temperature", 0.2)
    return modify(payload, model_options=options)
```

Use `block(reason, code=..., details=...)` only where enforcement is intended.
A sequential violation reaches the caller as `PluginViolationError` with
`hook_type`, `reason`, `code`, and `plugin_name`.

## Hook families and lifecycle correlation

Use the enum member or its wire value with `@hook`.

| Family | Start/pre | Middle or completion | Error/end | Correlation |
| --- | --- | --- | --- | --- |
| Session | `session_pre_init`, `session_post_init` | `session_reset` | `session_cleanup` | `session_id` |
| Component/action | `component_pre_execute` | `component_post_success` | `component_post_error` | `action_id` |
| Generation/chat | `generation_pre_call` | `generation_event`, `generation_post_call` | `generation_error` | `generation_id` |
| Generation/batch | `generation_batch_pre_call` | `generation_batch_post_call` | `generation_batch_error` | `generation_id` |
| Validation | `validation_pre_check` | — | `validation_post_check` carries normal or exception outcome | `validation_id` |
| Sampling | `sampling_loop_start` | `sampling_iteration`, `sampling_repair` | `sampling_loop_end` | `sampling_id` |
| Tool | `tool_pre_invoke` | — | `tool_post_invoke` carries success/error | `tool_invocation_id` |
| Streaming orchestration | `streaming_start` | `streaming_event` | `streaming_end` carries all outcomes | `streaming_id` |
| Adapter function | — | `adapter_function_phase_complete` | `adapter_function_invocation_complete` | name/revision plus phase/outcome |

Completion payloads often carry an `exception` field rather than using a
separate error hook. Read the payload contract before deciding whether success
and error are separate hook types.

Generation is lazy. `generation_pre_call` fires before backend dispatch, while
`generation_post_call` normally fires only when an uncomputed
`ModelOutputThunk` finishes materializing and post-processing. A backend that
returns an already-computed thunk can bypass that completion hook. For custom
backends that need paired generation spans, preserve the uncomputed-thunk
contract or instrument the real completion boundary; never leave a span open
waiting for a hook that cannot fire.

## Span lifecycle versus completion metrics

A span represents elapsed work, so it needs a real open boundary and a close on
every terminal path:

```text
pre/start: create span, stash by correlation id
middle:    add events/attributes to the same id
success:   pop, add result metadata, end
error:     pop, record exception/status, end
```

A post-only adapter-function hook can record an invocation counter or phase
duration because the payload already contains the measured result. It cannot
start a meaningful span after the operation has completed. Add a paired start
hook before adding a span, or use a metric.

## Built-in debug plugins

The `mellea.plugins.builtin_debug` package exports generation, validation, and
sampling hooks:

- generation pre/post: model, generation id, latency, token summary, prompt and
  response previews, and repair feedback;
- validation pre/post: requirement count, target type, pass/fail results,
  reasons, and score when available;
- sampling start/iteration/repair/end: strategy, budget, failed requirements,
  repair events, attempts, and outcome.

Use temporary activation rather than global import-time registration:

```python
import logging

from mellea.plugins import PluginSet, plugin_scope
from mellea.plugins.builtin_debug import (
    log_generation_post_call,
    log_generation_pre_call,
    log_sampling_iteration,
    log_sampling_loop_end,
    log_sampling_loop_start,
    log_validation_post_check,
    log_validation_pre_check,
)

logging.getLogger("mellea.plugins.builtin_debug").setLevel(logging.DEBUG)
diagnostics = PluginSet(
    "bounded-diagnostics",
    [
        log_generation_pre_call,
        log_generation_post_call,
        log_validation_pre_check,
        log_validation_post_check,
        log_sampling_loop_start,
        log_sampling_iteration,
        log_sampling_loop_end,
    ],
)

with plugin_scope(diagnostics):
    ...
```

These debug hooks use ordinary Python logging and are sequential by default.
Generation logs can expose the first 100 characters of prompts/responses, and
validation/sampling logs can expose requirement text and failure reasons. The
OpenTelemetry content-capture flag does not redact them. Enable them only for a
controlled diagnostic window and configure handler retention independently.

## Test isolation checklist

- Use uniquely named functions/classes; registry keys collide on
  module-qualified function names or `plugin-name.hook-value` adapter names.
- Start from a clean manager and shut it down after the case.
- Construct the exact typed payload where possible; invoke a hook function
  directly for pure unit behavior and use manager dispatch only for mode,
  priority, policy, registration, or scope behavior.
- Assert both the accepted result and the rejected read-only updates.
- For fire-and-forget, drain collected background tasks before assertions and
  discard stale tasks between event loops.
- Test normal and error terminal hooks for every span; assert the correlation
  entry is removed in both cases.
- Avoid live models, credentials, collectors, webhooks, and real file sinks in
  plugin unit tests.
