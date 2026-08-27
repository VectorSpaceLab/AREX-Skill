---
name: data-and-download
description: "Safely inspect PDEBench dataset metadata and local HDF5 data,
  visualize downloaded files, and convert 3D CFD velocity fields to vorticity
  with verified CPU NumPy/JAX paths."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data and download

Use this sub-skill for **metadata-first, local-data workflows**: identify a PDEBench
shard, inspect its expected HDF5 names and shapes, visualize a file that is already
local, or convert a local 3D CFD velocity field to vorticity. Do not begin a
multi-gigabyte download, upload, simulation, training run, or benchmark evaluation
without an explicit user request and a storage/network/credential check.

## Route quickly

1. Read [data formats](references/data-formats.md) before opening an HDF5 file or
   constructing a filename.
2. Use [the CLI reference](references/cli-reference.md) for commands. Start with
   the metadata checker and `--help`; these have no network side effect.
3. Use [the troubleshooting guide](references/troubleshooting.md) when imports,
   paths, schemas, coordinates, or spectral backends fail.
4. For a local 3D CFD file, use the bundled converter with an explicit output path
   and `--overwrite` only when replacement is intentional. Its default backend is
   NumPy/CPU; JAX is an opt-in acceleration path.
5. Run the deterministic [vorticity smoke](scripts/vorticity_smoke.py) after an
   install change or API change.

## Scope and boundaries

- **Source-evidence modules:** `pdebench.data_download.download_direct`,
  `pdebench.data_download.visualize_pdes`, and
  `pdebench.data_gen.velocity2vorticity` establish native names, dispatch, and
  schemas. Their source artifacts are not copied into this runtime tree. The
  native downloader must never be treated as a harmless default action.
- **Bundled skill helpers:**
  [metadata checker](scripts/check_dataset_metadata.py) reads a local CSV only;
  [safe converter](scripts/convert_velocity_to_vorticity.py) reads/writes local
  HDF5 only with explicit output/overwrite behavior; and
  [vorticity smoke](scripts/vorticity_smoke.py) uses a deterministic tiny fixture.
- Full PDE simulation/Hydra generation routes to `data-generation`. Model
  training, evaluation, and metrics route to `models-and-evaluation`.
- The EasyDataverse downloader and uploader are reference-only. They require
  external service access and possibly credentials; neither is a default route.

## Verified operating facts

Recorded inspection evidence verified Python 3.10, `pdebench` 0.1.0, NumPy
1.26.4, JAX 0.4.38 on CPU, and PyTorch 1.13.1 on CPU. NumPy and JAX spectral
vorticity APIs and the CPU path were verified in that recorded environment. The
current review shell used Python 3.13 and did not have JAX installed, so those
facts are not current-shell verification. CUDA may be useful for acceleration,
but is optional and unverified; do not claim GPU verification.

## Bundled files

- [HDF5 layouts, metadata names, sizes, and filename conventions](references/data-formats.md)
- [Safe commands and accepted native flags](references/cli-reference.md)
- [Recovery and failure diagnosis](references/troubleshooting.md)
- [Local CSV/PDE metadata validator](scripts/check_dataset_metadata.py)
- [Explicit-output velocity-to-vorticity converter](scripts/convert_velocity_to_vorticity.py)
- [Deterministic NumPy/JAX API smoke](scripts/vorticity_smoke.py)
