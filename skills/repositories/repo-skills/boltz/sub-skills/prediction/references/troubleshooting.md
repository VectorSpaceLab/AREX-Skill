# Prediction Troubleshooting

## Preflight First

Before launching a prediction, run:

```bash
python sub-skills/prediction/scripts/boltz_input_validator.py INPUT --use-msa-server --check-auth
```

Use `--no-use-msa-server` when custom MSA files are expected. The validator avoids Boltz imports and model downloads.

## Missing MSA

Signal:

```text
Missing MSA's in input and --use_msa_server flag not set.
```

Fix:

- Add `--use_msa_server` if the user wants server-generated MSAs.
- Or provide `msa: path/to/file.a3m` / `msa: path/to/file.csv` for every protein target.
- Or set `msa: empty` for deliberate single-sequence mode.

Avoid mixing custom MSA paths with omitted/auto MSA fields in one YAML target.

## Invalid Input Directory or Suffix

Signals:

```text
Found directory ... instead of .fasta or .yaml.
Unable to parse filetype ..., please provide a .fasta or .yaml file.
```

Fix:

- Pass a single input file, or a clean directory containing only `.yaml`, `.yml`, `.fasta`, `.fa`, or `.fas` files.
- Move MSA files, templates, outputs, logs, notebooks, and nested folders outside the batch input directory.

## `BOLTZ_CACHE` Must Be Absolute

Signal:

```text
BOLTZ_CACHE must be an absolute path
```

Fix:

```bash
export BOLTZ_CACHE=/absolute/path/to/boltz-cache
boltz predict input.yaml --use_msa_server
```

Or avoid the environment variable and pass `--cache /absolute/path/to/boltz-cache`.

## Conflicting MSA Authentication

Signal:

```text
Cannot use both basic authentication ... and API key authentication ...
```

Fix:

- Use basic auth with `BOLTZ_MSA_USERNAME` and `BOLTZ_MSA_PASSWORD`.
- Or use API-key auth with `MSA_API_KEY_VALUE` plus `--api_key_header` when needed.
- Do not set both methods in environment variables or CLI flags.

Prefer environment variables for secret values; avoid putting passwords or API keys in shell history.

## MSA Server Network or Credential Failure

Signals can include HTTP errors, unauthorized responses, server timeouts, or empty MSA output.

Fix:

- Confirm `--use_msa_server` is present.
- Confirm `--msa_server_url` is reachable and matches the expected API.
- Confirm the chosen auth method and header name.
- Retry with a smaller target or custom MSA files if the server is rate-limited or unavailable.

## Old CUDA or cuEquivariance Kernel Failure

Signals may mention `cuequivariance`, specialized kernels, triangular updates, unsupported GPU architecture, or kernel compilation/import failures.

Fix:

```bash
boltz predict input.yaml --out_dir predictions --use_msa_server --no_kernels
```

If GPU execution is still broken, use CPU for a small smoke run:

```bash
boltz predict input.yaml --out_dir predictions --use_msa_server --accelerator cpu
```

CPU is much slower and is not a substitute for a production GPU run.

## Large Downloads or Offline Machines

Signals include long stalls while downloading CCD/molecule data, `boltz2_conf.ckpt`, `boltz2_aff.ckpt`, or network errors.

Fix:

- Pre-create an absolute cache directory and reuse it with `--cache`.
- Run a small validation command with the bundled validator before model launch.
- For offline machines, stage cache files and checkpoints before prediction.
- Use `--checkpoint` and `--affinity_checkpoint` only when the paths match the selected Boltz model family.

## Stale Outputs and Skipped Predictions

Signal:

```text
Found some existing predictions ..., skipping ... set the --override flag.
```

Fix:

```bash
boltz predict input.yaml --out_dir predictions --use_msa_server --override
```

Use `--override` when changing YAML content, FASTA content, MSA files, templates, constraints, model version, sampling settings, or output format with the same input stem and output directory.

## Affinity Binder Problems

Signals can include errors about Boltz-2 requirements, missing binder, non-ligand binder, multiple affinity ligands, multi-copy ligand binder, or ligand size.

Fix:

- Use `--model boltz2`.
- Ensure `properties: [{affinity: {binder: L}}]` points to a ligand chain ID.
- Use one single-copy ligand as binder.
- Keep the ligand within the small-molecule regime; very large ligands are unsupported or unreliable.
- Interpret `affinity_probability_binary` for binder-vs-decoy triage and `affinity_pred_value` for related active-ligand optimization.

## FASTA Limitations

Signals include missing features that cannot be expressed in FASTA.

Fix: convert to YAML when the input needs any of:

- Modified residues.
- Covalent bonds.
- Pocket/contact constraints.
- Templates with explicit mapping.
- Affinity prediction.

## Constraint or Template Mismatch

Signals include parse errors around atom names, residue indices, chain IDs, max distances, template files, or template chain mapping.

Fix:

- Check chain IDs after expanding list IDs.
- Use 1-based residue indices.
- Confirm ligand atom names match the ligand/CCD representation.
- Keep pocket/contact `max_distance` between 4 Å and 20 Å.
- Ensure `force: true` template entries include `threshold`.
- Ensure template file paths exist relative to the run location or YAML file location.
