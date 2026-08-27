---
name: agent-harness
description: "Guides DataChain bundled agent skills, knowledge-base generation,
  target install layouts, and data-harness workflows for coding agents."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Agent Harness

Use this sub-skill when the user asks how DataChain works with coding agents,
how to install/uninstall/list DataChain's bundled agent skills, where target
agent skill files are written, how to build or refresh `dc-knowledge/`, or how
to use DataChain as a persistent data harness over datasets and buckets.

## Trigger Phrases

Load this sub-skill for prompts about:

- installing DataChain skills for Claude, Cursor, Codex, Pi, or GitHub Copilot;
- project-local versus global DataChain skill installation;
- target skill layout, command/rule files, placeholder resolution, or safe uninstall;
- `dc-knowledge/`, knowledge-base snapshots, collection, enrichment, index rebuilds,
  stale knowledge pages, or `dc-knowledge/jobs/index.md`;
- agent workflows over object-storage buckets, saved datasets, cross-agent handoff,
  compounding work across sessions, and CAST layer planning.

## First Decision

1. **Skill install/layout question** → read
   [target-layouts](references/target-layouts.md). If the user needs a safe
   dry-run view of directories, use [skill_layout_check.py](scripts/skill_layout_check.py).
2. **Knowledge-base or bundled-skill behavior** → read
   [agent-skill-and-knowledge-base](references/agent-skill-and-knowledge-base.md).
3. **Data harness workflow over buckets/datasets** → read
   [workflows](references/workflows.md), then use the appropriate DataChain
   operating sub-skill for detailed code or query mechanics.
4. **Failure diagnosis** → read [troubleshooting](references/troubleshooting.md)
   and use [knowledge_base_smoke.py](scripts/knowledge_base_smoke.py) for a
   read-only `dc-knowledge/` tree check.

## Boundaries and Reroutes

- This sub-skill owns agent-skill packaging, `datachain skill install|uninstall|list`,
  `dc-knowledge/` structure/update guidance, CAST-at-a-glance routing, and
  agent data-harness workflows.
- For a broad DataChain CLI command catalog, reroute to sibling sub-skill
  `cli-and-studio`.
- For DataChain SDK pipeline code patterns, UDF signatures, `.save()`,
  `read_storage`, or script authoring details, reroute to sibling sub-skill
  `sdk-pipelines`.
- For query expression/function details, reroute to sibling sub-skill
  `query-engine`.
- For repository maintainer policy, test matrix, release, or contribution
  questions, reroute to sibling sub-skill `repo-development`.

## Safety Rules

- Do not direct the user or a future agent to open DataChain's bundled source
  skill files. The operational guidance needed for this area is distilled in
  this subtree.
- Do not mutate target agent directories while only answering a layout question;
  use the dry-run helper first.
- Do not edit `dc-knowledge/` by hand as a substitute for regenerating it from
  the Dataset DB. Markdown can be read for context; regeneration should come
  from the DataChain knowledge workflow.
- Treat `.json` files under `dc-knowledge/` as temporary intermediates, not as
  the durable knowledge surface.
