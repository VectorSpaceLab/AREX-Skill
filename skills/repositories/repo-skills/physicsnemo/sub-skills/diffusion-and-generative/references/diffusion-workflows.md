# PhysicsNeMo diffusion workflows

## Two workflows, two levels of detail

### API building block

Use this path when the user needs imports, signatures, a minimal adapter, or a safe smoke. Focus on:

- `DiffusionModel`, `Predictor`, `Denoiser`
- noise schedulers and preconditioners
- samplers and solvers
- guidance and patching/multi-diffusion helpers

### Full domain recipe

Use this path when the user wants a real CorrDiff, StormCast, CFD, geophysics, or TopoDiff workflow. First confirm:

- trained weights or checkpoints are available,
- required datasets and statistics are present,
- the example-specific optional dependencies are installed,
- the user is willing to run a real CUDA workflow if needed.

## Example families to mention

- `SongUNet`, `DhariwalUNet`, and `StormCastUNet` for diffusion U-Nets.
- `DiT` for diffusion-transformer style recipes.
- `TopoDiff` for conditional topology/design workflows.
- `DPOTNet` where the example specifically targets operator-style diffusion.

## Safe ordering

1. Inspect the package API and signatures.
2. Decide whether the user wants a sampler, preconditioner, guidance path, or full recipe.
3. Route data prep to `../datapipes/` and scaling to `../distributed-and-domain-parallel/`.
4. Run a tiny smoke before any expensive example or training command.
