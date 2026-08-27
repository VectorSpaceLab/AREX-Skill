---
name: "testing-rig"
description: "Use testing-rig for Unstract's manifest-driven unit, integration,
  and e2e test selection, runtime orchestration, and critical-path reporting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Testing Rig

Use this sub-skill when the task is about repo-wide test selection, runtime orchestration, coverage aggregation, or critical-path reporting.

## Owns

- `tests/rig/` CLI, runtime selection, report aggregation, and coverage handling.
- `tests/groups.yaml` and `tests/critical_paths.yaml` as the source of truth for test coverage.
- The `tests/e2e/` and `tests/integration/` cross-service suites and their runtime modes.
- The repo-wide decision of which groups run in unit, integration, or e2e tiers.

## Excludes

- Backend API behavior itself — use `backend-platform`.
- Worker routing and operations — use `workers`.
- Full-stack startup — use `platform-deployment`.
- Shared SDK / tool authoring — use `sdk-and-tools`.
- Frontend route or runtime-config work — use `frontend`.

## Start Here

Read `references/manifest-and-runtime.md` when you need to understand the group manifest, runtime modes, coverage sources, and the rig CLI.

Read `references/troubleshooting.md` when the test run is missing a service, the runtime is wrong, or the rig reports an uncovered critical path.

For a safe inspection pass:

```bash
cd tests
python -m tests.rig validate
python -m tests.rig list-groups
```

## Shared References

- `references/manifest-and-runtime.md` — group manifests, runtime modes, reports, and critical-path coverage.
- `references/troubleshooting.md` — rig runtime, service, and coverage failures.
- `../../references/service-map.md` — repo-wide service map and dependencies.
- `../../references/installation-and-env.md` — install and environment matrix for rig-related runs.
- `../../references/repo-provenance.md` — source snapshot used to build this skill.

## Common Task Routing

| User request | Read next |
| --- | --- |
| "Which tests cover this path?" | `references/manifest-and-runtime.md` |
| "How do I list or expand the groups?" | `references/manifest-and-runtime.md` |
| "Why is an e2e / integration run failing?" | `references/troubleshooting.md` |
| "How does critical-path coverage work?" | `references/manifest-and-runtime.md` |
| "How do I run the platform-aware test lane?" | `references/manifest-and-runtime.md` |

## Safety Boundaries

- Do not run the full e2e suite as a smoke test unless the user explicitly wants test execution.
- Do not treat a missing critical-path group as a code defect until you have checked the manifest and the runtime lane that can actually cover it.
- Do not assume `testcontainers` starts the whole platform; today it only provisions the infra layer.
