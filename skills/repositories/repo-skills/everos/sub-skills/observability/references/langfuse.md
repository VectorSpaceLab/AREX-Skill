# Langfuse Reference

## Configure Langfuse export

Install `everos[otel]`, then configure:

```toml
[observability]
enabled = true
langfuse_public_key = "pk-lf-..."
langfuse_secret_key = "sk-lf-..."
langfuse_host = "https://us.cloud.langfuse.com"
# capture_content = true  # opt-in only
```

When `langfuse_*` keys are set, EverOS derives the OTLP traces endpoint `<host>/api/public/otel/v1/traces` and Basic auth header unless an explicit `endpoint` or `headers` override is provided.

## Recall scores

EverOS can push recall-quality scores to Langfuse's REST scores API when `emit_recall_scores` is true and Langfuse keys/host are configured.

Score names:

| Name | Meaning |
|---|---|
| `recall_top_score` | Calibrated top score for HYBRID/AGENTIC. |
| `recall_hit` | Boolean hit score for calibrated methods. |
| `recall_top_score_raw` | Raw uncalibrated score for KEYWORD/single-route VECTOR. |

Do not average raw and calibrated score names together.

## Demo choices

Use the bundled `trace_demo_driver.py --run-flow` when you already have a configured EverOS server and want a tiny live request sequence to generate spans.

The original Langfuse example also included a large trace replay workflow and a maintainer-side recorder. Those are credential/network-bound and are represented here as guidance rather than default scripts. Replay is useful to preview Langfuse UI without running EverOS; live tracing is the correct validation for your own deployment.

## Credential boundaries

Langfuse keys are region-scoped. If a host rejects credentials, try the matching regional host for the project. Never paste Langfuse secrets into prompts, logs, generated artifacts, or command histories that will be shared.
