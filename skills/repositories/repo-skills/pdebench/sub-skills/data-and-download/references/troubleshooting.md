# Troubleshooting data and vorticity workflows

## Install and import failures

- **`ModuleNotFoundError: pdebench`**: install the package in the active Python
  environment, or run from an environment where the package is already installed.
  Confirm with `python -c 'import pdebench; print(pdebench.__version__)'` when the
  version attribute is available. Do not make a bundled helper depend on the
  current checkout being the working directory.
- **Downloader import errors for `torchvision`/`tqdm`/`pandas`**: the Source repo
  artifact imports these at startup. Install the package's base dependencies in
  the active environment, then retry only `--help` or local metadata checks.
  The Bundled metadata checker intentionally uses the standard library and does
  not import the downloader.
- **Visualization import errors**: local visualization requires `h5py`, NumPy,
  Matplotlib, and a Matplotlib animation writer (Pillow for GIF output). Install
  the missing optional dependency in the environment; do not solve a plotting
  import by downloading data.
- **`jax` unavailable**: use the converter's default `--backend numpy` and run
  `vorticity_smoke.py --backend numpy`. Install a compatible CPU JAX only when
  the JAX API is required. JAX 0.4.38 CPU was verified for this skill; the
  repository's older documented JAX version is not a promise that every newer
  resolver can install it.
- **CUDA warnings or unavailable device**: CUDA is optional and unverified in
  the prepared environment. Do not change a correct CPU result solely because
  CUDA is absent. Use NumPy or CPU JAX, record the backend, and reserve GPU
  installation/verification for a separately approved environment.

## Metadata and PDE-name failures

- **`PDE name not defined` or `unknown PDE`**: use lower-case canonical names:
  `advection`, `burgers`, `1d_cfd`, `diff_sorp`, `1d_reacdiff`, `2d_cfd`,
  `darcy`, `2d_reacdiff`, `ns_incom`, `swe`, `3d_cfd`. Run
  `check_dataset_metadata.py --list-pdes` and inspect the local CSV header.
- **CSV not found**: pass `--metadata` explicitly to the bundled checker. The
  native downloader has no metadata-path argument and reads
  `pdebench_data_urls.csv` relative to its current working directory. Launch
  the installed module from a user-owned directory containing the trusted CSV;
  do not use a package checkout as the metadata directory.
- **Malformed metadata**: require the exact header fields `PDE`, `Filename`,
  `URL`, `Path`, and `MD5`; remove blank rows or repair the local copy from a
  trusted source. The checker does not fetch a replacement CSV.
- **No rows for a valid name**: the name may be valid but absent from the local
  CSV revision. Report the discrepancy and inspect the CSV version rather than
  treating an empty selection as a successful download plan.

## Invalid file paths and visualization conventions

- **File does not exist**: inspect the local directory and use the exact
  case-sensitive filename from [data-formats](data-formats.md). The names encode
  PDE parameters and train/test placement; do not approximate them.
- **Parameterized native visualization says `no such file` despite a visible
  file**: use a trailing slash in `--data_path`, because several source checks
  concatenate `path + filename`. Then verify the exact decimal spelling (`1e-8`
  versus `1.e-8`, for example).
- **Unsupported `--pde_name`**: the visualizer dispatch set is smaller than the
  metadata set. In particular, `ns_incom` has a no-op native function and should
  be treated as unsupported for useful animation.
- **`KeyError` in an HDF5 file**: run a read-only `h5py` inventory and compare
  dataset names and rank with the expected contract. Do not rename datasets in
  place or overwrite the downloaded source file to make a plot work.
- **Animation output is missing**: run from a writable scratch directory and
  check that Matplotlib's Pillow writer is installed. Native visualization writes
  fixed names and may overwrite an old figure in that directory.

## HDF5 schema and spacing failures

The Bundled converter expects root-level `Vx`, `Vy`, `Vz`, `t-coordinate`,
`x-coordinate`, `y-coordinate`, and `z-coordinate`.

- **Missing dataset**: stop and report the missing key. A grouped file with
  `0000/data` is a visualization input, not a converter input.
- **Shape mismatch**: `Vx`, `Vy`, and `Vz` must be equal four-dimensional arrays
  `[trial,time,x,y,z]`; coordinate lengths must equal the corresponding axes.
  The public in-memory API instead receives `[n,sx,sy,sz,3]` after the three
  components have been stacked on the last axis.
- **Bad time coordinate**: `t-coordinate` must be one-dimensional with length
  `time`; it is copied to the output and is not used to derive spatial spacing.
- **Bad spatial coordinate**: each spatial coordinate must be one-dimensional,
  finite, monotone, have at least two points, and have nonzero approximately
  uniform differences. The helper derives `dx`, `dy`, and `dz` from the mean
  absolute consecutive difference and reports them. Fix the coordinate/data
  pairing rather than passing a guessed spacing.
- **Nonuniform or nonperiodic grid**: spectral differentiation assumes an
  equidistant periodic grid. The helper rejects nonuniform spacing; it does not
  silently resample or claim finite-difference accuracy. Use a separately
  validated derivative method for a different grid.
- **Output already exists**: choose a new `--output` or add `--overwrite` after
  confirming the old file is disposable. The helper refuses accidental replacement
  and uses a temporary file during conversion.
- **Input and output are the same file**: this is refused. Never overwrite a
  source velocity file with its derived fields.

## Spectral vorticity and backend failures

Both public functions require `velocities.ndim == 5` and
`velocities.shape[-1] == 3`; otherwise they raise `ValueError` with the expected
shape. Check the stacking order is `[Vx, Vy, Vz]`, not `[x,y,z]` or a channel-first
layout. The returned components follow the right-handed curl convention:

```text
omega_x = dVz/dy - dVy/dz
omega_y = dVx/dz - dVz/dx
omega_z = dVy/dx - dVx/dy
```

- **NumPy smoke mismatch**: check coordinate spacing, axis order, periodicity,
  and component order. Run the deterministic smoke before debugging a large
  file; it should report a small max error.
- **JAX import/device/compilation error**: repeat with `--backend numpy` to
  separate numerical/schema errors from JAX setup. Ensure the JAX array is
  created from the validated field and that scalar spacings are finite. CPU JAX
  is the verified route; CUDA JAX is optional/unverified.
- **JAX and NumPy differ materially**: compare `np.asarray(jax_result)` with the
  NumPy result on the same tiny field and dtype. Large differences usually mean
  different spacing, axis ordering, precision settings, or a non-periodic input,
  not a reason to switch backends blindly.
- **Unexpected precision**: preserve the source dtype where possible and record
  the backend in output attributes. For strict comparisons, use tolerances
  appropriate to the dtype and JAX precision configuration.

## Network, credentials, and data safety

The direct DaRUS path is public but still networked, large, and externally
versioned. Check URL provenance and CSV MD5 values, use a dedicated destination,
set a bounded operational window, and retain download logs. Do not run it merely
to test imports. A failed or interrupted large transfer should be checked for
partial files and hashes before reuse.

The EasyDataverse and uploader paths are reference-only. They may contact a
Dataverse API and require DOI/URL/token configuration. Keep tokens in a secret
manager or protected environment, never in command arguments, committed files,
logs, or output HDF5 attributes. Ask for explicit authorization before any
credentialed read or write. A network failure is not permission to retry against
a different endpoint or upload generated data.

## Verification evidence boundary

The native vorticity test suite is **source-evidence-only**, not a runtime
dependency. It establishes NumPy/JAX spectral behavior on a random
`[10,16,32,32,3]` field with `dx=1/sx`, `dy=1/sy`, and `dz=1/sz`. The bundled
deterministic smoke provides a repeatable local check without relying on a
checkout or pytest fixtures. Keep native test reports outside the runtime skill
tree.
