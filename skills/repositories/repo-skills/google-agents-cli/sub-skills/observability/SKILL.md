---
name: observability
description: "Use this sub-skill when adding or debugging observability for
  agents-cli projects, including Cloud Trace, Cloud Logging, prompt-response
  logging, BigQuery Agent Analytics, and third-party telemetry."
metadata:
  disco-role: operating
  author: Google
  license: Apache-2.0
  version: 1.3.1
  requires:
    bins:
      - agents-cli
    install: "uv tool install google-agents-cli"
disable-model-invocation: true
license: Apache 2.0
---

# Observability

Use this sub-skill inside the `google-agents-cli` repo skill. It is a router plus operating checklist; move into the bundled references for full command flags, schemas, and examples.

## When to Use

- The user wants traces, logs, prompt-response logging, analytics, or telemetry.
- The task mentions Cloud Trace, Cloud Logging, BigQuery Agent Analytics, AgentOps, Arize, Comet, or Weave.
- You need observability provisioning or verification commands after deployment.

## Workflow

1. Decide whether the user needs traces only or full prompt-response/BigQuery analytics.
2. Provision required infrastructure with the deploy/infra guidance when needed.
3. Set environment variables and deployment config for logging/telemetry sinks.
4. Verify traces/log rows/analytics records after a real request.

## Read These References

- `references/observability-guide.md` — read for observability guide details.
- `references/bigquery-agent-analytics.md` — read for bigquery agent analytics details.
- `references/cloud-trace-and-logging.md` — read for cloud trace and logging details.

## Verification and Safety

Safe checks: inspect config/env and docs; provisioning and telemetry verification need cloud credentials and a deployed/requested agent.

## Boundaries

- Does not deploy or publish by itself.
- Does not enable third-party telemetry without user approval for keys/data flow.

## Related Sub-Skills

- `../workflow/SKILL.md` — lifecycle routing and approval gates.
- `../scaffold/SKILL.md` — project creation/enhancement.
- `../adk-code/SKILL.md` — ADK Python implementation patterns.
- `../eval/SKILL.md` — evaluation loops and metrics.
- `../deploy/SKILL.md` — deployment and infrastructure.
- `../publish/SKILL.md` — Gemini Enterprise registration.
- `../observability/SKILL.md` — logging, tracing, and analytics.
