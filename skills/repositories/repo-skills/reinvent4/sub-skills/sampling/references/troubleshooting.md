# Sampling Troubleshooting

Use this guide for no-run diagnosis before invoking `reinvent` and for interpreting common sampling failures after a run.

## `model_file` Missing or Not Accessible

Symptoms:

- Runtime error similar to `model file ... is not accessible`.
- Static validator reports a missing local model file.

Fixes:

- Use an existing `.prior`, `.model`, or `.chkpt` path.
- If using a dot-prefixed prior registry key such as `.reinvent`, confirm the installed runtime has prior files available or that `REINVENT_PRIOR_BASE` is configured for that shell.
- Do not assume public prior models are bundled with a clean REINVENT4 package install.
- For trained agents, ensure the learning workflow wrote the model and that `model_file` points to that output, not to a log directory.

## Wrong Model Mode vs Seed File Shape

Symptoms:

- Many invalid or empty generated SMILES.
- Missing expected output columns such as `Warheads` or `Input_SMILES`.
- Runtime errors while reading seed rows.
- Validator warnings about seed row shape.

Fixes:

- Reinvent de novo: omit `smiles_file` for ordinary sampling.
- LibInvent: one scaffold per row and attachment points marked with `*` or labels like `[*:0]` and `[*:1]`.
- LinkInvent: exactly two warheads per row separated by one `|`; each side should carry an attachment point.
- Mol2Mol: one molecule per row; later tab/comma/space-delimited labels are metadata, not the sampled input.
- PepInvent: one masked peptide representation per row with masks such as `?` and segment separators such as `|`.
- Validate with the intended mode:
  ```bash
  python sub-skills/sampling/scripts/validate_sampling_config.py sampling.toml --model-mode Linkinvent
  ```

## CUDA Requested on a CPU-Only Host

Symptoms:

- PyTorch reports CUDA is unavailable.
- A config copied from examples uses `device = "cuda:0"` but the target machine has no GPU.

Fixes:

- Rewrite top-level `device = "cpu"` for portable validation and small smoke sampling.
- Or run with CLI override:
  ```bash
  reinvent --device cpu sampling.toml
  ```
- Keep `num_smiles` small for CPU smoke tests, especially for seed-based modes.
- Use the validator; when PyTorch is importable it warns if the config requests CUDA on a CPU-only host.

## Invalid Config Format

Symptoms:

- TOML/YAML/JSON parser errors before validation.
- The file extension does not match the actual format.

Fixes:

- Prefer TOML for hand-written REINVENT4 configs.
- Use `--config-format json` or `--config-format yaml` when the extension is missing or misleading.
- Confirm booleans use the right syntax for the chosen format (`true`/`false` in TOML/JSON, normal YAML booleans in YAML).
- Keep all sampling run-mode parameters under `[parameters]`; top-level `model_file` and `num_smiles` are ignored by the schema.

## Schema or Unknown-Key Errors

Symptoms:

- Validation rejects a key under `[parameters]`.
- A config copied from another run mode contains learning or scoring keys.

Fixes:

- For sampling, keep scoring components out of the config except the optional `[filter].smarts` blocklist.
- Use `output_file`, not scoring mode’s `output_csv`.
- Use `model_file`, not learning mode’s `prior_file`, `agent_file`, or `input_model_file`.
- Use `num_smiles`, not staged-learning `batch_size`.

## Output Path Collisions

Symptoms:

- An existing CSV is overwritten.
- Multiple runs write to the same `sampling.csv`.

Fixes:

- Name outputs by mode and intent, such as `sampling_linkinvent_cpu.csv`.
- Run the validator without `--allow-output-overwrite`; it warns when `output_file` already exists.
- Keep logs separate with `--log-filename`.
- When running parameter sweeps, include seed/mode/date labels in output names outside the config template.

## Generation Is Too Slow or Expensive

Symptoms:

- CPU run appears stalled.
- Mol2Mol beam search is slow.
- Seed-based run produces far more outputs than expected.

Fixes:

- Remember total requested outputs are `num_smiles * seed_rows` for LibInvent, LinkInvent, Mol2Mol, and PepInvent.
- Keep smoke tests to `num_smiles <= 10` and 1-3 seed rows.
- Avoid Mol2Mol `beamsearch` with large `num_smiles`; REINVENT4 warns when Mol2Mol beam search exceeds 300.
- Use `--max-total-smiles` in the validator to catch oversized runs before launch.
- Prefer `multinomial` with controlled `temperature` for exploratory transformer sampling.

## Low Validity or Low Diversity

Symptoms:

- `SMILES_state` has many invalid rows.
- The output collapses to a small number of structures.
- `unique_molecules = true` removes most rows.

Fixes:

- Confirm the model family matches the seed-file shape.
- Start from a known-good prior or a less-overtrained agent.
- For Mol2Mol, adjust `temperature` and strategy.
- Temporarily set `unique_molecules = false` only to inspect raw generation behavior, then restore it for final outputs.
- For property-guided diversity control, use staged learning with diversity filters through the `learning` sub-skill rather than trying to solve it in pure sampling.

## Transformer Randomization Warning

Symptoms:

- Logs say `randomize_smiles` was true but the model was not trained with randomized SMILES, so it is set to false.

Meaning and fix:

- Mol2Mol, PepInvent, and transformer LibInvent/LinkInvent modes use canonical/isomeric handling internally.
- Set `randomize_smiles = false` in transformer configs to avoid noisy warnings.
- For classical Reinvent, LibInvent, and LinkInvent, randomization can improve seed diversity when compatible with the model.

## `reinvent --help` Fails on Import

A verified inspection environment needed `scipy` installed before `reinvent --help` worked because an imported plotting utility uses `scipy.stats.gaussian_kde`. If a future environment fails during `reinvent --help` with a SciPy import error, install or repair the declared package dependencies before debugging the sampling config itself.

## Optional Prior Downloads Are Not Bundled

Public prior models are external assets. This skill provides config and validation guidance, not prior weights. If a user asks for `.prior` files, direct them to obtain the official public priors or use their organization’s trained model artifacts, then place those files where the sampling config can read them.

## Safe CPU-Only LinkInvent Rewrite Case

Original risky config shape:

```toml
run_type = "sampling"
device = "cuda:0"

[parameters]
model_file = "priors/linkinvent.prior"
smiles_file = "warheads.smi"
output_file = "sampling.csv"
num_smiles = 1000
unique_molecules = true
randomize_smiles = true
```

Safe validation rewrite:

```toml
run_type = "sampling"
device = "cpu"

[parameters]
model_file = "priors/linkinvent.prior"
smiles_file = "warheads.smi"
output_file = "sampling_linkinvent_cpu_smoke.csv"
num_smiles = 10
unique_molecules = true
randomize_smiles = false
```

Then run:

```bash
python sub-skills/sampling/scripts/validate_sampling_config.py sampling_linkinvent_cpu.toml --model-mode Linkinvent --max-total-smiles 100
```

Only launch `reinvent` after the validator reports no errors.
