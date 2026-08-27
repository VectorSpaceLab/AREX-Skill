# Sampling Workflows

Sampling is the fastest REINVENT4 run mode for inspecting what a prior, trained model, or checkpoint generates. It does not train the model and does not design a scoring function; it loads `model_file`, generates molecules, and writes a CSV with sampled SMILES, state, likelihood, and generator-specific identity columns.

## Workflow 1: Validate Before Running

1. Pick the intended generator mode from the model file and task: Reinvent, LibInvent, LinkInvent, Mol2Mol, or PepInvent.
2. Start with `device = "cpu"` and a small `num_smiles` for a portable smoke config.
3. Make `output_file` unique for the run, such as `sampling_linkinvent_smoke.csv`, to avoid overwriting previous results.
4. Add seed files only for seed-based modes.
5. Run the bundled static validator:
   ```bash
   python sub-skills/sampling/scripts/validate_sampling_config.py sampling.toml --model-mode Linkinvent --max-total-smiles 1000
   ```
6. Fix errors before launching `reinvent`.

The validator is intentionally no-run: it parses TOML/JSON/YAML, checks common key mistakes, validates seed-file existence and row shape, warns on CUDA-on-CPU hosts when it can inspect PyTorch, and estimates total generation count.

## Workflow 2: Reinvent De Novo Generation

Use Reinvent when the user wants unconstrained small-molecule generation from a prior or trained agent.

Checklist:

- `model_file` points to a Reinvent prior, trained model, checkpoint, or a valid registry key such as `.reinvent`.
- `smiles_file` is omitted unless intentionally using a supported inception/conditioning file with a compatible model.
- `num_smiles` is small for smoke tests, then increased for exploration.
- `unique_molecules = true` for final CSVs; temporarily use `false` only when diagnosing raw validity/diversity.

Command:

```bash
reinvent --device cpu --seed 7 --log-filename sampling_reinvent.log sampling_reinvent.toml
```

Expected CSV columns are `SMILES`, `SMILES_state`, and `NLL`.

## Workflow 3: LibInvent Scaffold Decoration

Use LibInvent when the user has scaffold cores and wants generated R-groups.

Seed file rules:

- One scaffold per non-comment line.
- Attachment points must be present; labels such as `[*:0]` and `[*:1]` are common.
- Keep the scaffold format consistent with the prior or agent used for sampling.

Minimal smoke plan:

1. Put 1-3 representative scaffolds in `scaffolds.smi`.
2. Set `num_smiles` to a small value such as 10-50 per scaffold.
3. Validate with `--model-mode Libinvent`.
4. Run on CPU first if GPU availability is unknown.

Expected CSV columns include `Scaffold` and `R-groups`.

## Workflow 4: LinkInvent Warhead Linking

Use LinkInvent when the user has two fragments and wants a generated linker.

Seed file rules:

- One warhead pair per non-comment line.
- Separate the two warheads with exactly one pipe character, `|`.
- Each warhead side should carry an attachment point, usually `*` or bracketed atom-map notation.

CPU-only correction pattern:

```toml
run_type = "sampling"
device = "cpu"

[parameters]
model_file = "priors/linkinvent.prior"
smiles_file = "warheads.smi"
output_file = "sampling_linkinvent_cpu.csv"
num_smiles = 25
unique_molecules = true
randomize_smiles = false
```

Validate first:

```bash
python sub-skills/sampling/scripts/validate_sampling_config.py sampling_linkinvent.toml --model-mode Linkinvent
```

Then run:

```bash
reinvent --device cpu --seed 123 --log-filename sampling_linkinvent.log sampling_linkinvent.toml
```

Expected CSV columns include `Warheads` and `Linker`.

## Workflow 5: Mol2Mol Analogue Generation

Use Mol2Mol when the user has input molecules and wants analogues similar to each input.

Seed file rules:

- One molecule per non-comment row.
- Optional labels in later columns are fine; REINVENT4 reads the first column for SMILES.
- `num_smiles` is per input molecule, so total requested outputs are approximately `num_smiles * seed_rows` before filtering.

Strategy selection:

- `sample_strategy = "multinomial"` for stochastic analogue exploration.
- `temperature < 1.0` for conservative outputs; `temperature > 1.0` for more randomness.
- `sample_strategy = "beamsearch"` for deterministic outputs; keep `num_smiles` modest because large beam sizes can be slow.
- Set `randomize_smiles = false` for transformer-based modes unless there is a specific reason to keep the config value for compatibility; REINVENT4 will force transformer randomization off internally.

Expected CSV columns include `Input_SMILES`, `Tanimoto`, and `NLL`.

## Workflow 6: PepInvent Sampling

Use PepInvent when the user has masked peptide/CHUCKLES-like input rows and wants fillers.

Seed file rules:

- One masked peptide input per non-comment row.
- Include mask markers such as `?`.
- Segment separators commonly use `|`.

Practical settings:

- Use `beamsearch` for deterministic mask filling.
- Keep `num_smiles` small until the input representation and prior are confirmed.
- Use `randomize_smiles = false`; transformer modes use canonical/isomeric handling internally.

Expected CSV columns include `Masked_input_peptide`, `Fillers`, and additional filler columns when REINVENT4 splits filler sequences.

## Workflow 7: Sample After Learning

Transfer learning and staged learning produce an adapted agent/checkpoint that can be sampled the same way as a prior.

1. Use the `learning` sub-skill to create or locate the output model.
2. Replace `model_file` in the sampling config with that trained model path.
3. Keep the same generator family as the trained model. For example, do not sample a LibInvent checkpoint with Mol2Mol seed-file assumptions.
4. Run a small `num_smiles` smoke sample before scaling.
5. Inspect valid/unique rates and mode-specific columns before using outputs downstream.

## Workflow 8: Scale Up Safely

For production-scale sampling:

- Increase `num_smiles` gradually after the smoke run passes.
- Estimate total generation as `num_smiles` for Reinvent or `num_smiles * seed_rows` for seed-based modes.
- Keep output paths unique and write logs with `--log-filename`.
- Prefer `--seed` for reproducible troubleshooting.
- Avoid large Mol2Mol beam-search runs unless the user explicitly accepts the runtime cost.
- Record the exact config and prior/agent provenance outside the generated CSV.

## Output Review Checklist

- Header matches the intended mode.
- Row count is plausible after uniqueness/filtering.
- `SMILES_state` is mostly valid for a healthy run.
- Seed-based identity columns map back to the intended seeds.
- `NLL` values are numeric.
- Mol2Mol `Tanimoto` values are present when expected.
- The output CSV did not overwrite an earlier run unintentionally.
