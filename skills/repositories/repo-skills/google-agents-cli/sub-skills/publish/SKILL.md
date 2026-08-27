---
name: publish
description: "Use this sub-skill when registering a deployed ADK/A2A agent with
  Gemini Enterprise or managing Agent Registry records for agents-cli
  deployments."
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

# Gemini Enterprise Publishing

Use this sub-skill inside the `google-agents-cli` repo skill. It is a router plus operating checklist; move into the bundled references for full command flags, schemas, and examples.

## When to Use

- The user wants a deployed agent registered with Gemini Enterprise.
- The task mentions ADK registration, A2A agent card URLs, Gemini Enterprise app IDs, Agent Registry, or `publish gemini-enterprise`.
- You need to choose registration type from deployment metadata.

## Workflow

1. Confirm the Gemini Enterprise app ID and deployed endpoint or Agent Runtime metadata.
2. Use ADK registration for Agent Runtime unless A2A is explicitly required.
3. Use A2A agent card URLs for Cloud Run/GKE registration.
4. Treat re-publish as an update and verify IAM/SDK compatibility when debugging.

## Read These References

- `references/publish-guide.md` — read for publish guide details.

## Verification and Safety

Safe checks: `agents-cli publish gemini-enterprise --help`; live registration needs a deployed agent, app ID, and IAM approval.

## Boundaries

- Does not deploy the agent.
- Does not create Gemini Enterprise apps or change IAM unless explicitly requested and authorized.

## Related Sub-Skills

- `../workflow/SKILL.md` — lifecycle routing and approval gates.
- `../scaffold/SKILL.md` — project creation/enhancement.
- `../adk-code/SKILL.md` — ADK Python implementation patterns.
- `../eval/SKILL.md` — evaluation loops and metrics.
- `../deploy/SKILL.md` — deployment and infrastructure.
- `../publish/SKILL.md` — Gemini Enterprise registration.
- `../observability/SKILL.md` — logging, tracing, and analytics.
