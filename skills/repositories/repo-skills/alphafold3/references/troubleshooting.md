# Cross-Cutting Troubleshooting

## Import or Package Install Fails

Symptoms:
- `ModuleNotFoundError: alphafold3`
- pybind extension import errors
- package metadata exists but imports fail

Likely causes:
- Python version below the package requirement.
- Package was not built with its compiled extensions.
- JAX, RDKit, Haiku, Tokamax, or NumPy dependencies are missing or incompatible.

Actions:
- Confirm Python `>=3.12` for this baseline.
- Install the package through its documented build path or container image, not by copying source files onto `PYTHONPATH`.
- Run `python scripts/check_install.py` from this skill to collect import/resource facts.
- If only input JSON validation is needed, use `sub-skills/input-preparation/scripts/validate_fold_input.py` in an environment where AlphaFold 3 imports.

## Generated CCD Resources Are Missing

Symptoms:
- `FileNotFoundError` for `alphafold3/constants/converters/ccd.pickle` or `chemical_component_sets.pickle`.
- Importing modules that touch `alphafold3.constants.chemical_component_sets` fails.

Likely causes:
- Package data generation did not run or generated files were not included.
- `components.cif` from `libcifpp` is unavailable.

Actions:
- Check whether `components.cif` exists in the installed environment.
- If the package exposes `alphafold3.build_data.build_data()` and package resources are writable, run it once as an environment repair step.
- Avoid writing generated resources into a source checkout unless the user explicitly wants a maintainer-style repair.

## Full Prediction Is Not a Safe Smoke Test

Symptoms:
- Requests to “just test AlphaFold3” would require downloading databases or running GPU inference.

Likely causes:
- Full prediction requires model parameters, genetic databases, HMMER tools, GPU/JAX, and large output space.

Actions:
- Prefer safe checks: package import, input JSON validation, command construction, runtime preflight, or output-tree summarization.
- Use `sub-skills/running-predictions/scripts/build_run_command.py` to print commands without running them.
- Use `sub-skills/running-predictions/scripts/check_runtime_requirements.py` to check paths and binaries without downloads.

## CLI Help Prints but Exits Nonzero

Symptoms:
- `python run_alphafold.py --help` displays flags but returns status `1`.

Likely causes:
- Abseil required-flag handling can still consider missing required flags an error after rendering help.

Actions:
- Treat the visible help text as useful when present.
- Do not treat this behavior alone as proof that the package is broken.
- For command planning, rely on `sub-skills/running-predictions/references/cli-reference.md` and the bundled command builder.

## Hardware or Backend Is Unsuitable

Symptoms:
- CUDA/JAX import or runtime errors.
- Very low ranking scores with obvious clashes on older GPUs.
- Flash attention implementation failures.

Likely causes:
- GPU compute capability or driver/runtime mismatch.
- Known CUDA capability 7.x numerical issue.
- Flash attention backend not supported on the current accelerator.

Actions:
- Prefer Ampere or newer NVIDIA GPUs for inference.
- For CUDA capability 7.x GPUs, set `XLA_FLAGS` to include `--xla_disable_hlo_passes=custom-kernel-fusion-rewriter` before inference.
- Try `--flash_attention_implementation=xla` as a portability fallback when Triton/cuDNN kernels are unsuitable, accepting a possible performance trade-off.

## Large Databases or Model Parameters Are Missing

Symptoms:
- MSA/template search fails with missing FASTA/mmCIF paths.
- Model loading fails under `--model_dir`.

Likely causes:
- Genetic databases were not downloaded or mounted.
- Model parameters were not obtained under the required terms.
- Database directory permissions prevent HMMER tools from reading/writing.

Actions:
- Confirm database paths before running data pipeline.
- Confirm model parameter directory before inference.
- Avoid placing full databases inside a source checkout or generated skill directory.
- See `sub-skills/running-predictions/references/setup-and-performance.md` for database and model setup planning.
