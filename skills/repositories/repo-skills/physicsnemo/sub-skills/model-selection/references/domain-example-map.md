# PhysicsNeMo domain example map

This file turns the example tree into routing guidance. The examples are reference patterns, not default smoke tests.

| Domain | Example starting points | What they show | Caveat |
| --- | --- | --- | --- |
| CFD / data-driven surrogates | Darcy FNO tutorial, Vortex Shedding MeshGraphNet tutorial, Lagrangian MGN, Stokes MGN | Grid operators, mesh graphs, and physics-informed fine-tuning | Some examples expect generated data or heavier dependencies. |
| CFD / external aerodynamics | External aerodynamics recipes, DoMINO, Transolver, XAeroNet, Aero Graph Net | Surface/volume geometry workflows and multi-model recipes | Often requires preprocessed meshes, example-specific configs, or external data. |
| Weather / forecasting | FCN-AFNO tutorial, GraphCast weather recipe, DLWP, DLWP-HEALPix, Pangu Weather, StormCast, CorrDiff, ReGen, temporal interpolation | Global and km-scale forecasting, downscaling, generative correction, and temporal interpolation | Many need ERA5-style data, statistics, or pretrained weights. |
| Structural mechanics | Deforming Plate tutorial, crash surrogate recipes, drop-test recipes | MeshGraphNet/Transolver-style surrogates for structural response | Crash workflows are data-heavy and often pair with Curator preprocessing. |
| Healthcare | Bloodflow 1D MGN, brain anomaly detection | Mesh graph surrogates and grid-based anomaly detection | Domain examples may need specialized data preparation. |
| Geophysics | Diffusion FWI recipe | Diffusion-based inverse problems and seismic-style data pipelines | External datasets/checkpoints are commonly required. |
| Additive manufacturing | Sintering physics recipe | MeshGraphNet-style manufacturing surrogate workflows | Usually tied to example-specific data and configs. |
| Molecular dynamics | Lennard-Jones tutorial | Particle/graph-style force prediction | Useful when the user needs graph-based dynamics, not generic chemistry tooling. |
| Reservoir simulation | X-MeshGraphNet recipe | Mesh-graph surrogate workflows for subsurface problems | Example-specific data and preprocessing are expected. |
| Kinetic Monte Carlo | KMC surrogate recipe | GeoTransolver-style surrogate recipes | Specialized domain example, not a generic ML template. |
| Generative | TopoDiff tutorial | Conditional diffusion for topology/design | Requires example-specific configs and typically long training. |
| Active learning | Two-moons active learning tutorial, external-aero active learning recipe | PhysicsNeMo active-learning loop patterns | The examples show orchestration, not a universal training template. |
| Minimal tutorials | Minimal datapipes, minimal mesh, minimal ShardTensor tutorials | Smallest explainers for major package surfaces | Best for smoke checks and learning, not full workflows. |

## Selection guidance

- Use the domain plus data shape together. For example, weather does not automatically mean the same model family as CFD on a grid.
- If the user asks for the best first example, prefer the shortest tutorial that matches the data shape, then mention the heavier domain recipe as the next step.
- If the workflow depends on external data, pretrained weights, or a preprocessing pipeline, say so before recommending the example.
