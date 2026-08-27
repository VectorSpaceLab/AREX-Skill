# Relaxation and output troubleshooting

This troubleshooting guide covers post-processing failures owned by this sub-skill: Amber/OpenMM relaxation, output files, score/plot interpretation, citations, extra pTM metrics, and safe validation.

## Optional dependency failures

Symptoms:

- `ModuleNotFoundError: No module named 'alphafold'` during `colabfold_relax` or `relax_me(...)`.
- OpenMM, PDBFixer, or AlphaFold relaxation imports fail only when relaxation starts.
- Plot helpers fail with missing `matplotlib` or display helpers fail with missing `py3Dmol`.

Likely causes:

- The environment has base ColabFold but not the optional prediction/relaxation extras.
- A CLI entry point exists, but runtime optional dependencies are absent.
- The task is being run in a search-only or lightweight inspection environment.

Actions:

- For pure validation, do not install heavy extras; use `scripts/inspect_colabfold_outputs.py` instead.
- For relaxation, use an environment with ColabFold AlphaFold/OpenMM extras installed.
- Keep plotting/display optional. If matplotlib or py3Dmol is absent, report missing visualization support and continue with JSON/PDB validation.
- Route broader installation/backend repair to the root skill or `../batch-prediction/SKILL.md` when prediction dependencies are also broken.

## OpenMM GPU/CUDA backend failures

Symptoms:

- `--use-gpu` or `--use-gpu-relax` fails while CPU relaxation works.
- OpenMM reports no CUDA platform, incompatible CUDA, or driver/platform load errors.
- Relaxation crashes on a machine where prediction GPU/JAX works, or vice versa.

Likely causes:

- OpenMM and JAX use different GPU stacks and can fail independently.
- Installed OpenMM CUDA variant does not match the host driver/runtime.
- `CUDA_VISIBLE_DEVICES` hides the intended GPU.
- The structure is large enough that GPU memory pressure exposes backend instability.

Actions:

- Retry relaxation on CPU first:
  ```bash
  colabfold_relax input.pdb relaxed.pdb --max-iterations 2000
  ```
- Use GPU relaxation only after confirming OpenMM, not just JAX, can see the GPU.
- Remove `--use-gpu`/`--use-gpu-relax` for portable workflows.
- If GPU speed is required, repair the OpenMM CUDA installation in the environment before changing ColabFold outputs.

## Long or stalled relaxation

Symptoms:

- Relaxation appears to run indefinitely.
- A large batch of PDBs takes far longer than prediction output inspection.
- CPU use is high and no files are emitted until each structure finishes.

Likely causes:

- `max_iterations=0` means unlimited AlphaFold-style relaxation.
- `--amber` with `--num-relax 0` during prediction can relax every model/seed.
- Large complexes and problematic structures are expensive to relax.

Actions:

- Prefer bounded relaxation:
  ```bash
  colabfold_relax input_dir relaxed_dir --max-iterations 2000 --max-outer-iterations 3
  ```
- Relax only the top-ranked structure unless the task explicitly requires all ranks.
- If using `colabfold_batch`, set `--num-relax 1` rather than relying on `--amber` defaults.
- Validate that input PDB files exist before starting a large relaxation batch.

## CLI input/output path failures

Symptoms:

- `colabfold_relax` writes one output file repeatedly or fails to create expected files.
- A directory input produces no outputs.
- A single PDB input is paired with a directory path that does not exist.

Likely causes:

- Directory mode only scans `*.pdb` in the top-level input directory.
- Standalone relaxation accepts PDB inputs, not mmCIF, score JSON, or result directories with only AF3 JSON.
- The output path semantics differ for file vs directory inputs.

Actions:

- For one PDB, pass an explicit output PDB path:
  ```bash
  colabfold_relax job_unrelaxed_rank_001_model.pdb job_relaxed_rank_001_model.pdb
  ```
- For many PDBs, create an output directory first if needed and pass directory-to-directory paths.
- Use the bundled inspector to list PDB candidates before relaxation.
- If only mmCIF files exist, convert or obtain PDB files before using `colabfold_relax`.

## Malformed or incomplete structure files

Symptoms:

- Relaxation fails while importing a PDB into AlphaFold protein objects.
- Display helpers open the wrong file or cannot find expected `relaxed_model_1`/`unrelaxed_model_1` names.
- Mixed output directories contain `.pdb`, `.cif`, `.json`, and `.png` but no ranked PDB files.

Likely causes:

- The directory contains templates or initial guesses, not prediction outputs.
- Structure files are truncated, empty, or not valid PDB text.
- Notebook display helpers expect older/simple names while batch outputs use ranked names.

Actions:

- Check file sizes and names with `inspect_colabfold_outputs.py`.
- Use ranked batch PDB names directly for external viewers instead of relying on notebook naming conventions.
- Treat mmCIF validation separately from PDB relaxation. Required mmCIF fields include `_entity_poly_seq.mon_id`; missing required fields are data issues.

## Missing PAE or pLDDT plots

Symptoms:

- Score JSON exists but `<job>_pae.png` or `<job>_plddt.png` is missing.
- PAE JSON is missing but score JSON contains `pae`.
- A directory has structures and scores but no PNGs.

Likely causes:

- Plot output was skipped.
- PAE JSON output was skipped while per-model score JSON still contains PAE.
- Matplotlib failed or was unavailable during plotting.
- The model/run did not produce PAE.

Actions:

- Inspect `config.json` for skipped output settings if present.
- Check score JSON for `pae` and `plddt` before declaring data absent.
- Regenerate plots only when plotting dependencies are available and the underlying score data exists.
- For validation-only tasks, report missing plots as warnings rather than failed predictions.

## Score JSON and metric failures

Symptoms:

- `json.JSONDecodeError` reading a score file.
- `pae` matrix is not square or does not match `plddt` length.
- `iptm` or extra pTM metrics are missing for a complex.
- Extra metric plot is missing.

Likely causes:

- A run was interrupted while writing JSON.
- The file is AF3 input JSON, config JSON, or PAE JSON rather than a `scores` JSON.
- The model type did not produce the metric.
- Extra pTM calculation was disabled, unavailable, or only meaningful for complexes.

Actions:

- Classify JSON by file name: `scores`, `predicted_aligned_error`, `config`, and AF3 input JSON have different schemas.
- Treat absent optional metrics as unavailable unless the run settings prove they were requested.
- For pairwise interface interpretation, require chain-aware complex outputs and `asym_id`-based metrics.
- If JSON is truncated or invalid, re-run or recover the prediction output rather than editing score files by hand.

## Citation failures

Symptoms:

- `cite.bibtex` is missing.
- Amber/OpenMM citation is absent even though the user expected relaxed outputs.
- Citation count differs between workflows.

Likely causes:

- The run failed before final citation writing.
- Relaxation was not enabled, so OpenMM citation was not selected.
- MSA, environmental database, template, and model options differ between runs.

Actions:

- Check whether relaxed PDBs exist before expecting the OpenMM citation.
- Reconstruct citation expectations from `config.json` only when settings are available.
- Do not invent database or template citations if the run evidence does not show those features were used.

## Workflow ownership failures

Symptoms:

- The user asks to fix FASTA/A3M/CSV syntax while inspecting outputs.
- The user asks to rerun prediction because a plot is missing.
- The user asks to set up local MMseqs2 databases from an output validation task.

Actions:

- Keep output validation and relaxation here.
- Route input syntax and PDB/mmCIF input preparation to `../inputs-and-formats/SKILL.md`.
- Route MSA server/local database workflows to `../msa-search/SKILL.md`.
- Route prediction reruns, model selection, and JAX/GPU prediction setup to `../batch-prediction/SKILL.md`.
