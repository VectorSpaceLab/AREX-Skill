# Telemetry, logging, metrics, and tracing

This reference targets Mellea 0.8.0.dev0. Logging is available in the base
package; OpenTelemetry signals are optional. Tracing and metrics are automatic
only when both the telemetry dependencies and the plugin framework are present.

## Configure before import

Mellea imports tracing and metrics during normal package import. Their umbrella
flags are evaluated while those modules initialize. Set signal and exporter
environment variables before the first `import mellea` in a process. Changing a
flag afterward does not rebuild providers or re-register plugins.

OTLP logging differs: its provider is lazily initialized on the first
`get_otlp_log_handler()` call, then cached. The Mellea logger is also a lazy
singleton whose handlers are built on its first `MelleaLogger.get_logger()`
call. Configure logging before those boundaries.

For a side-effect-free capability probe, keep all flags false and use the
bundled checker:

```bash
uv run python scripts/check_telemetry_install.py --require base
uv run python scripts/check_telemetry_install.py --require hooks
uv run python scripts/check_telemetry_install.py --require telemetry
```

The checker removes exporter endpoints, webhooks, and file targets in its own
process. It never enables a provider or sends a signal.

## Dependency and activation matrix

| Capability | Dependency | Activation | Side-effect boundary |
| --- | --- | --- | --- |
| Console/JSON/rotating-file logging | Base Mellea | `MELLEA_LOGS_*`; logging handlers default on | First `MelleaLogger.get_logger()` configures selected handlers. |
| HTTPS webhook logging | Base Mellea | `MELLEA_LOGS_WEBHOOK` | First logger setup creates a network-capable handler. |
| Plugins and built-in debug hooks | `mellea[hooks]` (`cpex`) | Explicit registration or scope | Registration initializes a process-global manager. |
| Tracing | `mellea[telemetry]` | `MELLEA_TRACES_ENABLED=true` | Import builds a provider; console/OTLP exporters require separate flags. |
| Metrics | `mellea[telemetry]` | `MELLEA_METRICS_ENABLED=true` | Import builds a provider and readers, then registers metrics plugins. |
| OTLP logs | `mellea[telemetry]` | `MELLEA_LOGS_OTLP=true` and endpoint | First OTLP-handler request builds a logger provider. |
| Cost metric | `mellea[litellm]` plus metrics | pricing auto-enables with LiteLLM unless explicitly false | Pricing lookup occurs from the completion metrics plugin. |

The telemetry extra includes the hooks extra. A base install still exposes
no-op metric factories and disabled status calls, but it cannot auto-register
hook plugins without `cpex`.

## Environment reference

### General and OTLP endpoints

- `OTEL_SERVICE_NAME` defaults to `mellea`.
- `OTEL_EXPORTER_OTLP_ENDPOINT` is the general gRPC endpoint fallback.
- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`,
  `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`, and
  `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` override the general endpoint for their
  signal.

An umbrella signal flag does not imply export. Tracing may create and discard
spans when no exporter is selected. Metrics warns when enabled without a
working reader. An OTLP flag with no endpoint warns and does not prove export.

### Tracing

| Variable | Meaning | Default |
| --- | --- | --- |
| `MELLEA_TRACES_ENABLED` | Build tracing providers and auto-register tracing plugins | false |
| `MELLEA_TRACES_CONSOLE` | Batch-export spans to console | false |
| `MELLEA_TRACES_OTLP` | Batch-export spans over OTLP gRPC when an endpoint exists | false |
| `MELLEA_TRACES_CONTENT` | Capture selected response, tool, and validation content; may contain sensitive data | false |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | Standard alternative content-capture flag | false |
| `MELLEA_GENERATION_CHUNK_EVENTS` | Emit one `chunk_processed` event per streamed chunk and feed inter-chunk timing | false |

Current content-gated span attributes include action response text, tool
arguments/results, and validation failure reasons, truncated to 500 characters.
The set may expand with API changes, so treat either content flag as permission
to export user/model content generally. Prompt previews from built-in debug
plugins are controlled by logging level and plugin registration, not by this
flag.

### Metrics and pricing

| Variable | Meaning | Default |
| --- | --- | --- |
| `MELLEA_METRICS_ENABLED` | Build the meter provider and auto-register metrics plugins | false |
| `MELLEA_METRICS_CONSOLE` | Periodic console export | false |
| `MELLEA_METRICS_OTLP` | Periodic OTLP gRPC export when an endpoint exists | false |
| `MELLEA_METRICS_PROMETHEUS` | Register a Prometheus metric reader | false |
| `OTEL_METRIC_EXPORT_INTERVAL` | Positive export interval in milliseconds | 60000 |
| `MELLEA_PRICING_ENABLED` | true/false override for LiteLLM-backed pricing | auto when LiteLLM is installed |
| `MELLEA_PRICING_FILE` | JSON pricing overrides in LiteLLM's per-token schema | unset |

An invalid or non-positive metric interval warns and falls back to 60000 ms.
The Prometheus reader only registers with the default registry; the application
or deployment owns the HTTP scrape endpoint. Route that endpoint operation to
`serving-and-cli`.

Pricing is independent of the selected inference backend. It requires token
usage and a known model price. Unknown/private model ids produce no cost record.
Set `MELLEA_PRICING_ENABLED=false` when predictable no-pricing behavior matters.

### Logging

| Variable | Meaning | Default |
| --- | --- | --- |
| `MELLEA_LOGS_ENABLED` | Master switch for Mellea-owned handlers | true |
| `MELLEA_LOGS_LEVEL` | Logger level (`DEBUG`, `INFO`, and so on) | INFO |
| `MELLEA_LOGS_JSON` | Structured JSON formatter | false |
| `MELLEA_LOGS_CONSOLE` | Console handler | true |
| `MELLEA_LOGS_FILE` | Rotating-file path | unset |
| `MELLEA_LOGS_FILE_MAX_BYTES` | Rotation size | 10485760 |
| `MELLEA_LOGS_FILE_BACKUP_COUNT` | Retained backups | 5 |
| `MELLEA_LOGS_OTLP` | Enable OTLP log handler when telemetry and endpoint are available | false |
| `MELLEA_LOGS_WEBHOOK` | HTTPS webhook sink | unset |
| `MELLEA_LOGGER_INSECURE_HTTP_ALLOWED` | Permit HTTP webhook for local development only | false |

The executable 0.8.0.dev0 implementation reads
`MELLEA_LOGGER_INSECURE_HTTP_ALLOWED`; similarly named older documentation
variables are not interchangeable. A bad file path or webhook configuration
warns and leaves other handlers usable. A webhook handler suppresses request
errors so logging does not crash application work, but it is still a real
network sink with retention and disclosure implications.

`MELLEA_LOGS_ENABLED=false` prevents Mellea from attaching its own handlers.
If an application has configured root logger propagation, account for that
separately rather than assuming no record can escape.

## Logging context and trace correlation

Mellea has two scoped context mechanisms:

```python
from mellea.core import log_context
from mellea.telemetry import with_context

with log_context(route="summarize", attempt=2):
    with with_context(
        session_id="s-1",
        request_id="r-7",
        model_id="model-a",
        sampling_iteration=2,
    ):
        ...
```

- `mellea.core.log_context(...)` accepts arbitrary non-reserved fields and
  restores the previous mapping on exit. Use it for application log dimensions.
- `mellea.telemetry.with_context(...)` accepts exactly `session_id`,
  `request_id`, `model_id`, and `sampling_iteration`. It restores prior values,
  enriches logs, and supplies the session id as the GenAI conversation id.
- `async_with_context(...)` has the same contract when `async with` syntax is
  useful; ordinary `with_context(...)` is already safe inside async code.
- Active OpenTelemetry trace/span ids are added to Mellea logs when a valid
  span context exists.

Both mechanisms use `ContextVar`, so nested blocks and independently created
async tasks receive scoped copies. Do not retain a token and reset it from a
different task.

## Hook-fired signal architecture

Automatic lifecycle telemetry follows this direction:

```text
core/backend lifecycle
  -> typed hook payload
     -> tracing or metrics Plugin subclass
        -> signal helper
           -> disabled no-op or configured OpenTelemetry provider/reader
```

Core and backend implementations should fire lifecycle hooks and populate
payload/metadata. They should not call similarly named tracing or metric
helpers directly merely because such helpers exist. Session startup and session
lifetime tracing are a deliberate exception: synchronous session code calls
span helpers directly because OpenTelemetry attach/detach tokens are task-affine
and paired hook dispatch can run in a different task.

Tracing plugins use sequential hooks and priorities 1040-1045. Metrics plugins
use fire-and-forget hooks and priorities 1050-1057. Mode phase ordering means
all sequential tracing work runs before fire-and-forget metrics regardless of
those numeric ranges.

## Generation metadata contract

Every `ModelOutputThunk` carries a `GenerationMetadata` value:

```text
usage: dict[str, object] | None
model: str | None
provider: str | None
ttfb_ms: float | None
streaming: bool
response_model: str | None
finish_reasons: list[str] | None
response_id: str | None
logits: provider/backend dependent
raw_logits: provider/backend dependent
```

Backend authors own normalization at the provider post-processing boundary:

- set `model` to the requested model id and `provider` to a stable provider id;
- set `usage=None` when the provider has no usage evidence;
- otherwise include `prompt_tokens`, `completion_tokens`, and `total_tokens`;
- preserve optional cache/reasoning detail mappings when the provider supplies
  them;
- set response model/id/finish reasons when available;
- do not fabricate token counts from text length.

The thunk streaming machinery sets `streaming` from call options and records
`ttfb_ms` on the first received chunk. A backend must not duplicate that timer.
For raw batch generation, the backend returns aggregate usage separately; it
also fills per-thunk usage only when the provider exposes a defensible split.

Automatic token, duration, error, cost, and backend span attributes are derived
from this metadata. Missing tokens therefore usually indicate a backend
normalization or incomplete-stream problem, not a need for manual metric calls.

## Built-in metrics ownership

The metrics plugin set records:

| Signal | Hook boundary | Important attributes/conditions |
| --- | --- | --- |
| `gen_ai.client.token.usage` | generation or batch post-call | Input/output observations only when normalized usage exists. |
| `gen_ai.client.operation.duration` | post-call or error | Seconds; chat versus text-completion; error duration only after a real call boundary. |
| `gen_ai.client.operation.time_to_first_chunk` | generation post-call | Streaming only when `ttfb_ms` exists. |
| `gen_ai.client.operation.time_per_output_chunk` | `chunk_processed` event | Opt-in; skips the first chunk because no interval exists. |
| `mellea.llm.errors` | generation/batch error and streaming exception | Semantic category plus model/provider/operation and exception class. |
| `mellea.llm.cost.usd` | completion hooks | Only with usage and pricing evidence. |
| sampling attempt/outcome counters | iteration and loop/stream end | Raised loops are not counted as normal sampling outcomes. |
| requirement check/failure counters | validation post and streaming quick check | Exception-only validation has no result count. |
| `mellea.tool.calls` | tool post-invoke | Bounded tool name and success/failure. |
| adapter invocation/phase/parse metrics | completion hooks | Name, revision, outcome, binding/adapter type, and bounded phase. |

Requirement failure metrics can carry a deterministic validation reason; an
LLM-judged failure uses the bounded category `LLM judgment`. If deterministic
reasons contain user text or unbounded detail, normalize them before enabling
that metric in a sensitive or high-volume application.

Application code may create custom instruments safely:

```python
from mellea.telemetry import create_counter, create_histogram

requests = create_counter(
    "myapp.requests", description="Completed application requests", unit="{request}"
)
latency = create_histogram(
    "myapp.request.duration", description="Application request duration", unit="s"
)
requests.add(1, {"route": "summary", "status": "ok"})
latency.record(0.25, {"route": "summary"})
```

Factories return no-op instruments when metrics are disabled. Keep metric
attribute sets bounded: no prompts, responses, arbitrary exception messages,
request ids, user ids, or tool arguments.

## Trace scopes and lifecycle pairs

Mellea uses two instrumentation scopes:

- `mellea.application`: `start_session`, long-lived `session`, `action`,
  `stream`, `execute_tool {name}`, `sampling`, and `validation` spans;
- `mellea.backend`: GenAI `chat` and `text_completion` spans for provider calls.

Paired hook ownership is:

| Span | Open | Events | Close |
| --- | --- | --- | --- |
| Backend chat | generation pre-call | generation chunk event | generation post-call or generation error |
| Backend batch | batch pre-call | — | batch post-call or batch error |
| Action | component pre-execute | — | component post-success or component post-error |
| Stream | streaming start | streaming events | streaming end with success/failure/exception |
| Tool | tool pre-invoke | — | tool post-invoke with success/error |
| Sampling | sampling loop start | iteration and repair | sampling loop end |
| Validation | validation pre-check | — | validation post-check, including exception outcome |

Correlation uses the matching generation/action/streaming/tool/sampling/
validation id, and each close removes the in-flight entry. Error closure is not
optional. Session startup and lifetime spans are opened/closed directly by
synchronous session code for task-affinity reasons.

On Python 3.11 and earlier, hook dispatch through task wrappers can prevent an
attached span context from propagating back to the caller. Mellea still emits
spans and attributes but may flatten parent-child nesting. Python 3.12 supports
the intended nesting. Assert names, ids, status, attributes, and closure before
asserting hierarchy shape.

## Exporter and test boundaries

- Console exporters are diagnostics, not production proof.
- OTLP exporter flags require an endpoint that accepts gRPC. The deployment
  owner controls TLS, authentication, collector routing, batching, and shutdown.
- Prometheus registration does not expose a port by itself.
- Unit tests should use in-memory exporters/readers or patched constructors and
  must not configure reachable endpoints.
- OpenTelemetry global provider setters are effectively one-shot. Consumer
  tests that vary import-time configuration should prefer fresh subprocesses.
  Package-maintainer tests may reset private cached providers/instruments, but
  those helpers are version-sensitive and not extension API.
- Fire-and-forget metric handlers need an explicit background-task drain in
  assertion-based tests.
- Provider shutdown, plugin shutdown, cached-instrument cleanup, and in-flight
  span cleanup must occur even after an exception.
