---
name: physicsnemo
description: "Route PhysicsNeMo users to the right model, data, scaling, mesh,
  diffusion, active-learning, or deployment workflow."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PhysicsNeMo

Use this repo skill for NVIDIA PhysicsNeMo: a scientific-ML framework for physics-aware models, data pipelines, mesh processing, distributed/domain-parallel execution, diffusion workflows, active learning, and ONNX export.

This skill is a router, not a full manual. Start here to choose the right sub-skill, then follow the bundled reference files and scripts for the detailed workflow.

## Quick start

- Public install: `pip install nvidia-physicsnemo`
- If you need a specific backend or optional workflow, read [optional dependencies](references/optional-dependencies.md) first.
- Tiny smoke: run `python scripts/physicsnemo_environment_smoke.py` after install.
- For contributor/editable use in a local checkout, keep the public package name `nvidia-physicsnemo` and do not depend on this repository path at runtime.

## What to route where

- **Choose a model family or example starting point** → [model-selection](sub-skills/model-selection/SKILL.md)
- **Build readers, datasets, transforms, or `DataLoader` pipelines** → [datapipes](sub-skills/datapipes/SKILL.md)
- **Use `DistributedManager`, DDP/FSDP2, `ShardTensor`, or mesh-parallel launchers** → [distributed-and-domain-parallel](sub-skills/distributed-and-domain-parallel/SKILL.md)
- **Create, validate, repair, sample, serialize, or analyze `Mesh` / `DomainMesh` objects** → [mesh-and-geometry](sub-skills/mesh-and-geometry/SKILL.md)
- **Work with diffusion samplers, preconditioners, guidance, multi-diffusion, or generative recipes** → [diffusion-and-generative](sub-skills/diffusion-and-generative/SKILL.md)
- **Operate active-learning loops or export to ONNX** → [active-learning-and-deployment](sub-skills/active-learning-and-deployment/SKILL.md)

## Root import and package shape

- `physicsnemo.models` root exports only `DiT`, `DoMINO`, and `FullyConnected`.
- Most model families are imported from their family subpackages, such as `physicsnemo.models.fno`, `physicsnemo.models.meshgraphnet`, or `physicsnemo.models.graphcast`.
- `physicsnemo.mesh` root exports the core object model; validation, I/O, sampling, repair, and geometry helpers live in submodules.
- `physicsnemo.active_learning` root exports the driver/config/registry surface; protocol interfaces live in its `protocols` submodule.

If a user asks for an exact class name, backend option, or import path, use [package API map](references/package-api-map.md) and the relevant sub-skill reference rather than guessing from memory.

## Read these first when needed

- [Install and environment](references/install-and-environment.md) — install commands, backend notes, and the package smoke check.
- [Optional dependencies](references/optional-dependencies.md) — extras such as `cu12`, `cu13`, `gnns`, `mesh-extras`, `datapipes-extras`, `sym`, `natten`, and Transformer Engine.
- [Troubleshooting](references/troubleshooting.md) — import mistakes, missing extras, CUDA/backend issues, data/weight access, and long-example overrun prevention.
- [Repository provenance](references/repo-provenance.md) — source commit, package version, dirty-state summary, and evidence paths.

## Selection hints

When the task is ambiguous, resolve these axes before diving deeper:

1. **Data shape**: regular grid, weather lat-lon or HEALPix, unstructured mesh/graph, point cloud, particle graph, or coordinate/tabular inputs.
2. **Task type**: surrogate/regression, autoregressive forecasting, physics-informed training, diffusion/generative, active learning, deployment, or scaling.
3. **Constraints**: CUDA availability, optional extras, external datasets, pretrained weights, latency, and whether the user wants a tiny smoke or a full example.

If the route still depends on the exact model family, open [model-selection](sub-skills/model-selection/SKILL.md) first.

## Minimal verification workflow

1. Install the package and any needed extras.
2. Run `python scripts/physicsnemo_environment_smoke.py`.
3. Route to the appropriate sub-skill.
4. Use that sub-skill’s bundled reference files for the deep workflow.

## Notes

- Do not send users to original repo paths at runtime; only use bundled references and scripts.
- Do not treat large example training jobs as smoke tests.
- Keep experimental APIs labeled experimental when a workflow explicitly depends on them.
