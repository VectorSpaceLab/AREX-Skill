# Optional dependencies

PhysicsNeMo publishes many optional dependency groups. This table summarizes the ones that matter most for common routes.

| Extra | Use when | Notes |
| --- | --- | --- |
| `cu12` | CUDA 12.8-oriented GPU install | Pulls the CUDA 12 package family for core GPU workflows. |
| `cu13` | CUDA 13-oriented GPU install | Use when the environment targets CUDA 13 wheels/packages. |
| `gnns` | Graph-based models and datasets | Helpful for MeshGraphNet, GraphCast, and related GNN workflows. |
| `datapipes-extras` | Climate, Zarr, NetCDF, Dask, TensorStore data paths | Useful for ERA5, climate, and large-format datapipe workflows. |
| `mesh-extras` | Mesh visualization/conversion | Brings PyVista/VTK/matplotlib helpers for mesh workflows. |
| `sym` | Physics-informed / PINO / PINN recipes | Needed for symbolic PDE residual workflows. |
| `model-extras` | Broader model-side workflows | Includes secondary model-support dependencies. |
| `utils-extras` | Logging/profiling/experiment helpers | Useful when a workflow depends on W&B, MLflow, line profiling, or VTK utilities. |
| `uq-extras` | Uncertainty-quantification workflows | Needed for gpytorch-based UQ paths. |
| `natten-cu12` / `natten-cu13` | Neighborhood attention examples | Use the matching CUDA variant. |
| `transformer-engine-cu12` / `transformer-engine-cu13` | Transformer Engine examples | Use the matching CUDA variant. |
| `onnxscript` | ONNX export with recent PyTorch exporters | Not a PhysicsNeMo extra in the base install, but may be needed by `torch.onnx.export`. |

## Guidance

- Install only the extras that a selected workflow actually needs.
- Some example READMEs request extra packages beyond the base distribution; treat those as workflow-specific, not universal.
- Optional dependencies may be absent even when the base package imports successfully.
- If a route needs a missing extra, record it as a workflow requirement rather than silently skipping the capability.
