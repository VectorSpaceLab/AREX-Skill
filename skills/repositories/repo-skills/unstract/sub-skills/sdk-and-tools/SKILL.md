---
name: "sdk-and-tools"
description: "Use sdk-and-tools for Unstract's shared Python packages, tool
  protocol, tool registry, connectors, and tool authoring workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# SDK And Tools

Use this sub-skill when the task is about the reusable Python packages under `unstract/`, the containerized example tools under `tools/`, or the tool-registry / tool-sandbox workflow that connects them.

## Owns

- Shared packages: `unstract/sdk1`, `unstract/core`, `unstract/filesystem`, `unstract/flags`, `unstract/tool-registry`, `unstract/tool-sandbox`, `unstract/workflow-execution`, and `unstract/connectors`.
- Tool authoring under `tools/classifier` and `tools/text_extractor`.
- Tool protocol, tool metadata files, runtime-variable schema, and registry-backed tool loading.
- Shared tool / SDK inspection that does not belong to a specific service or route family.

## Excludes

- Backend API routing and hosted MCP details — use `backend-platform`.
- Full-stack deployment / bootstrap — use `platform-deployment`.
- Worker queue and Celery / PG orchestration — use `workers`.
- Frontend routing or runtime config — use `frontend`.
- Repo test-group manifests and critical-path reporting — use `testing-rig`.

## Start Here

Read `references/package-and-tooling.md` first when the task involves:

- shared package versions or import surfaces,
- the tool protocol or tool metadata schema,
- `tool-registry` / `tool-sandbox` configuration,
- or the classifier / text-extractor example tools.

Read `references/troubleshooting.md` when the issue is a missing optional dependency, registry config failure, tool metadata mismatch, or tool-container runtime problem.

For a safe package-level smoke check, use the root checker from this skill tree:

```bash
python ../../scripts/check_unstract_packages.py
python ../../scripts/check_unstract_packages.py --tool-registry --tool-registry-config <config-dir>
```

## Shared References

- `references/package-and-tooling.md` — shared package map, tool protocol, registry, and example tool guidance.
- `references/troubleshooting.md` — install, optional dependency, registry, and container-tool failures.
- `../../references/package-layout.md` — repo-wide package and service ownership map.
- `../../references/installation-and-env.md` — install and environment matrix for SDK / tool workflows.
- `../../references/repo-provenance.md` — source snapshot used to build this skill.
- `../../scripts/check_unstract_packages.py` — shared package and backend smoke checker.

## Common Task Routing

| User request | Read next |
| --- | --- |
| "How do these shared packages fit together?" | `references/package-and-tooling.md` |
| "How do I use the tool protocol?" | `references/package-and-tooling.md` |
| "How do I validate a tool registry config?" | `references/package-and-tooling.md` |
| "Why is a tool container / SDK import failing?" | `references/troubleshooting.md` |
| "What env vars do the example tools need?" | `references/package-and-tooling.md` |

## Safety Boundaries

- Do not assume optional cloud / database / tool-container dependencies are installed.
- Do not treat registry loading as a smoke test if it would pull images or write JSON to disk.
- Do not leak private registry credentials or tool-provider secrets into generated content.
