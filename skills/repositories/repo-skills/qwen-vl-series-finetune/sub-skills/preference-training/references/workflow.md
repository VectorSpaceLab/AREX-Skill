# Preference Training Workflow

## DPO

- Use paired `chosen` and `rejected` responses.
- If reasoning is enabled, keep `chosen_reasoning` and `rejected_reasoning` synchronized.
- The command builder should include `--beta`, `--dpo_loss`, and `--precompute_ref_log_probs` when relevant.

## GRPO

- Reward functions are discovered from `train.reward_funcs`.
- The repo’s GRPO trainer supports multimodal prompts and generation controls.
- Liger can be enabled, and the repo exposes `--liger_grpo_loss_type` for the supported loss variants.

## Shared choice points

- Use the data sub-skill first when the JSON schema is not yet trustworthy.
- Use the model-compatibility reference for reasoning support and Flash Attention 2 guidance.
- Prefer a dry-run command builder before launching training.
- The executable helper runs bundled `src/train/train_dpo.py` or `src/train/train_grpo.py` from the skill root with `PYTHONPATH=src`; it does not require the original checkout.

## Executable helper

```bash
python scripts/preference_command.py --help
python scripts/preference_command.py --mode dpo --model-id Qwen/Qwen2.5-VL-3B-Instruct --data-path data/dpo.json --image-folder data/images --output-dir outputs/dpo
python scripts/preference_command.py --mode grpo --model-id Qwen/Qwen2.5-VL-3B-Instruct --data-path data/grpo.json --image-folder data/images --output-dir outputs/grpo
# add --run only when the printed command should be executed
```

## Typical command ingredients

- `--model_id`
- `--data_path`
- `--image_folder`
- `--output_dir`
- `--deepspeed`
- `--enable_reasoning`
- `--disable_flash_attn2`
- `--use_liger_loss`
- `--beta`
- `--max_completion_length`
- `--max_prompt_length`
