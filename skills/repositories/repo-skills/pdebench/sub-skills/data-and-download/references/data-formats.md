# PDEBench data formats and naming

This reference separates **source-evidence modules** (the native downloader
and visualizer assumptions) from **bundled skill helpers** (the local validator
and safe converter linked from the router). The source modules are not bundled
runtime files. This reference documents metadata and local-file contracts; it
does not download a dataset.

## Dataset metadata

The direct-download source artifact reads `pdebench_data_urls.csv` with columns:
`PDE`, `Filename`, `URL`, `Path`, and `MD5`. The canonical lower-case names accepted
by the native parser are:

`advection`, `burgers`, `1d_cfd`, `diff_sorp`, `1d_reacdiff`, `2d_cfd`, `darcy`,
`2d_reacdiff`, `ns_incom`, `swe`, and `3d_cfd`.

The repository README reports approximate total sizes. Treat these as planning
estimates, not a reservation or a guarantee for a particular filtered shard:

| PDE name | Approximate size |
|---|---:|
| `advection` | 47 GB |
| `burgers` | 93 GB |
| `1d_cfd` | 88 GB |
| `diff_sorp` | 4 GB |
| `1d_reacdiff` | 62 GB |
| `2d_reacdiff` | 13 GB |
| `2d_cfd` | 551 GB |
| `3d_cfd` | 285 GB |
| `darcy` | 6.2 GB |
| `ns_incom` | 2.3 TB |
| `swe` | 6.2 GB |

Always run the bundled metadata checker against a **local copy** of the CSV
before a download. Confirm free space, destination, network policy, and the exact
PDE selection. The direct URLs are public DaRUS data-file URLs and the native
script passes the CSV MD5 to its downloader; a successful process still deserves
an integrity and file-layout check before use.

## File naming and visualization dispatch

The package's `pyproject.toml` exposes the Source repo converter as the
`velocity2vorticity` console entry point, equivalent to
`pdebench.data_gen.velocity2vorticity:convert_velocity`. The native visualizer
source artifact accepts these `--pde_name` values:
`diff_sorp`, `2d_reacdiff`, `swe`, `burgers`, `advection`, `1d_cfd`, `2d_cfd`,
`3d_cfd`, `darcy`, and `1d_reacdiff`. `ns_incom` appears in the metadata list but
its native visualization function is a no-op, so do not promise an animation for
it.

The native visualizer uses these default names when `--param`/`--params` are not
provided (the file must already be in `--data_path`):

| PDE | Expected default filename | Native data access |
|---|---|---|
| `diff_sorp` | `1D_diff-sorp_NA_NA.h5` | group `0000`-style sample, `data`, typically `[time, x, 1]` |
| `1d_reacdiff` | `ReacDiff_Nu1.0_Rho1.0.hdf5` | `x-coordinate`, `tensor`, batch-first `[batch,time,x,channel]` |
| `advection` | `1D_Advection_Sols_beta0.4.hdf5` | `x-coordinate`, `tensor`, batch-first `[batch,time,x,channel]` |
| `burgers` | `1D_Burgers_Sols_Nu0.01.hdf5` | `x-coordinate`, `tensor`, batch-first `[batch,time,x,channel]` |
| `1d_cfd` | `1D_CFD_Rand_Eta1.e-8_Zeta1.e-8_periodic_Train.hdf5` | `x-coordinate`, `density`, batch-first `[batch,time,x,channel]` |
| `2d_reacdiff` | `2D_diff-react_NA_NA.h5` | group `0000`-style sample, `data`, typically `[time,x,y,2]` |
| `swe` | `2D_rdb_NA_NA.h5` | group `0000`-style sample, `data`, typically `[time,x,y,1]` |
| `darcy` | `2D_DarcyFlow_beta1.0_Train.hdf5` | `tensor` and `nu`, batch index 0 |
| `2d_cfd` | `2D_CFD_Rand_M0.1_Eta1e-8_Zeta1e-8_periodic_512_Train.hdf5` | `density`, batch-first 2-D field; exact test-shard shape wins |
| `3d_cfd` | `3D_CFD_Rand_M1.0_Eta1e-8_Zeta1e-8_periodic_Train.hdf5` | `density`; native plot takes a fixed central-z slice |

For parameterized names, the source constructs the following patterns:

- Advection: `1D_Advection_Sols_beta{param}.hdf5`.
- Burgers: `1D_Burgers_Sols_Nu{param}.hdf5`.
- Reaction-diffusion: `ReacDiff_Nu{nu}_Rho{rho}.hdf5`.
- 1-D CFD: `1D_CFD_{type}_Eta{eta}_Zeta{zeta}_{boundary}_Train.hdf5`.
- 2-D CFD: `2D_CFD_{type}_M{mach}_Eta{eta}_Zeta{zeta}_{boundary}_{resolution}_Train.hdf5`.
- 3-D CFD: `3D_CFD_{type}_M{mach}_Eta{eta}_Zeta{zeta}_{boundary}_Train.hdf5`.
- Darcy: `2D_DarcyFlow_beta{param}_Train.hdf5`.

`--params` is positional text, not a comma-delimited single value: 1-D CFD
expects four values `[type, eta, zeta, boundary]`, 2-D CFD six values
`[type, M, eta, zeta, boundary, resolution]`, and 3-D CFD five values
`[type, M, eta, zeta, boundary]`. The native source concatenates a path and
filename while checking some parameterized files; provide a data path ending in
`/` (or use a path spelling that preserves that join) when using the native CLI.

## HDF5 inspection contract

Start read-only. A minimal inventory is:

```python
import h5py
with h5py.File("FILE.hdf5", "r") as f:
    def show(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(name, obj.shape, obj.dtype)
    f.visititems(show)
```

Do not infer a model-ready layout from a filename alone. Confirm dataset names,
rank, axis meaning, dtype, coordinate lengths, and whether the first axis is batch
or time. Grouped files use zero-padded sample keys in the native visualizer; the
converter described below uses root-level CFD datasets.

### 3-D CFD velocity-to-vorticity schema

The source converter's input contract is a root-level HDF5 file containing:

- `Vx`, `Vy`, `Vz`: equal-shaped five-dimensional arrays
  `[trial, time, x, y, z]` (the source loops over `trial` and passes each
  four-dimensional `[time,x,y,z]` field to the spectral API).
- `t-coordinate`: one-dimensional coordinate of length `time`.
- `x-coordinate`, `y-coordinate`, `z-coordinate`: one-dimensional coordinates
  whose lengths are respectively `x`, `y`, and `z`.

The **Bundled skill helper**
[convert_velocity_to_vorticity.py](../scripts/convert_velocity_to_vorticity.py)
validates this contract, derives `dx`, `dy`, and `dz` from the coordinate arrays,
requires finite nonzero uniform spacing, and refuses a missing or mismatched
schema. It writes a local output with the same trial/time/spatial shape for each
of:

- `omega_x`: `∂Vz/∂y - ∂Vy/∂z`
- `omega_y`: `∂Vx/∂z - ∂Vz/∂x`
- `omega_z`: `∂Vy/∂x - ∂Vx/∂y`

It also copies `t-coordinate`, `x-coordinate`, `y-coordinate`, and
`z-coordinate`, and records backend and spacing attributes. The default output
name is `<input-stem>_vorticity.hdf5`; use `--output` to choose another path and
`--overwrite` to replace an existing file. The helper writes through a temporary
file so a failed conversion does not leave a falsely complete output.

The public source API accepts an in-memory velocity array of shape
`[n, sx, sy, sz, 3]` plus scalar `dx`, `dy`, and `dz`:

```python
import jax.numpy as jnp
import numpy as np
from pdebench.data_gen.src.vorticity import (
    compute_spectral_vorticity_np,
    compute_spectral_vorticity_jnp,
)

omega_np: np.ndarray = compute_spectral_vorticity_np(
    velocities, dx, dy, dz
)
omega_jnp: jnp.ndarray = compute_spectral_vorticity_jnp(
    jnp.asarray(velocities), dx, dy, dz
)
```

`compute_spectral_vorticity_np(velocities, dx, dy, dz) -> np.ndarray` returns a
NumPy array of the same shape. The JAX variant has the analogous
`jnp.ndarray` return and is JIT-decorated. Both APIs use periodic spectral
derivatives and take absolute values of the spacings; the Bundled helper is
stricter and rejects nonuniform or invalid coordinate arrays before calling them.
The spectral assumption matters: a non-periodic or strongly nonuniform grid needs
a different derivative method.

## Visualization outputs and safety

The native visualizer writes animation files in the current working directory,
including `movie_diff_sorp.gif`, `movie_2d_reacdiff.gif`, `movie_swe.gif`,
`movie_burgers.gif`, `movie_advection.gif`, `movie_1d_cfd.gif`, and `movie.gif`
for some 2-D/3-D CFD paths. The Darcy route writes `2D_DarcyFlow.pdf`. Use a
scratch output directory and a fixed `--seed_number` for reproducibility. These
commands read local files but are not read-only with respect to the current
working directory because they create figures.
