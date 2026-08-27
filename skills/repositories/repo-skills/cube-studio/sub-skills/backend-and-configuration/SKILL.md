---
name: backend-and-configuration
description: "Operate CubeStudio backend lifecycle, configuration overlays,
  RBAC, services, and frontend build customization."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# CubeStudio backend and configuration

Use this sub-skill for CubeStudio backend maintenance tasks that involve Flask
AppBuilder startup, config/project overlays, authentication and RBAC, backend
view/API registration, Celery and watcher services, or frontend build/proxy
customization.

## Read first

1. `references/config-reference.md` for the mandatory runtime overlay model:
   the checked-in `myapp/config.py` and `myapp/project.py` placeholders are
   empty, while Docker and Kubernetes mount real overlay files at runtime.
2. `references/backend-lifecycle.md` for app startup, DB migration/init order,
   AppBuilder permissions, auth hooks, and Celery/watch service behavior.
3. `references/frontend-build.md` for the three frontend packages, safe proxy
   edits, and build commands that require explicit permission.
4. `references/troubleshooting.md` when imports, login, permissions, DB/Redis,
   Celery, watchers, or frontend proxy/builds fail.

For a safe static inspection of a provided CubeStudio-like checkout, run:

```bash
python scripts/inspect_cube_studio_structure.py /path/to/cube-studio --json
```

The helper reads files only. It does not import `myapp`, connect to DB/Redis,
start services, run Docker, run Kubernetes commands, install npm packages, or
build frontend bundles.

## Use this sub-skill when the task asks to

- boot, inspect, or change the Flask AppBuilder backend lifecycle;
- decide where to edit `config.py`, `project.py`, or runtime environment
  variables for Docker/Kubernetes/local inspection;
- add or debug backend model-view/API registrations and FAB permissions;
- customize login/auth, user roles, header/JWT behavior, or project messaging
  hooks;
- reason about Celery worker/beat tasks or `watch_workflow`/`watch_service`;
- change `setupProxy.js`, frontend package scripts, or SPA build/deploy
  behavior.

## Route elsewhere

- Raw Docker Compose or Kubernetes deployment, image registry rewrites, CRD
  ordering, namespace/secret/PVC setup: use `deploy-and-operate`.
- Notebook/resource group/GPU selectors, image catalog and online image builds:
  use `compute-notebooks-and-images`.
- Pipeline DAGs, task templates, Argo workflow generation, run history: use
  `pipelines-and-job-templates`.
- Dataset, metadata, dimension, SQLLab, ETL details: use
  `data-metadata-and-sqllab`.
- Model registry, inference services, AIHub, chat, LLM gateway behavior: use
  `serving-aihub-and-llm`.

Keep domain-specific model/view fields in those sibling sub-skills; use this
sub-skill only for the shared backend plumbing that makes those domains
available.
