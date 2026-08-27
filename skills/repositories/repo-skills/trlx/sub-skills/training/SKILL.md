---
name: training
description: "Training, configuration, data, checkpointing, PEFT, and sweep
  workflows for trlX Accelerate trainers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# trlX training

Use this sub-skill when the task is to train or configure trlX with the public `trlx.train` API and Hugging Face Accelerate trainers.

## Route here for

- Online RLHF or rejection fine-tuning with `reward_fn`, `prompts`, optional prompt metadata, `eval_prompts`, `metric_fn`, and `stop_sequences`.
- Offline ILQL from `samples` plus `rewards`, including causal and seq2seq prompt/output samples.
- SFT from `samples` without rewards, including prompt/completion dialogue samples for causal models.
- Editing or validating `TRLConfig` objects, defaults, YAML configs, trainer/method/pipeline combinations, PEFT, optimizer/scheduler names, logging, checkpointing, resume, and Ray Tune sweeps.
- Debugging data shape, tokenizer, Accelerate/DeepSpeed, CUDA, W&B, Ray, PEFT, bitsandbytes, and checkpoint issues specific to training.

## Route elsewhere

- NeMo, Megatron, Apex, NeMo checkpoint conversion, NeMo YAML configs, or NeMo inference/training: use the sibling NeMo sub-skill at `../nemo/SKILL.md`.
- Maintainer benchmark/report workflows based on long remote clones, W&B report generation, or full example benchmarking are excluded from runtime operation; treat them as maintainer-only evidence.
- General Gym or Stable-Baselines RL tasks are out of scope; trlX is for LLM post-training/RLHF workflows.
- Cross-cutting package install/import issues may also need the integrated root troubleshooting reference at `../../references/troubleshooting.md`.

## Start with these bundled references

- [Training workflows](references/workflows.md): recipes for PPO/RFT, ILQL/SFT, seq2seq/T5, PEFT, checkpointing, evaluation, sweeps, Accelerate/DeepSpeed launch patterns, and distilled example families.
- [API reference](references/api-reference.md): `trlx.train` argument modes, config classes, registries, data pipeline contracts, model wrappers, and optimizer/scheduler names.
- [Configuration guide](references/configuration.md): default/YAML config editing, `update` vs `evolve`, required sections, valid trainer/pipeline/method combinations, and Accelerate config notes.
- [Troubleshooting](references/troubleshooting.md): known failure modes for dependencies, Ray, W&B, CUDA/DeepSpeed, HF downloads/cache, tokenizers, data shapes, PEFT/8-bit, checkpoint/resume, and seq2seq/SFT limits.

## Safe helper

Use [scripts/inspect_training_config.py](scripts/inspect_training_config.py) to summarize a default or YAML config without launching training or downloading models:

```bash
python scripts/inspect_training_config.py --default ppo
python scripts/inspect_training_config.py --default ilql --json
python scripts/inspect_training_config.py --yaml path/to/config.yml
```

Resolve the script path relative to this `SKILL.md` before running it; the script itself does not rely on the current working directory.

## Minimal decision flow

1. Choose the training mode:
   - PPO/RFT online: `reward_fn` + `prompts`.
   - ILQL offline: `samples` + `rewards`.
   - SFT causal: `samples` only.
2. Choose a config path:
   - Start from `default_ppo_config()`, `default_ilql_config()`, or `default_sft_config()` when possible.
   - Use a full `TRLConfig` object or `TRLConfig.load_yaml(...)` for explicit YAML.
   - For RFT, construct `RFTConfig` with `AccelerateRFTTrainer` because no default RFT config factory is provided.
3. Validate the trainer/method/data match before running training.
4. For distributed runs, create or select an Accelerate YAML and launch the user script with `accelerate launch`; do not invoke NeMo workflows from this sub-skill.
5. For sweeps, ensure the training script exposes `main(hparams={})`, then use `python -m trlx.sweep` with a reviewed Ray search-space YAML.
