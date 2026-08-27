# Package API map

This is a compact route map for the top-level package surfaces.

| Package area | What it owns | Where to look next |
| --- | --- | --- |
| `physicsnemo.models` | Model families and family subpackages | `model-selection` and the family-specific model docs |
| `physicsnemo.datapipes` | Readers, datasets, transforms, loaders, collation | `datapipes` |
| `physicsnemo.distributed` | `DistributedManager`, launch/process-group helpers | `distributed-and-domain-parallel` |
| `physicsnemo.domain_parallel` | `ShardTensor`, `scatter_tensor`, `sync_module_over_mesh` | `distributed-and-domain-parallel` |
| `physicsnemo.mesh` | `Mesh`, `DomainMesh`, field helpers | `mesh-and-geometry` |
| `physicsnemo.diffusion` | Diffusion base classes and workflow pieces | `diffusion-and-generative` |
| `physicsnemo.active_learning` | Active-learning configs, driver, registry | `active-learning-and-deployment` |
| `physicsnemo.deploy` | ONNX export/runtime helpers | `active-learning-and-deployment` |
| `physicsnemo.metrics` | General and climate metrics | `active-learning-and-deployment` or the nearest workflow reference |
| `physicsnemo.optim` | Optimizer helpers | `active-learning-and-deployment` when used with iterative loops |
| `physicsnemo.utils` | Checkpointing, logging, profiling, capture helpers | `active-learning-and-deployment` or the workflow that needs them |
| `physicsnemo.core` | Base module, registry, metadata, version utilities | any route that needs import/version/registry details |

## Root import shape to remember

- `physicsnemo.models` root exports only `DiT`, `DoMINO`, and `FullyConnected`.
- `physicsnemo.mesh` root exports the core object model and field-rank helpers; validation helpers live in submodules.
- `physicsnemo.active_learning` root exports the driver/config/registry surface; protocol interfaces live in its `protocols` submodule.
