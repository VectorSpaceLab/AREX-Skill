---
name: data-and-rewards
description: "Prepare and validate verl post-training parquet data, reward-model
  metadata, and custom reward functions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data and Rewards

Use this sub-skill when the user needs to prepare, inspect, or debug verl post-training datasets and rewards before launching PPO-style training.

## Route Here For

- Creating or reviewing parquet rows with `data_source`, chat-template `prompt`, `ability`, `reward_model`, and `extra_info` fields.
- Validating one parquet file before wiring it into `data.train_files` or `data.val_files`.
- Aligning `reward_model.ground_truth` extraction with built-in or custom reward functions.
- Setting `custom_reward_function.path` and `custom_reward_function.name` for a Python reward module.
- Debugging prompt schema, multimodal placeholders, missing reward metadata, or reward-manager score failures.

## Bundled References

- Read `references/data-formats.md` for parquet row schemas, chat prompts, multimodal columns, and dataset-loader behavior.
- Read `references/reward-functions.md` for built-in reward dispatch, custom reward signatures, return values, and config keys.
- Read `references/troubleshooting.md` for common schema/reward failures and targeted fixes.

## Bundled Script

- Run `python scripts/validate_verl_parquet.py --help` for usage.
- Run `python scripts/validate_verl_parquet.py path/to/train.parquet --style-rule-requires-ground-truth --max-rows 200` to inspect schema without importing verl.
- Use `--json-output report.json` when a future agent needs machine-readable validation results.

## Working Pattern

1. Confirm every row has a dataset identifier in `data_source` and chat messages under the configured prompt key, usually `prompt`.
2. Confirm rule-based rows carry `reward_model.style == "rule"` and `reward_model.ground_truth` in the exact format expected by the reward function.
3. Keep reproducibility metadata such as `split`, `index`, raw question, raw answer, tool settings, and interaction settings under `extra_info`.
4. Validate a small sample with the bundled script before changing training configs.
5. For custom rewards, make the reward module importable by path and expose either `compute_score` or the configured function name.

## Boundaries

- This sub-skill does not own full PPO launch commands, rollout engine selection, installation, or cluster setup.
- Treat repo examples as schema evidence only; do not require future agents to call network-backed preprocessing scripts at runtime.
