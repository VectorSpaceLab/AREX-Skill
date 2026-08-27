---
name: repo-development
description: "Maintain, test, regenerate, and troubleshoot a Kubeflow Pipelines
  source checkout without confusing checkout work with public KFP package
  usage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kubeflow Pipelines Repo Development

Use this sub-skill only when the user is working on the Kubeflow Pipelines **source repository**: editing code, tests, generated files, CI, manifests, frontend assets, backend services, or checkout-local developer setup.

For public package use, route away instead of answering here:

- Writing KFP components, pipelines, artifacts, control flow, local execution, task modifiers -> `pipeline-authoring`.
- Compiling pipeline files, `Compiler().compile`, `kfp dsl compile`, `dsl-compile`, PipelineSpec output -> `compiler-and-cli`.
- `kfp.Client`, uploads, runs, recurring runs, experiments, registry, service auth -> `client-and-registry`.
- `from kfp import kubernetes`, secrets, PVCs, tolerations, node selectors, pod labels, Kubernetes task configuration -> `kubernetes-platform`.
- Other AI workflow libraries or different repositories -> use that repository's skill or ordinary repo inspection.

## Operating Rules

1. Confirm the task is checkout maintenance. If the user is trying to use an installed `kfp` package, route to the public-use sub-skill above.
2. Treat the bundled references as the operating baseline, then verify against the current checkout before running commands because Make targets, workflow matrices, and package versions may have changed.
3. Obey any current checkout agent instructions and keep changes minimal. Preserve DCO/PR conventions and project style.
4. Never hand-edit generated outputs. Change the source artifact and run the documented regeneration command from [references/generated-code.md](references/generated-code.md).
5. Choose the narrowest safe command family from [references/development-testing.md](references/development-testing.md). Do not run cluster, Docker, GCP, release, cleanup, or credential-bound commands unless the user explicitly asked for that scope and prerequisites are available.
6. When a repo edit changes public SDK behavior, update or test the corresponding public-use path too: authoring examples, compile behavior, client flows, or `kfp-kubernetes` task config.
7. Record skipped checks honestly. Go, Node, Docker, Kind, kubectl, Ginkgo, and GPU/Kubernetes lanes are prerequisite-bound; a CPU import or compile check does not verify those lanes.

## Reference Map

- [references/architecture-and-layout.md](references/architecture-and-layout.md): monorepo areas, package/version relationships, backend/frontend/runtime roles, and contribution conventions.
- [references/development-testing.md](references/development-testing.md): local setup, tool prerequisites, targeted test/format/build command families, frontend smoke testing, and dependency updates.
- [references/generated-code.md](references/generated-code.md): generated-file ownership, regeneration commands, CI drift checks, and frontend/backend API-client drift handling.
- [references/troubleshooting.md](references/troubleshooting.md): symptom-oriented fixes for generated drift, missing tools, cluster/e2e failures, frontend lockfile/API drift, GPU labels, `_KFP_RUNTIME=true`, dependency locks, and formatting failures.

## Safe Handoff Pattern

When answering a repo-maintenance task, include:

- changed area and owning paths;
- commands run and commands intentionally skipped with prerequisites;
- generated-code commands needed or not needed;
- public-package routes that may need examples/tests updated;
- CI lanes most likely to cover the change;
- any maintainer-only, credential-bound, destructive, or cluster/GPU-dependent gaps.

This sub-skill is self-contained. It names relative paths that should exist in a Kubeflow Pipelines checkout, but it does not require the original construction checkout or any absolute source path.
