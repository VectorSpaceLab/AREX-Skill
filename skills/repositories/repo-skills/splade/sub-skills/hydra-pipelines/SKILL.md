---
name: hydra-pipelines
description: "Construct, debug, and explain classic SPLADE Hydra workflows for
  train/index/retrieve/evaluate/flops/export without opening the source
  repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SPLADE Hydra Pipelines

Use this sub-skill when a user needs the original SPLADE Hydra entry points: `python -m splade.all`, `python -m splade.train`, `python -m splade.index`, `python -m splade.retrieve`, `python -m splade.evaluate`, `python -m splade.flops`, or `python -m splade.create_anserini`.

## Start Here

1. Choose exactly one config source:
   - `SPLADE_CONFIG_NAME=<name-or-yaml>` for a config bundled with the installed SPLADE package's `conf/` tree.
   - `SPLADE_CONFIG_FULLPATH=/path/to/config.yaml` for a saved experiment config, usually from a previous `config.checkpoint_dir`.
2. Decide whether the command needs a trained checkpoint config:
   - `splade.train` creates `config.checkpoint_dir/config.yaml`.
   - `splade.index`, `splade.retrieve`, `splade.flops`, and `splade.create_anserini` normally load `config.checkpoint_dir/config.yaml`.
   - For Hugging Face model-only evaluation, add `config.pretrained_no_yamlconfig=true` and set `init_dict.model_type_or_dir=<hf-model-or-local-model-dir>`.
3. Fill required output directories before running any workflow based on `config_default`: `config.checkpoint_dir=...`, `config.index_dir=...`, and `config.out_dir=...`.
4. Use Hydra package overrides for config groups, such as `train/data=msmarco`, `index=msmarco`, or `retrieve_evaluate=toy`; use package-position paths for parameters, such as `init_dict.model_type_or_dir=...` or `config.top_k=1000`.

## Common Tasks

- Generate safe command templates with `scripts/splade_hydra_command_builder.py`; it validates required arguments and prints commands without running SPLADE.
- Follow `references/hydra-workflows.md` for toy, training, indexing, retrieval, evaluation, FLOPS, pretrained-model, and create-Anserini command shapes.
- Follow `references/configuration.md` for config names, saved config paths, group overrides, output directories, and post-training config flow.
- Follow `references/troubleshooting.md` for unresolved `???`, config-source conflicts, Hydra override mistakes, `version_base` dependency drift, `pytrec_eval`, CPU/GPU, and model-download failures.

## Boundaries

- For Hugging Face Trainer training, multiple negatives, reranking commands, or `splade.hf_train`, use `../hf-training-reranking/SKILL.md`.
- For SPLADE model classes, datasets, data schemas, and inverted-index APIs, use `../model-data-api/SKILL.md`.
- For Anserini/PISA/BEIR/static pruning depth, use `../pruning-export-evaluation/SKILL.md`; this sub-skill only covers `splade.create_anserini` as the handoff command.
