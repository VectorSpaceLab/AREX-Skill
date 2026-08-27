---
name: kubeflow-pipelines
description: "Route Kubeflow Pipelines SDK, client, Kubernetes-addon, and
  repository-maintenance workflows to the right sub-skill."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kubeflow Pipelines

Use this repo skill for Kubeflow Pipelines (KFP) tasks that involve the Python SDK, client/registry flows, Kubernetes task configuration, or this checkout's maintainer workflow. The runtime skill is split into sub-skills so future agents can route quickly without reading the whole repository.

## Start here

If the request is about using KFP as a library, the bundled public-use sub-skills own the task:

- `sub-skills/pipeline-authoring/` for DSL components, pipelines, artifacts, task modifiers, control flow, and local execution smoke checks.
- `sub-skills/compiler-and-cli/` for `Compiler().compile`, `kfp dsl compile`, `dsl-compile`, and compile-output questions.
- `sub-skills/client-and-registry/` for `kfp.Client`, client-backed CLI groups, uploads, runs, recurring runs, experiments, and registry package flows.
- `sub-skills/kubernetes-platform/` for `kfp.kubernetes` helper APIs that add Kubernetes-specific task configuration.

If the request is about changing this checkout, generated files, tests, CI, manifests, frontend/backend code, or developer setup, route to `sub-skills/repo-development/`.

## Package map

Read `references/package-overview.md` before answering install, import, version, or package-layout questions. It summarizes the `kfp` namespace package, the `kfp-pipeline-spec` and `kfp-kubernetes` add-ons, the main console scripts, and the current repo layout at a high level.

Read `references/repo-provenance.md` when you need to compare the generated skill against the source checkout state, and `references/repo-routing-metadata.json` when you need the router metadata that places this skill inside the repo-skills router.

## Environment check

Use `scripts/check_kfp_environment.py` as a safe first smoke test when you need to confirm that the installed KFP environment is usable. It checks the public import surface and can optionally probe CLI/help behavior without relying on the original checkout.

## Troubleshooting

Read `references/troubleshooting.md` when the user reports import failures, endpoint confusion, local-runner issues, compile/manifest confusion, version skew, or checkout-maintenance prerequisites.

## Routing hints

- If the user wants to write a pipeline/component, start with `pipeline-authoring`.
- If the user already has a Python file or object and wants YAML or manifest output, use `compiler-and-cli`.
- If the user wants to submit or manage runs, experiments, or registry packages, use `client-and-registry`.
- If the user wants Kubernetes-specific task settings, use `kubernetes-platform`.
- If the user is editing source files or regen outputs in this repo, use `repo-development`.

## Notes for future agents

- The public-use sub-skills are self-contained and should not depend on this construction checkout.
- Do not treat `skills/tests/` as runtime content; it is the review and verification area.
- Use the smallest sub-skill that actually matches the task, then read only the bundled references and scripts that that sub-skill points to.
