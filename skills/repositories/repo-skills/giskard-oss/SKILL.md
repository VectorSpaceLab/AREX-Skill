---
name: giskard-oss
description: "Routes Giskard OSS v3 package tasks across checks, LLM providers,
  agents, scans, runtime setup, troubleshooting, and maintainer validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Giskard OSS

Use this repo skill for Giskard OSS v3, a split Python package set for
evaluating and red-teaming agentic systems. It covers `giskard.checks`,
`giskard.llm`, `giskard.agents`, `giskard.scan`, and `giskard.core`.

## Start Here

- [Package overview](references/package-overview.md) explains package names,
  install extras, import namespaces, and version boundaries.
- [Cross-cutting troubleshooting](references/troubleshooting.md) covers install,
  import, telemetry, optional extras, provider credentials, and scan triage.
- [Development and testing notes](references/development-and-testing.md) are only
  for tasks already working inside a Giskard OSS source checkout.
- [Repository provenance](references/repo-provenance.md) records the source
  snapshot used to generate this skill and when to refresh it.
- [Repo routing metadata](references/repo-routing-metadata.json) is structured
  import metadata for repo-skills-router publication checks.
- [scripts/check_giskard_imports.py](scripts/check_giskard_imports.py) checks an
  installed environment without provider calls or network access.

## Minimal Runtime Facts

- Requires Python `>=3.12`.
- Use namespace imports such as `import giskard.checks`; do not use
  `giskard_checks` or other underscore package names.
- The root `giskard` distribution is a v3 meta-distribution; the operational
  APIs live under split packages.
- Set `DO_NOT_TRACK=1` or `GISKARD_TELEMETRY_DISABLED=1` before the first import
  when the user requests telemetry opt-out.
- No console entry points are declared by the package metadata; primary usage is
  through Python APIs.

## Route by Task

| User task | Read |
| --- | --- |
| Install Giskard, choose extras, inspect versions, disable telemetry, diagnose import conflicts, or use `giskard.core` utilities | [runtime-setup](sub-skills/runtime-setup/SKILL.md) |
| Build evaluation scenarios/suites, choose deterministic checks or LLM judges, generate inputs, write custom checks, or export JUnit | [checks-evals](sub-skills/checks-evals/SKILL.md) |
| Configure OpenAI/Google/Anthropic/Azure provider aliases, call completions/embeddings/responses, inspect typed messages/tools, or handle provider errors | [llm-providers](sub-skills/llm-providers/SKILL.md) |
| Build async chat workflows with `Generator`, `ChatWorkflow`, tools, prompt templates, structured output, retries, rate limiting, or LiteLLM | [agents-workflows](sub-skills/agents-workflows/SKILL.md) |
| Plan or run vulnerability scans, RAG quality scans, scan suite generation, `KnowledgeBase`, prompt-injection generators, or garak/deepteam/lidar integrations | [scan-redteam](sub-skills/scan-redteam/SKILL.md) |

## Safe Checks Before Deeper Work

Run installed-package diagnostics first when the environment is uncertain:

```bash
python scripts/check_giskard_imports.py
python scripts/check_giskard_imports.py --require-scan
```

Then use sub-skill scripts for focused no-key checks:

```bash
python sub-skills/checks-evals/scripts/run_checks_smoke.py
python sub-skills/llm-providers/scripts/inspect_llm_routing.py
python sub-skills/agents-workflows/scripts/run_agents_smoke.py
python sub-skills/scan-redteam/scripts/inspect_scan_api.py
```

These helpers are deterministic and do not call live providers, remote datasets,
third-party scanners, or source-checkout tests.

## Optional Dependencies and External Inputs

Install only the extras the task needs. Provider-backed LLM judges, generators,
agents, and scans require matching SDK extras plus credentials. Third-party scan
integrations may require `garak`, `deepteam`, private packages, network access,
or additional API keys. Do not treat a successful import smoke as proof that a
live provider or scanner workflow is ready.

## Refresh Rule

Before relying on this skill for a changed checkout, compare the current commit,
working-tree state, and package versions against
[repo-provenance.md](references/repo-provenance.md). If they differ materially,
run the repo-skill refresh workflow instead of patching runtime guidance ad hoc.
