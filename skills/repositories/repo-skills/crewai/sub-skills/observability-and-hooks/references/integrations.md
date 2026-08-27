# Observability Integrations

CrewAI observability can be configured through built-in CrewAI tracing, the package's OpenTelemetry-based anonymous telemetry, third-party auto-instrumentation, or SDKs that wrap LLM/provider calls. This reference summarizes provider patterns and safe boundaries without requiring the original repository checkout.

## Integration Strategy

Choose the integration layer by desired outcome:

- Built-in CrewAI traces: use `Crew(..., tracing=True)` or `Flow(..., tracing=True)` plus CrewAI authentication/dashboard setup when the user wants CrewAI-hosted execution traces.
- Local-only debugging: use `output_log_file`, latest task-output storage, event listeners, or hooks, and disable hosted telemetry/tracing when necessary.
- OpenTelemetry-native observability: use tools such as OpenLIT, Braintrust OTEL, Phoenix/OpenInference, or provider OTLP exporters when the user's infrastructure expects OTLP spans/metrics.
- LLM gateway observability: use Portkey or LangDB when model calls should go through a gateway that also captures traces, cost, and reliability metadata.
- Vendor LLM observability: use Datadog, Langfuse, Langtrace, Opik, Weave, MLflow, Galileo, Maxim, Neatlogs, TrueFoundry, or similar when the user already has that provider and credentials.
- Evaluation/quality monitoring: use Patronus-style evaluation integrations when the primary goal is output quality checks rather than raw trace capture.

## Built-In CrewAI Tracing

Built-in tracing is controlled at the Crew/Flow level or by `CREWAI_TRACING_ENABLED`. It can capture execution events, tool usage, LLM calls, and performance metadata for CrewAI's trace UI when the user has configured authentication.

Credential-bound operations:

- Hosted CrewAI dashboard tracing requires user account/authentication setup.
- Do not run `crewai login`, open dashboards, or send hosted traces unless the user asks for hosted tracing or has already approved it.
- For local/no-network work, set `tracing=False` on the Crew/Flow being run and disable anonymous telemetry env vars.

## OpenLIT / OTLP Pattern

OpenLIT is an OpenTelemetry-native approach for monitoring CrewAI applications. The common pattern is:

```python
import openlit

openlit.init(otlp_endpoint="http://127.0.0.1:4318")

# Import/configure CrewAI and run crews after instrumentation is initialized.
```

Environment-based OTLP setup uses:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://127.0.0.1:4318"
```

Troubleshooting notes:

- OTLP HTTP receivers often use port `4318`; OTLP gRPC receivers often use `4317`. Endpoint/protocol mismatches are a common cause of missing spans.
- Initialize instrumentation before constructing or running the CrewAI application when the provider docs require it.
- `OTEL_SDK_DISABLED=true` disables OpenTelemetry SDK telemetry in CrewAI's own telemetry path and can also affect OTEL-based integrations depending on their SDK behavior.

## Datadog Pattern

Datadog's LLM Observability path uses `ddtrace` auto-instrumentation. Typical environment variables are:

```bash
export DD_API_KEY="..."
export DD_SITE="..."
export DD_LLMOBS_ENABLED=true
export DD_LLMOBS_ML_APP="my-crew-app"
export DD_LLMOBS_AGENTLESS_ENABLED=true
export DD_APM_TRACING_ENABLED=false
```

Run the app under Datadog auto-instrumentation:

```bash
ddtrace-run python crewai_agent.py
```

Boundaries:

- Datadog requires credentials and can transmit LLM observability data to Datadog; get user approval before running.
- Provider LLM API keys may also be required for the actual CrewAI run; do not infer or print them.
- If APM tracing is disabled but LLM observability is enabled, check the Datadog env vars first before changing CrewAI code.

## Langfuse Pattern

Langfuse examples pair Langfuse credentials with OpenLIT instrumentation:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

```python
import openlit
openlit.init()
```

Notes:

- Langfuse credentials are secrets; never echo real values into logs.
- Host/region mismatch can make traces appear missing even when SDK initialization succeeds.
- Initialize tracing before the CrewAI run.

## LangDB Pattern

LangDB is an OpenAI-compatible gateway plus observability platform. It is typically initialized before CrewAI imports or model construction:

```bash
export LANGDB_API_KEY="..."
export LANGDB_PROJECT_ID="..."
export LANGDB_API_BASE_URL="https://api.us-east-1.langdb.ai"
```

```python
from pylangdb.crewai import init
init()
```

LLM calls may then use LangDB's base URL and project headers. If no traces appear, confirm `init()` ran before CrewAI imports and that gateway env vars are present.

## Phoenix / OpenInference Pattern

Phoenix/OpenInference-style setups commonly install CrewAI instrumentation packages and configure Phoenix collector headers/endpoints, for example:

```bash
export PHOENIX_CLIENT_HEADERS="api_key=..."
export PHOENIX_COLLECTOR_ENDPOINT="https://app.phoenix.arize.com"
```

Use a self-hosted Phoenix collector endpoint when the user wants local infrastructure. Check whether the instrumentation is intended to wrap CrewAI directly or provider calls.

## Portkey Pattern

Portkey is primarily an AI gateway. CrewAI typically sends LLM traffic through a Portkey base URL and headers:

```python
from crewai import LLM
from portkey_ai import PORTKEY_GATEWAY_URL, createHeaders

llm = LLM(
    model="gpt-4o-mini",
    base_url=PORTKEY_GATEWAY_URL,
    api_key="provider-api-key-or-portkey-config",
    additional_params={
        "extra_headers": createHeaders(api_key="PORTKEY_API_KEY"),
    },
)
```

Boundaries:

- Gateway integrations can change provider routing, retries, and logging. Use the LLM/provider sub-skill during whole-skill integration for provider/base URL compatibility.
- Do not hardcode real API keys or gateway headers in public examples.

## Weave, Opik, MLflow, Braintrust, Langtrace, and Similar SDKs

Most provider SDK patterns are one of:

1. Install provider SDK plus CrewAI/OpenTelemetry instrumentation.
2. Set provider API key/project/env variables.
3. Initialize the SDK before running the CrewAI workload.
4. Run a small approved workload and inspect the provider UI/dashboard.

Examples of provider-specific signals:

- Weave: `weave.init(project_name="...")` before running the crew.
- Opik: install `opik` with CrewAI packages, configure Opik credentials/project, then run traced crew code.
- MLflow: initialize MLflow tracing/evaluation in the app process before CrewAI execution.
- Braintrust: OTEL-oriented package setup with CrewAI and OpenTelemetry instrumentation.
- Langtrace: SDK init with `LANGTRACE_API_KEY` or direct `api_key` before app execution.

## Patronus Evaluation Pattern

Patronus is positioned for evaluation/quality assurance. Treat it separately from low-level tracing:

- Configure Patronus credentials only when the user asks for evaluation or monitoring through Patronus.
- Avoid running evaluation jobs automatically; they can send prompts/outputs to a third party.
- Use hooks or output logs to prepare local redacted samples before sending any data.

## Integration Safety Checklist

Before running any integration that may emit traces:

- Confirm whether the user wants local-only diagnostics or external provider telemetry.
- Identify which env vars are required and which are secrets.
- Confirm initialization order: many providers require `init()` before CrewAI imports, LLM construction, or kickoff.
- Confirm endpoint/protocol: OTLP HTTP `4318` vs OTLP gRPC `4317`; HTTPS/cloud endpoints vs local collectors.
- Confirm data scope: default anonymous telemetry, full `share_crew` telemetry, prompt/response traces, tool results, and task outputs have different privacy impact.
- Prefer a minimal synthetic crew with no sensitive inputs when testing provider wiring.
- Record skipped provider checks as credential-bound rather than trying to fake success.

## Common Provider Environment Variables

| Provider/pattern | Common variables | Notes |
| --- | --- | --- |
| CrewAI built-in tracing | `CREWAI_TRACING_ENABLED`, `CREWAI_USER_ID`, `CREWAI_ORG_ID` | Hosted trace visibility requires CrewAI auth/configuration. |
| CrewAI telemetry disable | `OTEL_SDK_DISABLED`, `CREWAI_DISABLE_TELEMETRY`, `CREWAI_DISABLE_TRACKING` | Use for local/no-network runs. |
| Generic OTLP | `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_PROTOCOL`, `OTEL_SERVICE_NAME` | Match protocol and port to collector. |
| Datadog | `DD_API_KEY`, `DD_SITE`, `DD_LLMOBS_ENABLED`, `DD_LLMOBS_ML_APP`, `DD_LLMOBS_AGENTLESS_ENABLED`, `DD_APM_TRACING_ENABLED` | Usually run with `ddtrace-run`. |
| Langfuse | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | Often paired with OpenLIT/OTEL setup. |
| LangDB | `LANGDB_API_KEY`, `LANGDB_PROJECT_ID`, `LANGDB_API_BASE_URL` | Init before CrewAI imports when required. |
| Phoenix | `PHOENIX_CLIENT_HEADERS`, `PHOENIX_COLLECTOR_ENDPOINT` | Cloud vs self-hosted endpoint matters. |
| Patronus | `PATRONUS_API_KEY` | Evaluation-focused; can transmit outputs. |
| Portkey | `PORTKEY_API_KEY` plus provider keys/config | Gateway base URL changes LLM routing. |

## When to Route Elsewhere

- Exact CLI invocations such as `crewai traces`, `crewai log-tasks-outputs`, and deployment/auth commands: [cli-and-projects](../../cli-and-projects/SKILL.md).
- LLM provider base URLs, OpenAI-compatible model construction, Azure/Bedrock/Anthropic/Google provider setup: route to the LLM/provider sub-skill during whole-skill integration.
- Tool implementation and MCP integration internals: [tools-and-mcp](../../tools-and-mcp/SKILL.md).
- Flow graph design and event graph semantics: [flows-and-events](../../flows-and-events/SKILL.md).
