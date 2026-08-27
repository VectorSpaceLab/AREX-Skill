# Giskard OSS Package Overview

## Purpose

Read this to choose the correct Giskard v3 package, import namespace, optional
extra, and sub-skill before writing code. It is a distilled, self-contained
package map; it does not require the source repository checkout.

## Version and Python baseline

- Root distribution: `giskard` `3.0.0b1`.
- Split packages: `giskard-core` `1.0.1b6`, `giskard-llm` `1.0.0b6`,
  `giskard-agents` `1.0.2b6`, `giskard-checks` `1.0.2b6`,
  `giskard-scan` `1.0.0b4`.
- Python requirement: `>=3.12`.
- Import namespace: use `giskard.<sublib>` such as `giskard.checks` or
  `giskard.scan`. Do not import `giskard_checks`, `giskard_scan`, or other
  underscore names.

## Package map

| Distribution / extra | Import surface | Use when | Notes |
| --- | --- | --- | --- |
| `giskard` | split namespace packages, primarily `giskard.checks` | Basic eval scenarios/checks and root install path | Root meta-distribution depends on checks. The usable APIs live in split packages. |
| `giskard-core` | `giskard.core` | Telemetry, rate limiting, discriminated unions, serializable errors, version helpers | Usually installed as a dependency. |
| `giskard-llm` | `giskard.llm` | Provider/model routing, async completions, embeddings, response API, errors | Provider SDKs are optional extras. |
| `giskard-agents` | `giskard.agents` | Async chat workflows, generators, tools, prompt templates, structured outputs | Uses `giskard.llm` for native provider routing. LiteLLM is optional. |
| `giskard-checks` | `giskard.checks` | `Scenario`, `Suite`, deterministic checks, LLM judges, input generators, JUnit export | LLM judges require a configured generator/provider. |
| `giskard-scan` or `giskard[scan]` | `giskard.scan` | Vulnerability scan, RAG quality scan, `KnowledgeBase`, scan generators | Most real scans need a working default generator/provider. |

## Common install selections

```bash
pip install giskard
pip install "giskard[scan]"
pip install "giskard[openai]"
pip install "giskard[scan,openai]"
```

Use provider extras only for providers you will call:

| Extra | Adds / enables |
| --- | --- |
| `openai` | OpenAI, Azure OpenAI, and Azure AI Foundry through the OpenAI SDK. |
| `google` | Google Gemini completion and embedding provider. |
| `anthropic` | Anthropic completion provider. |
| `azure` | Azure OpenAI support through the OpenAI SDK; overlaps with `openai`. |
| `litellm` | Optional `giskard-agents` LiteLLM generator backend. |
| `regorus` | Optional Rego policy check support in `giskard-checks`. |
| `scan` | Installs `giskard-scan`. |
| `garak`, `deepteam` | Optional third-party scanner integrations for `giskard-scan`. |
| `full` | Broad aggregate; avoid by default unless the task truly needs many extras. |

## Route by task

| Task | Sub-skill |
| --- | --- |
| Install/import, telemetry opt-out, version checks, core utilities | `sub-skills/runtime-setup/SKILL.md` |
| Build eval scenarios, checks, suites, judges, generators, JUnit export | `sub-skills/checks-evals/SKILL.md` |
| Configure provider aliases or call direct completions/embeddings/responses | `sub-skills/llm-providers/SKILL.md` |
| Build async agent workflows with tools/templates/structured output | `sub-skills/agents-workflows/SKILL.md` |
| Plan or run vulnerability/quality scans and use scan generators | `sub-skills/scan-redteam/SKILL.md` |

## Safe installed-package smoke

Run the bundled root helper to check importability and optional dependency
availability without network calls:

```bash
python scripts/check_giskard_imports.py
python scripts/check_giskard_imports.py --require-scan
```

The helper sets telemetry opt-out before import and does not call providers or
third-party scanners.
