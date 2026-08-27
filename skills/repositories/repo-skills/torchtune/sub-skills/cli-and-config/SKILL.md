---
name: cli-and-config
description: "Use torchtune's tune CLI, recipe registry, and OmegaConf config
  system safely without importing recipes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# cli-and-config

Use this sub-skill when an agent needs to discover torchtune recipes/configs, copy or inspect built-in YAML, validate config shape, build `tune run` commands, or explain torchtune's `_component_`/OmegaConf override behavior.

## Route Here For

- Listing, copying, catting, validating, downloading, or running through the `tune` CLI.
- Building `tune run [TORCHRUN-OPTIONS] <recipe> --config <config> [RECIPE-OPTIONS]` commands.
- Explaining config YAML fields, `_component_` dotpaths, interpolation, `key=value` overrides, and `~field` removals.
- Inspecting built-in recipes/configs without importing the intentionally non-importable `recipes` package.
- Diagnosing CLI/config failures before moving on to expensive training.

## Quick Workflow

1. Discover registry entries with `tune ls` or `python scripts/inspect_tune_registry.py --format table`.
2. Inspect a built-in config with `tune cat <config-name>` or copy it with `tune cp <config-name> ./my_config.yaml --make-parents`.
3. Make quick changes with recipe overrides after the `--config` value, using `key=value` and `~field` only.
4. Run the bundled shape checker before training: `python scripts/validate_config_shape.py ./my_config.yaml optimizer=bitsandbytes.optim.PagedAdamW8bit ~optimizer.fused`.
5. Use `tune validate ./my_config.yaml` when optional dependencies are present and component signature validation is desired.
6. Build execution commands with torchrun flags before the recipe and recipe/config overrides after `--config`.

## Read Next

- [CLI reference](references/cli-reference.md) for `tune download`, `tune ls`, `tune cp`, `tune cat`, `tune validate`, and `tune run` syntax.
- [Config reference](references/config-reference.md) for `config.parse`, `config.instantiate`, `_component_`, interpolation, overrides, and removals.
- [Troubleshooting](references/troubleshooting.md) for common CLI/config errors and safe fixes.
- [post-training-recipes](../post-training-recipes/SKILL.md) for choosing recipes and planning expensive runs.
- [data-and-datasets](../data-and-datasets/SKILL.md) for dataset field semantics and dataset-specific component choices.

## Bundled Helpers

- `scripts/inspect_tune_registry.py` prints recipe/config registry metadata without importing or executing recipe modules.
- `scripts/validate_config_shape.py` loads a local or registry config, applies torchtune-style overrides, checks `_component_` shape, and optionally resolves/imports components without launching training.

## Guardrails

- Do not `import recipes`; use `tune run`, `tune cp`, `tune cat`, registry names, or runpy behavior through the CLI.
- Do not place torchrun/distributed flags after the recipe name; they must appear before the recipe to affect torchrun.
- Do not use unknown `--flags` after `--config`; torchtune recipe overrides are `key=value` or `~field` tokens.
- Do not embed Hugging Face or Kaggle tokens in configs, commands, examples, or skill content.
- Keep dataset schemas, recipe selection depth, and model/module API catalogs in their sibling sub-skills.
