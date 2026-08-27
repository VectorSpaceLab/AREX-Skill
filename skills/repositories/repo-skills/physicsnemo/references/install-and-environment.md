# Install and environment

This skill is intended to work from the published PhysicsNeMo package, not from the source checkout.

## Public install

```bash
pip install nvidia-physicsnemo
```

## Common extras

Use extras only when a workflow needs them:

- `cu12` or `cu13` — CUDA package variants for GPU-oriented installs.
- `gnns` — graph-model workflows such as MeshGraphNet/GraphCast family examples.
- `datapipes-extras` — Zarr, NetCDF4, xarray, dask, and related datapipe formats.
- `mesh-extras` — PyVista/matplotlib/VTK mesh visualization and conversion helpers.
- `sym` — physics-informed / PINN / PINO workflows.
- `model-extras` — broader model-side extras for some examples.
- `natten-cu12` or `natten-cu13` — prebuilt NATTEN wheels when a workflow explicitly needs them.
- `transformer-engine-cu12` or `transformer-engine-cu13` — Transformer Engine workflows.

The base package import is the first smoke test; only add extras when a workflow requires them.

## Tiny smoke

Run the bundled helper after install:

```bash
python scripts/physicsnemo_environment_smoke.py
```

It prints package version, key imports, and CUDA availability if present.

## CUDA note

PhysicsNeMo is GPU-oriented. Many workflows can be imported on CPU, but domain-parallel and many example workflows need a CUDA-capable environment to be fully validated.

## Install troubleshooting

- If a mirror misses a pinned nightly or NVIDIA wheel, retry against public PyPI and, when needed, the NVIDIA wheel index.
- If `pip check` fails, fix the environment before using the skill.
- Do not assume a CPU import proves a GPU workflow works.
- Do not install every optional extra just to inspect the package; choose the smallest set that covers the requested route.
