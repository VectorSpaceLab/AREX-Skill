---
name: nemo
description: "Router for trlX's optional NVIDIA NeMo/Megatron backend: when to
  choose it, how configs and checkpoints fit together, and what remains
  unverified without NeMo/Apex."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# nemo

Use this sub-skill only when the task explicitly depends on the trlX NeMo / Megatron backend, `.nemo` checkpoints, or the trlX NeMo wrappers.

## Route here when the request mentions
- `NeMoPPOTrainer`, `NeMoILQLTrainer`, or `NeMoSFTTrainer`
- `PPOGPT`, `ILQLGPT`, or `SFTGPT`
- `default_nemo_20b_config`, `default_nemo_2b_config`, or `default_nemo_1_3b_config`
- NeMo YAMLs, tensor/pipeline parallel sizing, rank-sharded checkpoints, or LLaMA-to-NeMo conversion
- checkpoint loading, NeMo-style inference, or `pretrained_model` / `megatron_cfg` wiring
- the optional NeMo / Apex / Megatron backend and its install prerequisites

## Route elsewhere when the task is really about
- standard `trlx.train` PPO / ILQL / SFT / RFT on Accelerate, reward functions, samples/rewards, PEFT, data shapes, or Ray sweeps → `../training/SKILL.md`
- generic NeMo usage that is not tied to trlX wrappers or configs
- direct NeMo/Apex installation, large-model conversion, or distributed launch execution

## Backend status in this inspection
- CUDA torch smoke passed in the minimum env.
- NeMo / Apex / Megatron were not installed in that env.
- The installed trlX package registers the NeMo trainer names, but they resolve to dummy import-error stubs until NeMo is installed.
- Treat all NeMo guidance here as source-backed and intentionally unverified for the local backend.

## What this sub-skill provides
- `references/workflows.md` for setup, conversion, training, inference, and default selection.
- `references/configuration.md` for NeMo YAML shape and trlx-to-NeMo config mapping.
- `references/troubleshooting.md` for import, Apex/CUDA, parallelism, checkpoint, tokenizer, and memory failures.

## Provenance used to distill this guidance
Source evidence was read from the NeMo-related trainer/model files, NeMo defaults, and docs/examples in the repo, including `docs/source/installation.rst`, `docs/source/api.rst`, `trlx/models/README.md`, `examples/llama_nemo/README.md`, `trlx/data/default_configs.py`, `trlx/trainer/nemo_*.py`, `trlx/models/modeling_nemo_*.py`, and `configs/nemo_configs/*.yaml`.
