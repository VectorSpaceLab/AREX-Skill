# Package Overview

This repository ships multiple Python packages and a broader source checkout around the Kubeflow Pipelines ecosystem.

## Core public packages

| Package | What it provides | Typical install/use |
| --- | --- | --- |
| `kfp` | Main Kubeflow Pipelines Python SDK: DSL authoring, compiler API, client API, local execution helpers, and CLI entry points. | `pip install kfp` |
| `kfp-pipeline-spec` | Generated PipelineSpec protobuf and namespace package used by the compiler and SDK internals. | Installed as a dependency of `kfp`; sometimes edited/installed separately for checkout work. |
| `kfp-kubernetes` | Kubernetes-task helper addon for `kfp` pipelines. | `pip install kfp[kubernetes]` or `pip install kfp-kubernetes` |
| `kfp-server-api` | Generated backend client used by `kfp.Client` and related flows. | Installed transitively with `kfp`; regenerated from backend API outputs. |

## Package relationships

- `kfp` is a namespace package. Its top-level import surface exposes `dsl`, `components`, and `Client` when runtime-import filtering is not active.
- `kfp-pipeline-spec` and `kfp-kubernetes` also share the `kfp` namespace.
- `kfp.kubernetes` is an addon namespace, not part of the base `kfp` install unless the Kubernetes extra is present.
- `_KFP_RUNTIME=true` changes import behavior for runtime containers; it is not the same as a normal authoring or development environment.

## Console scripts and entry points

- `kfp`: top-level CLI for compile-related, client-backed, and diagnostic command groups.
- `dsl-compile`: deprecated compile CLI alias that still exists for compatibility in older workflows.

## High-level checkout layout

| Area | What lives there |
| --- | --- |
| `sdk/python/` | Main Python SDK source, tests, and package metadata. |
| `api/v2alpha1/python/` | PipelineSpec namespace package and generated protobuf support. |
| `kubernetes_platform/python/` | `kfp-kubernetes` addon package, docs, and tests. |
| `backend/` | Go backend services, generated API clients, backend tests, and helper images. |
| `frontend/` | React/TypeScript UI, mock backend, server package, and frontend scripts. |
| `manifests/` | Kustomize deployment manifests. |
| `samples/` | User-facing pipeline examples and tutorials. |
| `test/` | Integration, E2E, and maintainer test infrastructure. |

## Install combinations to remember

- Base SDK usage: `pip install kfp`
- KFP plus Kubernetes task helpers: `pip install kfp[kubernetes]`
- Editable checkout work: install from the checked-out source tree only when you are doing repo-maintenance tasks in this repository.

## Version alignment

Keep `kfp`, `kfp-pipeline-spec`, and `kfp-kubernetes` on matching major versions when possible. Mismatched versions are a common source of import or helper-surface failures.

## How to use this reference

Read this file first when a user asks which package to install, which module owns a workflow, why a helper is or is not available, or how the repository is partitioned across SDK, addon, backend, frontend, and manifests work.