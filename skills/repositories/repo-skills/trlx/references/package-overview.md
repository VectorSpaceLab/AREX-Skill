# trlX package overview

## Purpose

trlX is a Python framework for fine-tuning language models with RLHF-style objectives. It exposes one public training entrypoint, `trlx.train`, and selects behavior from a `TRLConfig` made of train/model/tokenizer/optimizer/scheduler/method sections.

## Public surface at this snapshot

- Distribution: `trlx`, version `0.7.0`.
- Public import: `import trlx`.
- Main entrypoint: `trlx.train(...)`.
- Core algorithm configs: `PPOConfig`, `ILQLConfig`, `SFTConfig`, `RFTConfig`.
- Default factories: `default_ppo_config()`, `default_ilql_config()`, `default_sft_config()`, plus NeMo default config loaders.
- Normal backend: Hugging Face Accelerate with optional DeepSpeed through Accelerate configs.
- Optional backend: NVIDIA NeMo/Megatron with Apex for larger model-parallel training and checkpoint flows.
- Pipeline registry: `PromptPipeline` for prompts and evaluation prompts.
- Training utilities: logging controls under `trlx.logging`, optimizer/scheduler registries, checkpoint save/load helpers, PEFT-aware wrappers, Ray Tune sweep module.

## Training modes

| Mode | Main arguments | Typical config | Owning sub-skill |
| --- | --- | --- | --- |
| PPO online RLHF | `reward_fn`, `prompts`, optional `eval_prompts`, `metric_fn`, `stop_sequences` | `default_ppo_config()` / `AcceleratePPOTrainer` | `sub-skills/training/` |
| RFT online rejection fine-tuning | `reward_fn`, `prompts`, optional eval/metric callbacks | Explicit `RFTConfig` / `AccelerateRFTTrainer` | `sub-skills/training/` |
| ILQL offline RL | `samples`, `rewards`, optional eval/metric callbacks | `default_ilql_config()` / `AccelerateILQLTrainer` | `sub-skills/training/` |
| Causal SFT | `samples`, optional eval/metric callbacks | `default_sft_config()` / `AccelerateSFTTrainer` | `sub-skills/training/` |
| NeMo PPO/ILQL/SFT | Same conceptual data modes plus `trainer_kwargs.megatron_cfg` / `pretrained_model` | NeMo default YAMLs / NeMo trainers | `sub-skills/nemo/` |

## Install shape

Use a Python 3.9-3.11 environment. For the full 0.7.0-era runtime, the source requirements pin Accelerate, transformers, datasets, deepspeed, Ray, W&B, PEFT, and `torch==2.0.1+cu118`. Adapt the PyTorch wheel to the host GPU/driver if needed.

Public-install pattern:

```bash
python -m pip install torch --extra-index-url https://download.pytorch.org/whl/cu118
python -m pip install "trlx @ git+https://github.com/CarperAI/trlx.git"
```

Current-checkout pattern:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

If a modern packaging stack conflicts with the pinned 2023 dependencies, use the troubleshooting reference before downgrading or upgrading broad dependency sets.

## Safe inspection helpers

- Root helper: `scripts/check_trlx_install.py` checks importability, version metadata, train signature, registries, defaults, and optional CUDA availability.
- Training helper: `sub-skills/training/scripts/inspect_training_config.py` loads a default or YAML `TRLConfig` and summarizes it without launching training.

Both helpers are safe parser/import/config checks. They do not download models, load datasets, start Ray, launch Accelerate, or run native examples.

## Route selection

Choose `sub-skills/training/` for almost every task about the main `trlx.train` API, data shapes, configs, Accelerate/DeepSpeed, PEFT, checkpoints, logging, and sweeps.

Choose `sub-skills/nemo/` only when the user explicitly names NeMo/Megatron/Apex, `.nemo` checkpoints, rank-sharded checkpoint directories, or NeMo trainer/model class names.

If the user is contributing to the repository source rather than using trlX as a package, keep this skill's package behavior in mind but also apply normal Python repository maintenance practices.
