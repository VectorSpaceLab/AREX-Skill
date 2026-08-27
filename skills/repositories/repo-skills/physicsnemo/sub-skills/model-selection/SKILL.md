---
name: model-selection
description: "Route PhysicsNeMo model families and example starting points from
  data shape, domain, task, and constraints."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PhysicsNeMo model selection

Use this sub-skill when the user needs to choose a PhysicsNeMo model family, import path, or example-style starting point. It is a router: keep the answer short, give a menu of plausible families, name the evidence-backed caveats, and route implementation details to sibling sub-skills.

## Trigger phrases

- "Which PhysicsNeMo model should I use for ...?"
- "Start from a CFD/weather/mesh/diffusion/active-learning example."
- "FNO vs MeshGraphNet vs Transolver vs DoMINO."
- "What import path do I use for this model?"
- "My data is regular grid / lat-lon / HEALPix / mesh / point cloud / particle graph / tabular coordinates."
- "I found an old Modulus or PhysicsNeMo v1 import; what is the current family?"

## First rule: shape before brand names

Do not pick a single model by popularity. Normalize these axes first:

1. **Data shape/topology**: regular Cartesian grid, weather lat-lon, cubed-sphere/HEALPix, unstructured mesh/graph, point cloud with geometry, particle graph, or tabular/coordinate features.
2. **Domain**: CFD/aerodynamics, weather/climate, structural mechanics, healthcare, geophysics, reservoir, molecular dynamics, additive manufacturing, kinetic Monte Carlo, active learning, or generic operator learning.
3. **Task**: deterministic surrogate, autoregressive forecast/rollout, physics-informed/PINO/PINN, super-resolution/downscaling, diffusion/generative/inverse problem, active-learning loop, deployment/export, or scaling.
4. **Constraints**: CPU vs CUDA, optional graph/mesh/weather dependencies, existing data/weights, allowed downloads, required latency, and whether the user wants a tiny smoke, a training recipe, or production integration.

## Clarification gate

Ask a clarifying question before recommending if any of these would change the model family:

- **Grid vs mesh/graph** is unclear.
- **Global weather vs regional km-scale weather** is unclear.
- **Surface-only vs surface+volume CFD geometry** is unclear.
- **Deterministic regression vs stochastic diffusion/downscaling** is unclear.
- **Data are already prepared vs the user needs a data pipeline** is unclear.
- **GPU/extras availability** is unknown for graph, TransformerEngine, NATTEN, HEALPix, mesh, or full weather examples.
- **Full example run vs tiny smoke** is unclear; full domain examples may need external datasets, credentials, pretrained weights, or long GPU training.

## Routing workflow

1. Optionally run the bundled helper for a first-pass menu:

   ```bash
   python sub-skills/model-selection/scripts/choose_physicsnemo_route.py --data-shape "<shape>" --domain "<domain>" --task "<task>"
   ```

2. Open [model-family-map.md](references/model-family-map.md) and shortlist by data shape first. Return a menu when several families apply.
3. Open [domain-example-map.md](references/domain-example-map.md) to name example-style starting points and caveats. Treat these as distilled workflow patterns, not as scripts to run by default.
4. Explain import surface precisely:
   - `physicsnemo.models` root exports only `DiT`, `DoMINO`, and `FullyConnected`.
   - Most families are imported from family subpackages such as `physicsnemo.models.fno`, `physicsnemo.models.meshgraphnet`, or `physicsnemo.models.graphcast`.
   - For lower-stability or optional-backend families, tell the user to confirm class existence in the installed package with a direct import check.
5. Route depth to siblings instead of duplicating it here:
   - Data loading, TensorDict payloads, HDF5/Zarr/VTK/NPZ setup → [datapipes](../datapipes/SKILL.md).
   - DDP/FSDP2, ShardTensor/domain parallel, mesh partitioning, torchrun → [distributed-and-domain-parallel](../distributed-and-domain-parallel/SKILL.md).
   - Mesh validation, repair, sampling, serialization, geometry utilities → [mesh-and-geometry](../mesh-and-geometry/SKILL.md).
   - Diffusion preconditioners, samplers, losses, patching, adapters → [diffusion-and-generative](../diffusion-and-generative/SKILL.md).
   - Active-learning driver/config/protocols or ONNX deployment → [active-learning-and-deployment](../active-learning-and-deployment/SKILL.md).
6. Use [troubleshooting.md](references/troubleshooting.md) for root import mistakes, wrong data shape, optional backend failures, migration/rename issues, missing datasets/weights, and accidental long-running example execution.

## Recommended answer shape

When responding to a user, use this compact structure:

1. **Assumptions**: data shape, domain, task, constraints.
2. **Candidate families**: 2-5 families with import paths and why each fits.
3. **Best starting workflow**: one or two example-style patterns from the domain map, with data/weight caveats.
4. **Sibling routes**: which sub-skills must handle data, distributed, mesh, diffusion internals, active learning, or deployment.
5. **Validation hints**: one tiny shape/import check and one full-example caveat. Never recommend running full training as the default smoke.

## Construction-time verification anchors

This sub-skill was connected to native verification planning for model registry/factory behavior, wrapping a PyTorch module as a PhysicsNeMo module, and the basic FNO tutorial smoke. Large domain examples remain reference-only unless the user explicitly authorizes datasets, credentials, and GPU time.
