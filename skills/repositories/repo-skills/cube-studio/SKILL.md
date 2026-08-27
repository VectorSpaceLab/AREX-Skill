---
name: cube-studio
description: "Route CubeStudio MLOps platform deployment, customization, and
  operation tasks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# CubeStudio

Use this repo skill for CubeStudio platform tasks: deployment, backend customization, notebooks and image catalogs, pipeline/job-template authoring, data and SQLLab workflows, and model serving / AIHub / chat operations.

## Start here

1. Read [references/platform-overview.md](references/platform-overview.md) for the repo-wide architecture and route map.
2. Read [references/configuration-and-catalogs.md](references/configuration-and-catalogs.md) for overlay behavior, runtime configuration, and seed catalogs.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/config/runtime failures.
4. If the checkout looks stale, compare it with [references/repo-provenance.md](references/repo-provenance.md).
5. If you want a safe static inventory of a CubeStudio checkout, run the bundled helper:

   ```bash
   python scripts/cube_studio_static_check.py --help
   python scripts/cube_studio_static_check.py /path/to/cube-studio
   ```

## Setup note

CubeStudio is a platform checkout, not a normal pip-installable package. For a public inspection environment, use Python 3.9 and install the documented runtime dependencies before running the bundled static helpers:

```bash
python -m pip install -r install/docker/requirements.txt
python scripts/cube_studio_static_check.py .
```

Use the deployment and backend sub-skills for Docker Compose, Kubernetes, and runtime overlay setup rather than trying to install the repository as a library.

## Route map

- `deploy-and-operate` — local Docker Compose development, Kubernetes install order, offline/private registry prep, manifest inventory, overlays, and deployment triage.
- `backend-and-configuration` — Flask AppBuilder startup, runtime overlays, auth/RBAC, backend views/APIs, Celery/watchers, and frontend build/proxy customization.
- `compute-notebooks-and-images` — project/resource groups, notebook lifecycle, GPU resource strings, registry/image catalog, and monitoring/resource views.
- `pipelines-and-job-templates` — pipeline DAGs, job-template registration, Argo workflow generation, template args schema, and NNI/HPO templates.
- `data-metadata-and-sqllab` — datasets, metadata and dimension tables, SQLLab, ETL pipelines, and data-transfer templates.
- `serving-aihub-and-llm` — model registry, inference services, AIHub cards, chat scenarios, and LLM gateway configuration.

## When to use this repo skill

- The user names CubeStudio, Kubeflow Dashboard, AIHub, notebook, pipeline, job template, inference service, SQLLab, or the platform's Kubernetes/Docker install stack.
- The user needs the platform's own runtime guidance, not a generic Flask, Kubernetes, or image-serving answer.
- The user wants to understand how a record in one CubeStudio area becomes another record or runtime object, such as training model → inference service or job template → pipeline task.

## What not to do here

- Do not treat this as a generic repository-maintenance skill unless the request is explicitly about editing the CubeStudio source tree.
- Do not point future agents to the original checkout for runtime steps when the answer can be bundled into a reference or helper.
- Do not run cluster-mutating, Docker-building, or service-starting commands as part of skill drafting.

## Safe first checks

- Inspect the selected sub-skill first when the request is clearly domain-specific.
- Use the repo-level static helper for a fast, read-only inventory of a checkout.
- Use the sub-skill references for detailed APIs, workflows, and troubleshooting.

## Shared guidance

- The checked-in `myapp/config.py` and `myapp/project.py` are placeholders; runtime overlays provide the real configuration.
- Pipeline, serving, and notebook tasks often depend on the same project, resource, and image registry assumptions, so cross-link to the sibling sub-skill when the question spans domains.
- If a task mixes installation, backend customization, and runtime deployment, start with the deployment or backend sub-skill and then follow the route map above.
