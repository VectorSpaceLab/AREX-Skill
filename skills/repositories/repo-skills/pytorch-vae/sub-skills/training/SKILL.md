---
name: training
description: "Guides config-driven PyTorch-VAE training, dry-runs, data layout
  checks, and experiment troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training

Use this sub-skill when the user wants to run, dry-run, resume, or debug a PyTorch-VAE experiment from a YAML config.
It covers the generic runner pattern, CelebA-style data setup, logger/checkpoint output, and trainer knobs.
The bundled command examples assume the generated skill directory is the current working directory.

## Read first

- `references/workflows.md` for the end-to-end experiment flow.
- `references/configuration.md` for the config schema and model-specific fields.
- `references/troubleshooting.md` for data, trainer, and legacy-config failures.
- `scripts/train_from_config.py` for the bundled safe wrapper.

## Include here

- Choosing the right `configs/*.yaml` file for a model.
- Understanding `model_params`, `data_params`, `exp_params`, `trainer_params`, and `logging_params`.
- Verifying CelebA extraction paths and sample output locations.
- Dry-running a config before a full `fit`.
- Full training runs when the user explicitly wants them.
- Trainer settings that affect GPUs, checkpointing, logging, or seeds.
- Special training knobs such as FactorVAE's dual optimizer or legacy VampVAE config handling.

## Exclude or route elsewhere

- Constructor signatures, sample/generate behavior, and architecture selection -> `sub-skills/model-reference/SKILL.md`.
- Low-level architecture comparisons -> `references/model-overview.md` or model-reference.
- Repository provenance and staleness checks -> `references/repo-provenance.md`.

## Typical triggers

- "train VAE"
- "run this config"
- "why does the trainer fail"
- "where are logs/checkpoints saved"
- "how do I point it at CelebA"
- "why is `gpus` failing"
- "how do I dry-run the experiment before a long fit"

## Workflow

1. Pick the config that matches the target model family.
2. Confirm the data layout and `data_path`.
3. Run the bundled training wrapper without `--fit` for a safe validation pass.
4. Add `--fit` only after the config, data, and backend are ready.
5. Inspect logs under `logs/<experiment-name>/version_*` and checkpoints under the logger's `checkpoints/` directory.

## Hand off to model-reference when needed

If the user switches from "run the experiment" to "what arguments does the model take" or "what does `sample()` expect", route to the model-reference sub-skill.
