# Troubleshooting and recovery

Start with safe diagnostics:

```bash
python --version                 # must be 3.11+
clawbio --version
clawbio --help
clawbio list
# Run from the generated ClawBio skill root:
python sub-skills/core-runner/scripts/check_output_contract.py --help
```

When developing against a checkout, use the installed editable `clawbio`
command in that checkout rather than assuming that the generated skill contains
the checkout's source tree. The bundled output checker itself does not import
ClawBio and can run from any current working directory.

## Installation failures

- `clawbio: command not found`: use the Python environment where the package
  was installed, check `python -c "from importlib.metadata import version; print(version('clawbio'))"`,
  and reinstall with `python -m pip install clawbio`. With uv, use `uv run
  clawbio --version` or install the public tool in an isolated environment.
- Python version rejected: create a Python 3.11+ environment; the project
  metadata declares `requires-python = ">=3.11"`.
- Conda cannot solve the package: update the conda index/cache and use the
  documented `conda-forge`/`bioconda` channels as appropriate, or use pip/uv.
  Skill-specific heavy tools may need their own environment and are not fixed
  by reinstalling the core wheel.
- Installed wheel lists too few skills: this is expected relative to a full
  checkout. The wheel bundles a curated subset; use a checkout when the
  complete repository tree or development tests are required.

## Input and parser errors

- `No input provided...`: choose exactly one of `--demo`, `--input`, or a
  profile-backed invocation. A domain skill may also document a no-input mode.
- Auto-detection cannot identify a file: pass
  `--format 23andme|ancestry|myheritage|vcf` to `clawbio upload`, or use the
  explicit parser API. Supported raw formats have distinct headers; compressed
  `.gz` files are opened transparently.
- Empty or malformed VCF: the single-sample parser skips records without a
  usable GT field; matrix parsing can raise `No samples found in VCF header`,
  `No variants found in VCF`, or a GT-field error. Fix the source VCF rather
  than treating a partial profile as complete.
- Profile loads but a run cannot read data: inspect
  `metadata.input_file`, verify the source path and permissions, and recreate
  the profile if the raw file was moved. Loading JSON does not restore the raw
  genotype file.
- An API upload raises instead of returning a result: `upload_profile` exposes
  parser/file exceptions directly. Catch `OSError`, `ValueError`, or JSON/file
  errors at the caller and report the selected format/path.

## Output and profile collisions

- `OUTPUT_DIR_NOT_WRITABLE`: the requested output path is an existing regular
  file or cannot be created. Pick a new directory or fix permissions. Do not
  delete a user file automatically.
- Existing output contains old files: the runner allows existing directories,
  but skills differ in overwrite behavior. Use a timestamped empty directory
  for a clean run; compare `files` and checksums, not just the directory name.
- Profile ID already exists: upload saves to `profiles/<patient_id>.json` and
  may replace the old JSON. Preserve the old profile first or select a new
  patient ID. A profile's source checksum lets you detect whether the source
  changed.
- Full profile is partially successful: inspect `pipeline_summary.json` and
  each child directory. The chain is sequential but continues after a stage
  failure; aggregate `success` is false if any stage failed. Fix the failed
  stage and rerun to a new output path. Profile result accumulation is
  best-effort, so verify `skill_results` before relying on it.

## Dependency, timeout, and child failures

- Timeout: raise `timeout` in `run_skill(..., timeout=...)` or CLI
  `--timeout`; do not disable the timeout without an explicit runtime plan.
- Non-zero child exit: inspect returned `stderr` and `stdout`, then the child
  skill's own contract. The runner captures logs and returns the child's exit
  code; it does not classify biological correctness.
- Missing report/result: a zero exit does not promise both files. Check the
  selected skill's documented output contract and use the output checker to
  distinguish absent optional files from malformed required files.
- An extra flag had no effect: the runner filters `extra_args` against the
  per-skill allowlist and blocks `--input`, `--output`, and `--demo`. Use the
  exact allowed flag spelling from the selected skill's documentation.

## Replay and provenance failures

- `sha256sum -c` fails: check that the original inputs, external tools, and
  versions are available and that the output directory was fresh. A changed
  tool or nondeterministic timestamp can change files. Verify only the paths
  listed in `checksums.sha256`.
- Replay command points at an old checkout: inspect `commands.sh`; some shared
  portable bundles allow `CLAWBIO_ROOT=/new/checkout`, while direct commands
  may require manual path edits. Do not edit a checksum file to hide a mismatch.
- `conda-lock` cannot run: install `conda-lock` or use the suggested
  `environment.yml`; lock generation is optional and is not proof that the
  original run can be reproduced.
- RO-Crate unexpectedly contains sensitive material: remove raw data/secrets
  from the output before calling `write_ro_crate`; that helper packages every
  file below the output root.

## Safe escalation

If a failure remains, preserve the complete structured return dictionary, the
child stderr, the exact command mode, package version, input format, and a
sanitised output tree. Do not attach raw genomes or profile JSONs to a bug
report. Avoid running native tests/examples during sub-skill drafting; those
belong to whole-skill integration.
