# Batch Prediction Troubleshooting

## Optional Dependency Failures

Symptom:

```text
RuntimeError: alphafold is not installed. Please run pip install colabfold[alphafold]
```

Cause: the base package exposes the `colabfold_batch` entry point, but structure prediction requires the AlphaFold optional extra.

Recovery:

1. If the task is MSA-only or AF3 JSON export, use `--msa-only` or `--af3-json` and avoid prediction dependencies.
2. If structures are required, install the prediction extra: `pip install colabfold[alphafold]`.
3. Install a compatible `jax` build for the target backend. CUDA GPU jobs need a CUDA-compatible JAX wheel; CPU-only jobs can use CPU JAX but will be slow.
4. Re-run `colabfold_batch --help` and a tiny `--num-models 1` job before scaling.

## Missing or Unapproved Model Parameters

Symptom: parameter `.npz` files are missing under `DATA_DIR/params/`, or prediction begins by attempting a large download.

Cause: the CLI calls `download_alphafold_params(model_type, data_dir)` for any prediction with `num_models > 0`.

Recovery:

- Use `--msa-only` when the current step should not download parameters.
- Use `--data PARAM_DIR` to point to an existing parameter directory.
- Ask for approval before network downloads in constrained environments.
- Verify the model type matches available files; multimer v3 requires `params_model_<N>_multimer_v3.npz`, pTM requires `params_model_<N>_ptm.npz`.

## JAX, CUDA, and GPU Memory Failures

Symptoms include JAX backend errors, CUDA library errors, long compilation times, or log messages like `Could not predict ... Not Enough GPU memory?`.

Recovery:

- Start with `--num-models 1`, shorter inputs, and default recycles.
- Reduce MSA memory with `--max-msa max_seq:max_extra_seq`, `--max-seq`, or `--max-extra-seq`.
- Disable or lower expensive options such as multiple seeds, high recycles, templates, `--save-all`, and representation saving.
- Try `--disable-unified-memory` when TensorFlow/JAX unified-memory settings cause allocation issues.
- Use `--recompile-padding 0` for exact memory tests, or keep a small positive value to reduce repeated recompilation in batches.
- Use `--use-pallas true` only on compatible NVIDIA Ampere-or-newer setups with a matching JAX/Triton stack.

## Public MSA Server and Network Failures

Symptoms: MSA step hangs, server errors, HTTP failures, or policy concerns about public server use.

Recovery:

- Split the workflow: run `--msa-only`, inspect logs, then predict later.
- If public server use is not acceptable, prepare local A3M files with the MSA-search route and run `colabfold_batch msas/ predictions/`.
- Use `--msa-mode single_sequence` for a no-network baseline when biological quality trade-offs are acceptable.
- Use `--host-url` only when a trusted compatible MSA server is available.

## Input and Query Failures

Symptoms: unexpected complex/monomer route, unsafe job names, duplicate outputs, malformed AF3 JSON, or parser errors.

Recovery:

- Validate FASTA/CSV/A3M formatting with the input-format route before prediction.
- Use `--jobname-prefix` to avoid unsafe or duplicate header-derived names in large batches.
- For complexes, ensure chains are encoded as a single multichain query rather than unrelated separate monomer queries.
- For AF3 JSON export with ligands/nucleic acids, verify non-protein FASTA syntax before running; aromatic SMILES colons should be substituted according to the input-format guidance.

## Template Failures

Symptoms: `--custom-template-path` ignored, per-entry template errors, `local_pdb_path is not specified`, or no templates found.

Recovery:

- Always include `--templates` when using template-related flags.
- Do not combine `--custom-template-path` and `--pdb-hit-file`.
- For `--pdb-hit-file`, also provide `--local-pdb-path`.
- For CSV per-entry templates, provide `--custom-template-cache-path` and omit `--custom-template-path`.
- Check `log.txt` for `found templates` versus `found no templates`, and inspect `<jobname>_template_domain_names.json` when present.

## AF3 JSON Export Failures

Symptoms: no structures appear after `--af3-json`, or JSON generation fails during MSA/template preparation.

Recovery:

- This is expected: `--af3-json` returns before structure prediction.
- Inspect output JSON and A3M files, not PDB files.
- If MSA generation failed, troubleshoot MSA server/local A3M inputs first.
- If non-protein molecules are involved, route input syntax validation to the input-format sub-skill.

## Output and Resume Surprises

Symptoms: a rerun skips jobs, zip files are missing individual outputs, or expected plots/PAE JSON are absent.

Recovery:

- Existing `.done.txt` or `.result.zip` files cause skips; use `--overwrite-existing-results` to recompute.
- `--zip` deletes per-job result files after successful archive creation; inspect `<jobname>.result.zip`.
- `--skip-output plots` omits coverage/PAE/pLDDT PNGs.
- `--skip-output pae_json` omits AlphaFold-DB-style PAE JSON.
- `--skip-output msa` omits A3M output.

## API-Level Failures

When using `colabfold.batch.run(...)` directly:

- Pass parsed query tuples in the expected shape `(jobname, sequence_or_chain_list, a3m_lines, custom_template_path_or_molecules)`.
- Call `set_model_type(is_complex, model_type)` before reasoning about parameter files.
- Ensure `data_dir` points to available parameters before calling model-loading code.
- Prefer the CLI unless the caller has already validated inputs and owns dependency setup.
