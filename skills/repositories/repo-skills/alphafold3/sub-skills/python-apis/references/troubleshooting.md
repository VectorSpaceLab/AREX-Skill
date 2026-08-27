# Python API Troubleshooting

Use this for Python import, package-resource, and internal-API failures. For CLI invocation and prediction-run failures, route to `../running-predictions/`; for JSON schema mistakes, route to `../input-preparation/`; for confidence/output questions, route to `../output-interpretation/`.

## Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'alphafold3'`.
- `PackageNotFoundError` when querying the `alphafold3` distribution.
- Import succeeds for `alphafold3` but fails for C++ backed modules under `alphafold3.cpp` or structure parsing modules.

Checks:

```bash
python scripts/inspect_alphafold3_api.py
python -c "import alphafold3; print(alphafold3.__file__)"
```

Likely causes and fixes:

- The active Python environment does not have AlphaFold 3 installed; install the package in the environment used by the agent or application.
- The package was installed without compiled extension modules; rebuild/reinstall according to the package's supported build path.
- The script is being run from a different Python executable than the one used for installation; run inspection with the same interpreter that runs the application.
- A local file or directory named `alphafold3` shadows the installed package; run from a neutral working directory or fix `PYTHONPATH`.

## Missing Generated CCD Pickles

Symptoms:

- `chemical_components.Ccd()` raises `FileNotFoundError` for `ccd.pickle`.
- Featurisation or structure utilities fail while loading chemical component data.
- The inspection script reports `ccd.pickle` or `chemical_component_sets.pickle` missing.

Cause:

AlphaFold 3 uses generated pickle resources under `alphafold3.constants.converters`. Some install paths require a post-install resource-generation step.

Recovery pattern:

1. Confirm the installed package resource directory is writable by the current user.
2. Confirm `libcifpp` data is available as `components.cif`.
3. If `components.cif` is in a non-standard location, set `LIBCIFPP_DATA_DIR` to the directory that contains it.
4. Run a small repair script only with explicit approval:

```python
from alphafold3 import build_data
build_data.build_data()
```

Do not run `build_data()` against read-only, system-managed, shared, or production package installs without approval. It writes generated files into installed package resources.

## Missing `libcifpp` `components.cif`

Symptom:

```text
Could not find components.cif. If libcifpp is installed in a non-standard location, please set the LIBCIFPP_DATA_DIR environment variable to the directory where libcifpp is installed.
```

Fixes:

- Install `libcifpp` data through the environment's supported package manager.
- Set `LIBCIFPP_DATA_DIR` to the directory containing `components.cif`, not to the file itself.
- Re-run resource generation only after confirming package resources are writable.

Related nuance: compiled DSSP/mmCIF helpers may also need `share/libcifpp/components.cif` to be discoverable. If CCD pickle generation succeeds but structure cleaning fails, check `libcifpp` data discovery again.

## Package-Data Issues

Symptoms:

- Package imports succeed but resource lookup through `importlib.resources` fails.
- `alphafold3.cpp.OUTPUT_TERMS_OF_USE.md` or constants resources are missing.
- Wheel or editable install behaves differently from the source tree.

Checks:

```python
from importlib import resources
import alphafold3.constants.converters as converters
print(resources.files(converters))
```

Fixes:

- Reinstall the package using the supported build backend so package data is included.
- Avoid relying on source-tree-relative files at runtime; package resources should be available through `importlib.resources`.
- For editable installs, verify generated files exist in the package resource subtree used by the active interpreter.

## JSON Parse API Errors

Common `Input.from_json` failures:

- Missing `dialect` or `version`.
- Unsupported dialect or version.
- Missing or empty `modelSeeds`.
- Missing sequence IDs, duplicate chain IDs, or lowercase/non-letter chain IDs.
- Bonded atom pairs with invalid chain IDs, residue IDs, or SMILES ligand atom references.
- Both `userCCD` and `userCCDPath` set.
- `userCCD` accidentally contains a path-like short string; use `userCCDPath` for paths.

Fix in the JSON authoring layer and route schema details to `../input-preparation/`.

## Accidental Full Inference

Symptoms:

- A supposedly harmless script starts loading model weights, compiling JAX, allocating GPU memory, or running for a long time.
- `ModelRunner.model_params`, `ModelRunner.run_inference`, or `process_fold_input(..., model_runner=runner, ...)` appears in a diagnostic script.

Safe alternatives:

- For parse-only checks, call `Input.from_json` and `Input.to_json` only.
- For data-pipeline-only runs, call `process_fold_input(..., model_runner=None, ...)`.
- For API inspection, use `scripts/inspect_alphafold3_api.py`; it never calls `run_inference`.
- Do not access `ModelRunner.model_params` unless the task is explicitly an inference task with model weights and device approval.

## JAX, GPU, and Flash Attention Issues

Symptoms:

- `jax.local_devices(backend='gpu')` fails or returns no devices.
- Inference raises GPU compute capability errors.
- For compute capability 7.x devices, errors mention `XLA_FLAGS` or `--flash_attention_implementation`.
- Flash attention implementation errors mention `triton`, `cudnn`, `xla`, `xla_chunked`, or `mosaic`.

Guidance:

- API inspection and JSON parsing do not require GPU; avoid importing or invoking runner paths that force accelerator work.
- `make_model_config()` accepts `flash_attention_implementation` values `mosaic`, `triton`, `cudnn`, `xla`, and `xla_chunked`.
- The runner script enforces special settings for some older GPUs; route command-line run recipes to `../running-predictions/`.
- Do not change model config defaults to work around hardware errors without understanding the target accelerator and JAX installation.

## Model Directory Issues

Symptoms:

- Model parameter loading fails after constructing or using `ModelRunner`.
- Errors mention missing parameter files, terms-of-use files, or invalid model directory contents.

Checks:

- Confirm the task is allowed to run inference and use model parameters.
- Confirm `model_dir` points to a directory containing the expected AlphaFold 3 model parameter files.
- Confirm the active user has read access.

Safe boundary: constructing `ModelRunner(config, device, model_dir)` stores values, but `model_params`, `_model`, and `run_inference()` trigger expensive or failure-prone model loading and execution.

## Data Pipeline Configuration Failures

Symptoms:

- `DataPipeline.process()` fails with missing binaries or database files.
- Sharded database paths or Z-values cause errors.
- Protein chains with only partially supplied MSA/template fields raise `ValueError`.

Guidance:

- `DataPipelineConfig` requires binary paths, database paths, and `max_template_date`.
- Sharded databases may require matching `*_z_value` values and complete shard paths.
- For protein chains, either provide all custom MSA/template fields or let AlphaFold 3 search for all missing fields.
- For RNA chains, setting `unpaired_msa` skips RNA MSA search; an empty string means use an empty MSA.

## Structure and mmCIF Failures

Symptoms:

- `structure.from_mmcif` fails on malformed or incomplete mmCIF.
- Bond parsing fails with `_struct_conn` references not present in `_atom_site`.
- Type-symbol inference fails when CCD data is unavailable.

Guidance:

- Parse mmCIF text first with `alphafold3.structure.mmcif.from_string` when debugging low-level CIF issues.
- Use `mmcif.get_bond_atom_indices(...)` to isolate bond-table failures.
- Use `chemical_components.Ccd()` only after confirming generated CCD resources exist.
- For non-CCD ligands, ensure chemical component metadata or user CCD data is available before converting to `Input` or `Structure`.

## `run_alphafold.py --help` Exits Nonzero

The runner can render flags while still exiting with code `1` in some inspection contexts. If help text is printed and flags are visible, record this as an entry-point nuance rather than proof that the package is broken. Validate actual imports and signatures separately with the bundled inspection script.
