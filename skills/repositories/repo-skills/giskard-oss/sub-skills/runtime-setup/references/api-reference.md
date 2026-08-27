# Runtime Setup API Reference

## Package and import boundaries

Giskard OSS v3 requires Python `>=3.12` and is distributed as small packages
under a shared namespace. Do not import underscore-style package names such as
`giskard_checks`; use the dotted namespace imports.

| Distribution | Import namespace | Purpose |
| --- | --- | --- |
| `giskard` | `giskard.<sublib>` namespace only | Public meta-distribution that installs the default eval stack. It is not the v2 monolithic top-level API. |
| `giskard-core` | `giskard.core` | Shared telemetry, rate limiting, discriminated unions, errors, and version helpers. |
| `giskard-llm` | `giskard.llm` | Provider-agnostic LLM routing and async completion/embedding/response helpers. |
| `giskard-agents` | `giskard.agents` | Agent workflow, generator, tool, template, and middleware APIs. |
| `giskard-checks` | `giskard.checks` | Scenarios, suites, deterministic checks, LLM judges, input generators, and export helpers. |
| `giskard-scan` | `giskard.scan` | Vulnerability scan, quality scan, scan generators, knowledge bases, and optional scanner bridges. |

The root `giskard` distribution is a v3 meta-distribution/shim. Usable v3 APIs
live in the submodules above. If code expects v2 top-level objects such as
`giskard.Model`, `giskard.Dataset`, or a top-level `giskard.scan(...)` function,
treat that as a legacy-v2 workflow and do not mix it into the same environment
as the v3 split namespace unless the user explicitly accepts that separation.

## Core exports

Import core utilities from `giskard.core`:

```python
from giskard.core import (
    BaseRateLimiter,
    Discriminated,
    Error,
    GISKARD_LIBS_VERSIONS,
    MinIntervalRateLimiter,
    disable_telemetry,
    discriminated_base,
    get_lib_version,
    telemetry_capture,
    telemetry_run_context,
    telemetry_tag,
)
```

| Symbol | Contract |
| --- | --- |
| `get_lib_version(lib: str, default: str = "unknown") -> str` | Return an installed distribution version, or `default` when it is not installed. |
| `GISKARD_LIBS_VERSIONS` | Dict keyed by `giskard-core`, `giskard-checks`, `giskard-scan`, `giskard-agents`, and `giskard-llm`; missing packages use `not_installed`. |
| `Error(message: str)` | Pydantic model for serializable errors; `str(Error(message="x"))` is `ERROR: x`. |
| `Discriminated` / `discriminated_base` | Pydantic-compatible discriminated union base. Subclasses registered with `.register("kind")` validate from dicts containing a string `kind`. |
| `BaseRateLimiter` | Abstract async rate-limiter base with `throttle()` and `BaseRateLimiter.from_id(id)`. Instances with the same id and fields share state. |
| `MinIntervalRateLimiter` | Built-in limiter with `min_interval >= 0`, optional `max_concurrent >= 1`, async `throttle()`, and `from_rpm(rpm, max_concurrent=None, id=None)`. |
| `disable_telemetry()` | Disable telemetry and GeoIP enrichment for the current process. Prefer env-var opt-out before import when no local anonymous ID should be created. |
| `telemetry_run_context()` | Context manager for a logical operation; inside it, telemetry helpers share a consistent scope. |
| `telemetry_tag(name, value)` | Attach non-sensitive dimensions to telemetry context. Do not tag prompts, outputs, secrets, or paths. |
| `telemetry_capture(event, properties=None)` | Capture an event only when a telemetry run context is active; outside that context it returns without sending. |

## Telemetry controls

Truth-like values (`1`, `true`, `yes`, `on`, `t`, `y`, case-insensitive) are
recognized for opt-out environment variables. Set these before any `giskard.*`
import when privacy-first behavior is required:

| Variable | Effect |
| --- | --- |
| `DO_NOT_TRACK` | Fully disables Giskard telemetry. |
| `GISKARD_TELEMETRY_DISABLED` | Fully disables Giskard telemetry. |
| `GISKARD_TELEMETRY_DISABLE_GEOIP` | Keeps usage telemetry enabled but disables GeoIP enrichment. Fully disabled telemetry also disables GeoIP. |

Runtime calls to `disable_telemetry()` stop further sends in the current process,
but env-var opt-out before import is the safer first step for tests, notebooks,
and reproducible smoke checks.

## Rate limiter details

`MinIntervalRateLimiter.from_rpm(rpm, max_concurrent=None, id=None)` converts
requests-per-minute to `min_interval = 60.0 / rpm`. `rpm` must be positive.
`max_concurrent`, when provided, must be at least `1`.

Use a stable `id` only when multiple components should intentionally share
limiter state. Reusing the same `id` with different limiter fields raises a
validation error by default because `BaseRateLimiter.from_id(id)` would become
ambiguous. If a user knowingly wants duplicate-id warnings instead of errors,
set `GISKARD_DISABLE_DUPLICATE_RATE_LIMITERS_WARNINGS=1` before importing
`giskard.core`.

## Discriminated-union details

A base class must be decorated with `@discriminated_base`, and concrete
subclasses are registered from that base:

```python
from giskard.core import Discriminated, discriminated_base

@discriminated_base
class Step(Discriminated):
    pass

@Step.register("message")
class MessageStep(Step):
    text: str

step = Step.model_validate({"kind": "message", "text": "hello"})
assert isinstance(step, MessageStep)
assert step.kind == "message"
```

Validation fails when the input is not a dict, when `kind` is missing, when
`kind` is not a string, or when the kind has not been registered for the base.
