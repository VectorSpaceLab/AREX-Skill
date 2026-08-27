---
name: cli-and-inference
description: "Build safe Protenix prediction commands and debug CLI inference
  setup, model selection, output layout, cache/checkpoint expectations, and
  user-facing kernel choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Protenix CLI and Inference

Use this sub-skill when a user needs help with `protenix pred`, root CLI help, prediction model selection, inference flags, cache/checkpoint side effects, output locations, or command-shape diagnosis. It is designed for planning and debugging without launching expensive inference.

## Fast Triage

1. Confirm the installed command shape first: `protenix --help` and `protenix pred --help`. The verified console commands are `pred`, `json`, `msa`, `mt`, and `prep`.
2. For command planning, use the bundled no-run builder: `python sub-skills/cli-and-inference/scripts/build_protenix_pred_command.py --input input.json --out-dir output --print-warnings`. It prints a shell-quoted `protenix pred` command and never imports or runs Protenix.
3. Prefer explicit boolean values for `protenix pred`: use `--use_template true`, `--use_rna_msa false`, and similar value pairs rather than bare flags.
4. Start routine prediction commands from `--model_name protenix_base_default_v1.0.0 --use_default_params true` unless the user explicitly needs Protenix-v2, a 2025 cutoff model, or a mini/tiny smoke-test shape.
5. Set only user-provided data/cache roots at runtime. Do not invent checkpoint paths; Protenix derives the checkpoint directory from the runtime `PROTENIX_ROOT_DIR` environment variable and auto-downloads needed cache/checkpoint files when missing.
6. For CUDA/kernel failures, first build a no-run fallback command with `--trimul-kernel torch --triatt-kernel torch`; route deeper kernel installation, CUTLASS, cuEquivariance, or config surgery to `../advanced-model-configuration/SKILL.md`.

## References

- `references/cli-reference.md` covers root command registry facts, `pred` flag names, boolean handling, and no-run command construction.
- `references/model-selection.md` covers model capabilities, default parameters, seed behavior, dtype, TFG routing, cache/checkpoint expectations, and user-facing kernel choices.
- `references/output-layout.md` covers prediction output directories, sample/confidence file naming, atom-confidence output, and `ERR` behavior.
- `references/troubleshooting.md` covers missing CLI/version mismatches, accidental launches, missing caches/checkpoints, preprocessing dependencies, kernel errors, output surprises, and feature/model mismatches.

## Route Elsewhere

- Input JSON schemas, entity fields, ligands, constraints, `modelSeeds`, `templatesPath`, `rna_msa` fields, and example JSON interpretation belong to `../input-data-and-features/SKILL.md`.
- Protein MSA, template search, RNA MSA search, external databases, FASTA inputs, and preprocessing workflows belong to `../msa-template-and-prep/SKILL.md`.
- Training, finetuning, training data preparation, torchrun training, and dataset configs belong to `../training-and-data-pipeline/SKILL.md`.
- Deep kernel installation/debugging, model config internals, TFG internals, and backend performance tuning belong to `../advanced-model-configuration/SKILL.md`.
