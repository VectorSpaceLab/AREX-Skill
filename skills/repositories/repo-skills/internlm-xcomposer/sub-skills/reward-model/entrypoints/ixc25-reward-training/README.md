# Bundled IXC-2.5-Reward Training Entrypoints

This directory packages the reward-model training entrypoints so reward SFT/preference training no longer depends on the original checkout.

## Contents

- `finetune.py` — reward training launcher using the custom `RewardTrainer`.
- `trainer.py` — source-derived reward trainer implementation.
- `data_mix.py` and `ixc_utils.py` — preference data loading and image preprocessing support.
- `ds_config_zero2.json` — DeepSpeed ZeRO-2 config from the reward training workflow.
- `launch_full.sh` and `launch_lora.sh` — self-contained torchrun wrappers.
- `merge_reward_lora.py` — source-README-derived PEFT adapter merge entrypoint for reward LoRA outputs.
- `data.txt`, `data/example.json`, and `data/example.png` — small source example fixture.

## Run gates

Running these launchers imports torch/Transformers/DeepSpeed/PEFT, loads an IXC-2.5-Reward checkpoint, and starts CUDA training. Validate preference data first and require explicit model/data/GPU/output approval.

## Examples

```bash
# Validate reward data from the reward-model sub-skill root.
python scripts/validate_reward_data.py entrypoints/ixc25-reward-training/data.txt --given-num --manifest-base manifest

# Real LoRA training after approval.
cd entrypoints/ixc25-reward-training
MODEL=/models/internlm-xcomposer2d5-7b-reward DATA=/data/reward_data.txt GPUS_PER_NODE=8 OUTPUT_DIR=/runs/ixc_reward_lora ./launch_lora.sh

# Merge the trained reward LoRA adapter after training.
python merge_reward_lora.py \
  --adapter-model-name /runs/ixc_reward_lora \
  --base-model-name /models/internlm-xcomposer2d5-7b-reward \
  --output-name /runs/ixc_reward_merged
```

For API scoring and ranking, use the sibling `references/api-reference.md`; this bundle is for training and reward-adapter merge entrypoints.
