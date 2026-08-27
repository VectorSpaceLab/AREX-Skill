# Data, visualization, and conversion commands

Set `SKILL_ROOT` to the directory containing this sub-skill's `SKILL.md` when
using the bundled helpers. Set `METADATA_CSV` to a trusted, user-owned local
copy of the PDEBench metadata CSV. The CSV is not bundled in this skill and
must not be resolved from a package checkout.

## Safe first steps (no download)

List metadata names and row counts from a local CSV:

```bash
python "$SKILL_ROOT/scripts/check_dataset_metadata.py" \
  --metadata "$METADATA_CSV" --list-pdes
```

Validate one or more names without opening a network connection:

```bash
python "$SKILL_ROOT/scripts/check_dataset_metadata.py" \
  --metadata "$METADATA_CSV" \
  --pde-name 3d_cfd --pde-name diff_sorp --show-files
```

The helper prints `VALID` plus matching row/file information. It only reads the
CSV, rejects unknown names, and never imports a downloader or calls a URL. Run
its parser check with:

```bash
python "$SKILL_ROOT/scripts/check_dataset_metadata.py" --help
```

Check installed package parsers without side effects:

```bash
python -m pdebench.data_download.download_direct --help
python -m pdebench.data_download.visualize_pdes --help
python -m pdebench.data_gen.velocity2vorticity --help
```

The package declares `velocity2vorticity` as a console entry point as well. The
module form is preferred here because it remains explicit about which installed
package is being used.

The native downloader's `--help` has two relevant flags:

- `--root_folder PATH` (required for an actual download): destination root.
- `--pde_name NAME` (repeatable): one canonical lower-case PDE name per flag.

## Intentional network download (never a default)

Only after metadata, disk, network, and provenance checks pass may an operator
run the installed native downloader. It reads `pdebench_data_urls.csv` from
its process working directory, so provide a **user-owned** directory containing
the trusted CSV; do not point this at a source checkout:

```bash
: "${METADATA_DIR:?Set METADATA_DIR to a user-owned directory containing the trusted CSV}"
(
  cd "$METADATA_DIR" || exit 1
  python -m pdebench.data_download.download_direct \
    --root_folder "$DATA_ROOT" --pde_name diff_sorp
)
```

Repeat `--pde_name` for additional datasets. This can consume approximately the
full size listed in [data-formats](data-formats.md), creates nested paths from
the CSV, and contacts DaRUS. Do not use `ns_incom`, `2d_cfd`, or `3d_cfd` as a
casual smoke test. Prefer one known small shard only after confirming the exact
target. A successful process still needs an integrity and file-layout check.

The EasyDataverse/Hydra path is **reference-only** and not a default command. It
can require a Dataverse URL, DOI, filename filter, and service credentials. Do
not put API keys in shell history, Markdown, or HDF5 attributes. Uploading via
the source uploader is out of scope for this sub-skill.

## Visualize an already-downloaded file

Run the module from a writable user-owned scratch directory so generated GIF or
PDF files do not overwrite unrelated work. Set `RUN_DIR` as the caller's
scratch directory and launch the command there; the native visualizer writes
fixed output names in its current directory.

```bash
mkdir -p "$RUN_DIR"
cd "$RUN_DIR" || exit 1
python -m pdebench.data_download.visualize_pdes \
  --pde_name diff_sorp --data_path "$DATA_DIR/" --seed_number 0
```

Other safe local examples:

```bash
python -m pdebench.data_download.visualize_pdes \
  --pde_name 2d_reacdiff --data_path "$DATA_DIR/" --seed_number 0
python -m pdebench.data_download.visualize_pdes \
  --pde_name swe --data_path "$DATA_DIR/" --seed_number 0
python -m pdebench.data_download.visualize_pdes \
  --pde_name advection --data_path "$DATA_DIR/" --param 0.4
python -m pdebench.data_download.visualize_pdes \
  --pde_name burgers --data_path "$DATA_DIR/" --param 0.01
python -m pdebench.data_download.visualize_pdes \
  --pde_name 1d_reacdiff --data_path "$DATA_DIR/" --params 1.0 1.0
```

For 1-D CFD use four `--params` values (`type eta zeta boundary`), for 2-D CFD
six (`type M eta zeta boundary resolution`), and for 3-D CFD five (`type M eta
zeta boundary`). Example parameter forms are given in [data-formats](data-formats.md).
Use `--data_path "$DATA_DIR/"` with the trailing slash because the native
parameterized existence check concatenates strings.

Expected output is a new GIF or PDF in the scratch directory; a successful
process may still produce a visually uninformative plot if the selected field
is constant. A missing file, missing dataset key, or unsupported `--pde_name`
should be fixed by checking the HDF5 inventory and filename convention, not by
downloading another large dataset blindly.

## Convert local 3-D CFD velocity to vorticity

The bundled helper is context-independent and defaults to NumPy/CPU. It
performs no download or upload:

```bash
python "$SKILL_ROOT/scripts/convert_velocity_to_vorticity.py" \
  --input "$DATA_DIR/3D_CFD_Rand_M1.0_Eta1e-8_Zeta1e-8_periodic_Train.hdf5" \
  --output "$RUN_DIR/velocity_vorticity.hdf5" --backend numpy
```

Use `--overwrite` only when replacement is deliberate:

```bash
python "$SKILL_ROOT/scripts/convert_velocity_to_vorticity.py" \
  --input "$INPUT_H5" --output "$OUTPUT_H5" --backend numpy --overwrite
```

`--backend jax` uses the public JAX API and can select an accelerator if the JAX
environment is configured; recorded CPU JAX evidence exists, but the current
review shell did not have JAX installed. JAX is not required for safe NumPy
conversion. The helper validates root-level `Vx`, `Vy`, `Vz`, coordinate arrays,
equal shapes, finite uniform spacing, and the `[trial,time,x,y,z]` contract
before creating output. It writes `omega_x`, `omega_y`, `omega_z` plus all four
coordinate datasets and reports derived spacing/output schema on success.

Inspect a converted file without loading all fields:

```bash
python - <<'PY'
import h5py
with h5py.File("OUTPUT_H5", "r") as f:
    for name, obj in f.items():
        print(name, getattr(obj, "shape", "group"), getattr(obj, "dtype", ""))
PY
```

Run the deterministic API smoke (no HDF5 or network):

```bash
python "$SKILL_ROOT/scripts/vorticity_smoke.py" --backend both
```

Use `--backend numpy` when JAX is not installed. `--help` is always safe:

```bash
python "$SKILL_ROOT/scripts/convert_velocity_to_vorticity.py" --help
python "$SKILL_ROOT/scripts/vorticity_smoke.py" --help
```
