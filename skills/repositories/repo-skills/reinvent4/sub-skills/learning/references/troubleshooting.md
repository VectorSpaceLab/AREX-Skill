# Learning Troubleshooting

Use this guide to diagnose transfer learning and staged RL configuration problems without starting long training runs.

## Static validation first

Run the bundled checker on every TL/RL config before training:

```bash
python sub-skills/learning/scripts/check_learning_config.py transfer_learning.toml
python sub-skills/learning/scripts/check_learning_config.py staged_learning.toml
```

The checker parses TOML, JSON, or YAML, verifies `run_type`, checks major TL/RL sections, validates referenced local model/input/scoring paths where possible, and warns about CUDA and long-run risks. It does not import REINVENT4 and does not run training.

## CUDA and device issues

Symptoms:

- Runtime fails because CUDA is unavailable.
- The config says `device = "cuda:0"` but the machine is CPU-only.
- Torch reports a device error before training starts.

Actions:

- Prefer `device = "cpu"` for static examples, smoke tests, and small validation.
- Use CLI override for fallback: `reinvent --device cpu CONFIG`.
- Only use `cuda:0` after confirming the installed Torch build, driver, and hardware are compatible.
- Avoid running full RL on CPU without user approval; it can be slow even when technically valid.

## Missing model files

Symptoms:

- TL cannot read `input_model_file`.
- RL cannot read `prior_file` or `agent_file`.
- TL-then-RL starts with a missing `agent_file` because TL was not run or the output path changed.

Actions:

- Validate path spelling and relative working directory.
- Keep priors, TL outputs, and checkpoints in separate names; never overwrite the original prior.
- For TL-then-RL, set RL `agent_file` to the selected TL `.model` or checkpoint and leave `prior_file` as the compatible original prior.
- If continuing RL, use the previous `chkpt_file` as `agent_file` and decide deliberately whether `use_checkpoint = true` should restore diversity filter state.

## TL model type mismatch

Symptoms:

- RL raises an error like inconsistent model types between prior and agent.
- A Reinvent prior is paired with a Mol2Mol TL output or transformer checkpoint.

Actions:

- Use the same generator family for `prior_file` and `agent_file` in staged learning.
- Keep Mol2Mol/LibInvent/LinkInvent/Pepinvent priors and checkpoints separate from standard Reinvent priors.
- If the user needs to change generator family, plan a new workflow rather than reusing incompatible TL output.

## Invalid or incompatible SMILES input

Symptoms:

- TL reports no valid SMILES read from `smiles_file`.
- Conditional RL generates invalid outputs or cannot parse seed inputs.
- LibInvent/LinkInvent training data appears to read the wrong columns.

Actions:

- For standard Reinvent TL, use one SMILES per line or first-column SMILES; extra IDs are ignored.
- Split train/validation before TL; REINVENT4 does not create a validation split automatically.
- For LibInvent/LinkInvent TL, provide the expected two fragment columns; TL only affects the learned R-group/linker part.
- For LibInvent RL, provide scaffold inputs with attachment points; for LinkInvent, provide warheads separated by `|`; for Mol2Mol/Pepinvent, provide one conditional input per line.
- Use the data-pipeline sub-skill when the user needs standardization, filtering, deduplication, or column extraction.

## Staged scoring file path errors

Symptoms:

- A stage with `[stage.scoring].filename` fails to load.
- Scoring works in one directory but fails in another.
- Stage 2 never starts because stage 1 scoring is impossible.

Actions:

- Make scoring filenames relative to the working directory used for `reinvent CONFIG`.
- Include `filetype = "toml"` or `filetype = "json"` when using external stage scoring files.
- Validate the scoring file separately with the scoring sub-skill or a scoring-only run on a small SMILES set before RL.
- Check component transforms: if a component is always zero, adjust raw value ranges, filter roles, or weights before RL.

## Diversity filter and stage behavior

Symptoms:

- Stage-specific diversity filter seems ignored.
- Molecules collapse to one scaffold or many duplicates.
- Later stages rediscover the same scaffold series unexpectedly.

Actions:

- A global `[diversity_filter]` overrides `[stage.diversity_filter]`; remove the global section to use per-stage filters.
- Lower `bucket_size` or raise `minscore` to penalize repeated high-scoring scaffolds earlier.
- For cross-stage memory, use `purge_memories = false`; to reset after each stage, use `purge_memories = true`.
- If diversity is still poor, reduce `sigma`, lower learning rate, increase scoring diversity pressure, or sample from an earlier checkpoint.

## Inception and intrinsic penalty issues

Symptoms:

- Inception has no effect or fails to read seed SMILES.
- Intrinsic penalty and diversity filter appear mutually confusing.

Actions:

- Inception seed SMILES must be valid for the prior vocabulary and file path.
- If no inception SMILES are read, REINVENT4 may populate inception from the first sampled batch; this is weaker guidance than curated seeds.
- Use inception primarily with Reinvent-style RL unless the user has checked generator-specific behavior.
- Do not configure global diversity filter and intrinsic penalty expecting both to operate; the global diversity filter takes precedence.

## TensorBoard logdir confusion

Symptoms:

- No event files appear under the expected directory.
- RL creates directories with suffixes, but the user opens only the base directory.

Actions:

- Put `tb_logdir` at the top level of the config, not inside `[parameters]`.
- For staged learning, open the parent/base path or specific suffixed directories such as `tb_RL_0`.
- For TL, open the configured TL directory directly.
- If `tensorboard` is not installed in the environment, inspect CSV/log output first or ask permission to install runtime extras.

## Remote responder and dotenv

Symptoms:

- Remote monitoring does not receive events.
- Components needing environment variables fail.

Actions:

- Use `--dotenv-filename FILE` with `reinvent` when scoring components or responder tokens require environment variables.
- Keep secrets out of public configs and skills.
- Confirm `[responder]` endpoint and frequency only after the user approves remote reporting.
- If remote monitoring fails but local TensorBoard/CSV works, continue locally and report responder as non-blocking unless the user requires it.

## Long-run safeguards

Before launching TL/RL, confirm:

- User approval for runtime, compute device, and expected cost.
- All model, SMILES, and stage scoring files exist.
- Output model, checkpoint, CSV, TensorBoard, and log filenames will not overwrite valuable artifacts.
- `max_steps`, `min_steps`, `max_score`, and `num_epochs` are bounded for the user’s experiment stage.
- CLI flags are explicit: `reinvent --device cpu --log-filename learning.log CONFIG` for a controlled CPU smoke run, or a confirmed CUDA command for production.

If `reinvent --help` fails before any run because `scipy` is missing, install SciPy in the REINVENT4 environment; the CLI imports plotting utilities that require `scipy.stats.gaussian_kde`.
