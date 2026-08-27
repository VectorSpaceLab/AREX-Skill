---
name: learning
description: "Configure REINVENT4 transfer learning and staged reinforcement
  learning runs safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# REINVENT4 Learning

Use this sub-skill when the user asks for transfer learning, `transfer_learning.toml`, staged RL/curriculum learning, `staged_learning.toml`, diversity filters, inception memory, TensorBoard monitoring, or a TL-then-RL workflow.

## Route the request

- Use `run_type = "transfer_learning"` to bias a prior or checkpoint toward a curated SMILES set and write an `output_model_file` that can later be sampled or used as an RL `agent_file`.
- Use `run_type = "staged_learning"` for all reinforcement learning, including a single-stage RL run and multi-stage curriculum learning.
- For TL followed by RL, prepare and validate the TL config first, plan a brief sample/quality check of the TL model, then set the staged-learning `agent_file` to the chosen TL `.model` or checkpoint while keeping `prior_file` compatible with the same generator type.
- Cross-link to the scoring sub-skill for scoring component design, transforms, external scoring files, and scoring-only validation; this sub-skill only covers how scoring is embedded in staged learning.
- Cross-link to the sampling sub-skill when the user needs to sample from a prior, TL model, or RL checkpoint.
- Cross-link to the data-pipeline sub-skill when the training or seed SMILES file needs cleaning, splitting, column extraction, or standardization.

## Safe workflow

1. Identify the generator family from the model file and input shape: Reinvent uses one-column SMILES; Mol2Mol/Pepinvent usually need conditional input plus `sample_strategy`; LibInvent/LinkInvent use two-column fragment inputs.
2. Use CPU by default for dry-run validation and small examples; if the config says `device = "cuda:0"`, tell the user `reinvent --device cpu FILE` overrides the config for CPU fallback.
3. Validate config shape before any training: run `python sub-skills/learning/scripts/check_learning_config.py CONFIG` from the skill root or copy the script beside the planned config.
4. Never start long TL/RL training without explicit user approval for runtime, model files, input SMILES, scoring files, output locations, and device.
5. Prefer short exploratory settings first: small `num_epochs` for TL, conservative RL `max_steps`, and checkpoint files on every stage.

## Required config anchors

- TL config: top-level `run_type`, `device`, optional top-level `tb_logdir`, then `[parameters]` with `input_model_file`, `smiles_file`, `output_model_file`, `num_epochs`, `batch_size`, and usually `validation_smiles_file` plus `save_every_n_epochs`.
- Mol2Mol TL: include `[parameters.pairs]` or dotted `pairs.*` thresholds for Tanimoto pair construction.
- RL config: top-level `run_type`, `device`, optional top-level `tb_logdir`, `[parameters]`, `[learning_strategy]`, optional `[diversity_filter]`, optional `[inception]` or `[intrinsic_penalty]`, and one or more `[[stage]]` blocks.
- RL parameters: `prior_file`, `agent_file`, `summary_csv_prefix`, `batch_size`, optional `smiles_file` for conditional generators, and safe checkpoint/continuation settings (`use_checkpoint`, `purge_memories`).
- RL stages: each `[[stage]]` needs `max_steps`, `termination = "simple"`, `min_steps`, `max_score`, optional `chkpt_file`, and `[stage.scoring]` with inline components or `filename` plus `filetype` for bundled stage scoring files.

## Bundled guidance

- Read `references/tl-rl-workflows.md` for concrete TL, staged RL, diversity filter, inception, intrinsic penalty, and TL-then-RL patterns.
- Read `references/monitoring-and-outputs.md` for TensorBoard log layout, CSV columns, checkpoint behavior, and review criteria.
- Read `references/troubleshooting.md` for device fallback, missing model/input files, model type mismatch, scoring-file path errors, SMILES column issues, TensorBoard confusion, remote responder setup, and long-run safeguards.
- Run `scripts/check_learning_config.py` to statically parse TOML/JSON/YAML configs and report missing major sections or risky settings without importing REINVENT4 or starting training.
