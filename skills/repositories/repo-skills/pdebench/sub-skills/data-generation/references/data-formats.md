# Data, environment, and output conventions

## Environment and `.env`

The package declares Python `>=3.9,<3.11`. The recorded inspection baseline for
this skill is Python 3.10, Hydra 1.3.5, CPU JAX 0.4.38, and NumPy 1.26.4.
Optional phiflow, Lightning, Clawpack, and CUDA variants are not installed in
that baseline. This revision's live shell probe was Python 3.13 with Hydra and
JAX unavailable, so the recorded baseline is not a current-environment claim.
Do not silently substitute a GPU JAX build or a different Python major version
for a reproducibility check.

The published package's `example.env` is source evidence for these fields; it is
not bundled by this skill and must not be read from a checkout:

```dotenv
WORKING_DIR=...
ARTEFACT_DIR=...
#OUTPUT_DIR=...
DEBUG_DIR=debug
DATAVERSE_URL=...
DATAVERSE_API_TOKEN=...
DATAVERSE_ID=...
```

Use a local file named exactly `.env` only for non-secret path defaults and
machine-local settings. The classical wrappers call `dotenv.load_dotenv()`;
Hydra interpolations also read `WORKING_DIR`, `ARTEFACT_DIR`, and `DEBUG_DIR`
through environment resolvers. `WORKING_DIR` controls the default Hydra run
root for the diffusion/sorption/radial configs; `ARTEFACT_DIR` is used by the
incompressible Navier–Stokes config. Resolve paths with `--cfg job --resolve`
before a real run because Hydra's current directory is not necessarily the
shell's current directory.

Never put a real Dataverse token in a skill, command transcript, committed
config, or generated artifact. `DATAVERSE_URL`, `DATAVERSE_API_TOKEN`, and
`DATAVERSE_ID` are upload inputs only. Keep `upload=false` and omit upload
fields for inspection and verification. Upload is a separate, explicitly
approved network action and is not part of data generation verification.

## Classical HDF5 writers

The diffusion/sorption wrappers create one HDF5 file under a Hydra-derived data
path. Each seed is a zero-padded group, normally `0000`, `0001`, and so on:

```text
<file>.h5
└── 0000/
    ├── data        float32, compressed with lzf
    └── grid/
        ├── x       float32
        ├── y       float32       # diffusion-reaction and radial dam break
        └── t       float32
```

The group has a `config` attribute containing the resolved OmegaConf YAML.
Diffusion-reaction's helper returns `(time, y, x, 2)` for the `u` and `v`
channels. Diffusion-sorption returns `(time, x, 1)`. The radial dam-break saver
expands the saved water-height field with a final channel dimension and writes
`data`, `grid/x`, `grid/y`, and `grid/t` under the seed group. Always inspect
actual shapes with `h5py` rather than assuming the order from a filename.

A read-only inspection recipe for a file that already exists:

```bash
python - <<'PY'
from pathlib import Path
import h5py

path = Path("<approved-output>.h5")
with h5py.File(path, "r") as f:
    for seed in list(f)[:2]:
        print(seed, list(f[seed]))
        print("data", f[seed]["data"].shape, f[seed]["data"].dtype)
        print("config", "config" in f[seed].attrs)
PY
```

The recipe uses a placeholder path intentionally; replace it only after an
output directory has been approved.

## Incompressible Navier–Stokes HDF5

The source-evidence module `pdebench.data_gen.src.data_io` allocates a file
named `<sim_name>-<seed>.h5` with top-level
float32, lzf-compressed datasets:

```text
velocity    (batch, frames, x, y, vector)
particles   (batch, frames, x, y, 1)
force       (batch, x, y, vector)
t            (batch, frames)
```

The frame count is `((n_steps - 1) // frame_int) + 1`. The file attributes
include the serialized config and `latestIndex`. The exact output path is
affected by Hydra and by `sim_name`/`seed`; never collide two runs by reusing a
working directory. This writer imports phiflow/`phi`, so this format cannot be
verified on the CPU-only baseline when that optional package is absent.

## NLE NumPy/JAX outputs

NLE generators save NumPy-compatible arrays with `jax.numpy.save` (normally
`.npy`) plus coordinate arrays. The multi-solution code uses the leading sample
axis followed by saved time and spatial axes; the exact leading shape can be
observed after a tiny run because device sharding is reshaped before saving.
Common evidence-backed names are:

- Advection: `1D_Advection_Sols_beta<beta>.npy`,
  `x_coordinate.npy`, `t_coordinate.npy`.
- Burgers: `1D_Burgers_Sols_Nu<epsilon>.npy`,
  `x_coordinate.npy`, `t_coordinate.npy`.
- Reaction-diffusion: `ReacDiff_Nu<nu>_Rho<rho>.npy`,
  `x_coordinate.npy`, `t_coordinate.npy`.
- Compressible CFD: `HD_Sols_<mode>_Eta<eta>_Zeta<zeta>_M<M>_key<key>_<D|P|Vx|Vy|Vz>.npy`,
  plus coordinate files. `Vy` is present for dimension 2/3 and `Vz` for 3D;
  the source still allocates singleton dimensions for 1D.

The source's generic helpers also use `Data_<index>.npy` and
`x_coordinate`/`y_coordinate`/`z_coordinate`/`t_coordinate` for some routes.
Do not mix output families, dimensions, boundary modes, or parameter values in
one `savedir`: `pdebench.data_gen.data_gen_NLE.Data_Merge` discovers files by
glob and filename tokens.

For an approved `.npy` directory, inspect without modifying it:

```bash
python - <<'PY'
from pathlib import Path
import numpy as np

root = Path("<approved-npy-directory>")
for path in sorted(root.glob("*.npy")):
    a = np.load(path, mmap_mode="r")
    print(path.name, a.shape, a.dtype)
PY
```

Estimate memory before loading a full array:

```text
bytes ~= numbers * saved_times * nx * ny * nz * channels * itemsize
```

JAX may hold compiled/intermediate buffers in addition to the saved array.
`numbers`, spatial resolution, final time, and `dt_save` therefore all matter.

## Data_Merge expectations

The NLE documentation describes the intended sequence: generate `.npy` files,
provide the merge module's Hydra `args` values, and invoke
`pdebench.data_gen.data_gen_NLE.Data_Merge`. The config fields are:

```yaml
args:
  type: advection | burgers | ReacDiff | CFD
  dim: 1 | 2 | 3
  bd: periodic | trans
  nbatch: <approved batch count>
  savedir: <one homogeneous output directory>
```

For 1D `advection`, `burgers`, and `ReacDiff`, `transform` writes an HDF5 with
`tensor`, `x-coordinate`, and `t-coordinate`; it also records PDE-specific
attributes (`beta`, `Nu`, or `Nu`/`rho`). For CFD, the intended HDF5 has
`density`, `pressure`, `Vx`, and dimension-appropriate `Vy`/`Vz`, coordinate
datasets, and `eta`/`zeta`/`M` attributes. The merge code expects CFD files
with names containing `HD`, variable suffixes, `key`, and parameter tokens.

The inspected merge implementation currently has apparent runtime defects
including `Path.glob(...).sort()` on a glob iterator and multiple
`create_dataet` typos. Therefore these are **format expectations**, not a
verified claim that the installed module can complete. Do not overwrite the
package or repair it as part of a normal generation request. Report a merge
blocker and preserve the raw `.npy` output until an approved fix is separately
tested.

## Reproducibility record

For every approved trial retain, outside this skill tree:

- the selected config file and fully resolved Hydra config;
- all CLI overrides, `seed`/`init_key`, JAX backend/device, and package versions;
- output directory, file names, array shapes/dtypes, and approximate byte size;
- whether output was in-memory, `.npy`, or HDF5; and
- any optional dependency or backend caveat.

A help-only rendering or a tiny in-memory fixture is evidence of routing and
parser compatibility only. It is not evidence of full-data correctness,
long-run stability, merge correctness, upload success, or benchmark fidelity.
