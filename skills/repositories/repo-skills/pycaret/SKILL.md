---
name: pycaret
description: "Routes PyCaret monorepo tasks across engine workflows, backend API
  work, web UI edits, deployment operations, and maintainer workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyCaret Repo Skill

Use this skill when working in the PyCaret monorepo or with the PyCaret 4 Control Plane stack. It is a router, not a full manual: read the sub-skill that matches the user-facing workflow, then follow its bundled references and scripts.

## Quick start

Install the surface you need in an isolated environment:

- Engine workflows: `python -m pip install -e packages/engine[anomaly,timeseries,test]`
- Control Plane backend: `python -m pip install -e services/api[test]`
- Web UI: `cd apps/web && npm install`
- Full stack editing: install both Python packages, then use the web install when you touch `apps/web`

For a quick cross-cutting check, run:

```bash
python scripts/check_pycaret_stack.py --json
```

That helper confirms the engine package, the `pycaret-server` package, the engine model registries, and the FastAPI app factory without requiring a browser or a live deployment.

Read these shared references when you need a higher-level map:

- [Package overview](references/package-overview.md) for the monorepo surface map and install matrix.
- [Troubleshooting](references/troubleshooting.md) for cross-cutting install/import/tooling failures.
- [Repository provenance](references/repo-provenance.md) when checking whether this skill matches the current checkout or before refreshing it.
- [Routing metadata](references/repo-routing-metadata.json) for managed DisCo import only.

## Route by task

### Engine workflows

Read [sub-skills/engine-workflows/SKILL.md](sub-skills/engine-workflows/SKILL.md) for:

- OOP task classes such as `ClassificationExperiment`, `RegressionExperiment`, `ClusteringExperiment`, `AnomalyExperiment`, and `TimeSeriesExperiment`.
- `fit`, `create_model`, `compare_models`, `tune_model`, `predict_model`, `assign_model`, `plot_model`, `evaluate_model`, `interpret_model`, and persistence.
- Typed result dataclasses, event logging, `pycaret.api` introspection, and safe smoke checks.

### Control Plane API

Read [sub-skills/control-plane-api/SKILL.md](sub-skills/control-plane-api/SKILL.md) for:

- `pycaret-server`, FastAPI routes, auth/bootstrap, run and trial lifecycles, deployments, storage, and LLM advisories.
- CLI usage, `PYCARET_*` settings, TestClient workflows, and backend smoke checks.

### Web UI

Read [sub-skills/web-ui/SKILL.md](sub-skills/web-ui/SKILL.md) for:

- React/Vite route wiring, typed API client changes, auth state, dynamic experiment forms, run/trial/deployment screens, and npm verification.

### Platform operations

Read [sub-skills/platform-operations/SKILL.md](sub-skills/platform-operations/SKILL.md) for:

- Docker Compose, secrets, queues, workers, backups, storage, and GPU routing.

### Repo development

Read [sub-skills/repo-development/SKILL.md](sub-skills/repo-development/SKILL.md) for:

- Contributor policy, release notes, tests, docs, kill-list guardrails, and maintainer automation.

## Working rules

- Route by user workflow, not only by repository directory name.
- If a task mixes surfaces, start with the most user-facing workflow and then cross-link to the owning sub-skill for the rest.
- Keep the root skill short; signatures, long examples, model lists, route tables, and troubleshooting matrices belong in the sub-skill references.
- Do not treat the root skill as a write-up of the repository docs. It only orients future agents and points them to the right sub-skill.

## Boundaries

- This skill does not replace sub-skill-specific guidance on model APIs, route schemas, UI forms, deployment ops, or maintainer policy.
- It does not tell future agents to depend on the current checkout for runtime behavior. Any reusable logic lives in the bundled references or scripts inside this skill tree.
