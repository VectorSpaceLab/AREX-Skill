---
name: data-juicer
description: "Data-Juicer repo router for local recipes, Ray recovery, and
  service/MCP workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Data-Juicer Repo Skill

Use this skill as the top-level router for the Data-Juicer repository. Keep workflow depth, long examples, and troubleshooting details in the sub-skills and shared references.

## Start with the route

| User need | Read |
| --- | --- |
| Local recipe processing, dataset config, export, operator choice, or simple analysis | `sub-skills/recipes-and-ops/SKILL.md` |
| Ray execution, partitioning, checkpointing, job monitoring, or recovery | `sub-skills/ray-and-recovery/SKILL.md` |
| FastAPI service, MCP server, operator search, or request encoding | `sub-skills/service-mcp/SKILL.md` |

## Quick environment check

Install guidance lives in `references/install-and-scope.md`; start with `py-data-juicer` and add `tools` or `distributed` only when the selected route needs them.

Use the bundled smoke check when you only need a safe install/import sanity check:

```bash
python scripts/check_environment.py
```

Useful CLI help checks:

```bash
dj-process --help
dj-analyze --help
dj-install --help
dj-mcp --help
```

## Shared references

- `references/repo-provenance.md`
- `references/repo-routing-metadata.json`
- `references/install-and-scope.md`
- `references/package-overview.md`
- `references/cli-reference.md`
- `references/api-reference.md`
- `references/optional-extras.md`
- `references/troubleshooting.md`
- `references/workflow-map.md`

## Scope boundaries

- Do not mix local recipe guidance with Ray recovery details.
- Do not mix HTTP/MCP request transport with local dataset semantics.
- Do not assume optional extras are installed unless the workflow needs them.
- Do not depend on the source checkout remaining present once the skill is created.

## When in doubt

Start from `references/workflow-map.md`, then open the matching sub-skill.
