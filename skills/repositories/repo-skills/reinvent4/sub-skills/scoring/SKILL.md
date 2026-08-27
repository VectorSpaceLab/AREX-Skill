---
name: scoring
description: "Build and troubleshoot REINVENT4 scoring configurations,
  components, transforms, aggregation, and scoring plugins."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Scoring

Use this sub-skill when a task mentions `scoring.toml`, `run_type = "scoring"`, scoring components, transforms, aggregation, `comp_*` plugin files, `@add_tag`, `QED`, `MolecularWeight`, `TanimotoSimilarity`, `TanimotoDistance`, OpenEye ROCS, Chemprop, `ExternalProcess`, or REST scoring.

## Scope

This skill covers scoring-only jobs and scoring-function design that will later be reused by staged learning. For model sampling setup, use the sibling sampling skill. For transfer-learning or staged-learning orchestration, use the learning skill and return here only for `[scoring]` or `[stage.scoring]` blocks. For SMILES preprocessing, use the data-pipeline skill.

## Start Here

1. Use `run_type = "scoring"` for a standalone scoring run and provide a `[parameters]` block with `smiles_file` and optional `output_csv`.
2. Build a `[scoring]` block with `type = "geometric_mean"` or `type = "arithmetic_mean"`, optional `parallel`, optional `use_pumas`, and one or more `[[scoring.component]]` blocks.
3. Keep each component block in this shape: `[[scoring.component]]`, `[scoring.component.ComponentName]`, then one or more `[[scoring.component.ComponentName.endpoint]]` tables with `name`, optional `weight`, optional `params.*`, and optional `transform.*`.
4. Prefer a scoring-only run on representative SMILES before using the same scoring function in RL.

## References

- `references/components-and-plugins.md`: component block shapes, common built-ins, external components, and custom plugin discovery.
- `references/transforms-and-aggregation.md`: transform choice, endpoint weights, geometric/arithmetic aggregation, filters, and penalties.
- `references/troubleshooting.md`: config parsing, plugin import, optional dependency, external service, and transform-debugging failures.

## Bundled Helpers

- `scripts/validate_scoring_config.py`: parse a TOML scoring config and summarize scoring blocks, components, endpoints, params, transforms, and likely structural issues without running scoring.
- `scripts/list_scoring_components.py`: inspect installed `reinvent_plugins.components` namespace packages and list discovered `comp_*` modules/classes without executing a scoring job.

Run each helper with `--help` first. Both helpers are read-only; they inspect installed Python packages and config files but do not launch `reinvent`, score molecules, call external services, or load model checkpoints intentionally.

## Practical Defaults

- Use `QED` without a transform because it already returns a 0-1 value.
- Use `MolecularWeight` with `double_sigmoid` for a preferred mass window such as 200-500 Da.
- Use `TanimotoSimilarity` for new configs; treat `TanimotoDistance` as a backward-compatible deprecated alias.
- Use `custom_alerts` for must-fail SMARTS filters and do not rely on its `weight` for optimization.
- Use `geometric_mean` when every objective must remain acceptable; use `arithmetic_mean` when compensation between objectives is acceptable.
