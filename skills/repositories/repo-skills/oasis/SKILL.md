---
name: oasis
description: "Use OASIS (camel-oasis) for LLM social-media simulations, agent
  profiles, platform actions, recommendation settings, SQLite traces, and legacy
  experiment analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OASIS Repo Skill

Use this skill for tasks involving OASIS / `camel-oasis`: agent-based Twitter-like or Reddit-like simulations, profile file preparation, `AgentGraph` and `SocialAgent` setup, `ManualAction`/`LLMAction` step orchestration, custom `Platform` and recommendation settings, OASIS SQLite trace databases, and legacy experiment analysis.

## Start here

1. Confirm the package import and version with [scripts/check_oasis_install.py](scripts/check_oasis_install.py).
2. Read [references/api-overview.md](references/api-overview.md) for the public API surface and object relationships.
3. Route the task to the closest sub-skill below.
4. Use [references/troubleshooting.md](references/troubleshooting.md) for install/import, credentials, optional backends, and DB lifecycle blockers.
5. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a different checkout or package version.

## Install and import check

Normal package install:

```bash
pip install camel-oasis
```

Local checkout install:

```bash
pip install -e .
```

Minimal import check:

```python
import oasis
print(oasis.__version__)
from oasis import AgentGraph, SocialAgent, UserInfo, ActionType, ManualAction
```

If import fails with `FastMCP` / `mcp.server`, use a compatible MCP version such as `pip install 'mcp<2'` or update CAMEL to a compatible release.

## Sub-skill routes

| Task | Read |
| --- | --- |
| Create or validate Reddit JSON/Twitter CSV profiles; build `AgentGraph`; customize `SocialAgent`, `UserInfo`, prompts, toolkits, or Neo4j graph backend. | [sub-skills/agent-profiles/SKILL.md](sub-skills/agent-profiles/SKILL.md) |
| Run or adapt Reddit/Twitter/custom simulations; manage `env.reset()` / `env.step()` / `env.close()`; use `ManualAction` and `LLMAction`; configure model backends and budgets. | [sub-skills/simulation-workflows/SKILL.md](sub-skills/simulation-workflows/SKILL.md) |
| Choose `ActionType` and `ManualAction.action_args`; configure `Platform`, `RecsysType`, `Clock`, or `Channel`; inspect SQLite tables, traces, groups, reports, products, and recommendations. | [sub-skills/platform-actions/SKILL.md](sub-skills/platform-actions/SKILL.md) |
| Triage legacy OASIS experiment YAMLs, generated-user flows, large-scale VLLM/OpenAI runs, score/counterfactual analysis, and visualization outputs. | [sub-skills/experiments-analysis/SKILL.md](sub-skills/experiments-analysis/SKILL.md) |

## Safe default workflow

For a new task, prefer a tiny no-LLM path before provider-backed simulation:

1. Validate or create profiles with `agent-profiles`.
2. Run [sub-skills/simulation-workflows/scripts/oasis_manual_smoke.py](sub-skills/simulation-workflows/scripts/oasis_manual_smoke.py) to prove local imports, SQLite, signup, post/comment/follow, and close behavior.
3. Inspect the generated database with [sub-skills/platform-actions/scripts/oasis_db_summary.py](sub-skills/platform-actions/scripts/oasis_db_summary.py).
4. Only then add real `LLMAction`, TwHIN/personalized recommendation, VLLM, OpenAI embeddings, Neo4j, or large experiment settings with explicit credentials and budget.

## Important package facts

- Distribution name is `camel-oasis`; import name is `oasis`.
- The verified version for this skill is `0.2.5` on Python `>=3.10,<3.12`.
- `ManualAction` uses `action_type` and `action_args`. Some docs or snippets may show older `action` / `args` names; use the source-backed dataclass fields.
- `actions` passed to `env.step()` are keyed by `SocialAgent` objects, not integer agent IDs.
- Constructing `SocialAgent(model=None)` can require a non-empty `OPENAI_API_KEY` because CAMEL builds a default model backend. No real provider call occurs until an LLM-backed action is performed.
- The default Twitter platform uses `twhin-bert` recommendations, which may require optional model downloads or torch/CUDA resources. Use Reddit or random recommendation settings for tiny CPU-only checks.

## Do not use this skill when

- The task is generic CAMEL agent framework development without OASIS social-platform objects.
- The task is only VLLM/Neo4j/OpenAI infrastructure setup and does not involve OASIS simulations.
- The user asks to perform downstream research interpretation without needing package operation guidance; then use the appropriate Researcher mode and loaded operating graph.

## Router metadata

Structured router metadata lives in [references/repo-routing-metadata.json](references/repo-routing-metadata.json). Do not hand-edit live routers; use the repo-skill verification/import protocol when importing is explicitly requested.
