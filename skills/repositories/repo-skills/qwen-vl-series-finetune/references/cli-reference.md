# CLI Reference

This repo skill bundles the source entrypoints and configuration needed for the selected workflows. See `references/bundled-runtime.md` for the executable path contract.

## Bundled entrypoints

Run from the skill root with `PYTHONPATH=src`, or use the helper scripts that do that automatically.

| Bundled entrypoint | Purpose | Required runtime configuration |
| --- | --- | --- |
| `deepspeed src/train/train_sft.py` | SFT, full finetuning, LoRA, vision LoRA, and video finetuning | `--deepspeed scripts/deepspeed/<zero*.json>` plus model/data/output paths. |
| `deepspeed src/train/train_dpo.py` | DPO preference training | Same DeepSpeed config plus `--dpo_loss`, `--precompute_ref_log_probs`, and `--beta`. |
| `deepspeed src/train/train_grpo.py` | GRPO preference training | Same DeepSpeed config plus generation/reward controls such as `--num_generations`, `--max_completion_length`, `--use_liger_loss`, and `--liger_grpo_loss_type`. |
| `deepspeed src/train/train_cls.py` | Sequence classification | Same DeepSpeed config plus `--loss_type`, `--num_labels`, eval, early-stopping, and head-learning-rate flags. |
| `python src/merge_lora_weights.py` | Merge LoRA adapters into a base model | Requires `--model-path`, `--model-base`, and `--save-model-path`; optional `--safe-serialization`. |
| `python -m src.serve.app` | Gradio multimodal demo | Requires `--model-path` for merged or adapter-backed weights and optional device/quantization/generation controls. |

The helper scripts print commands in this shape:

```bash
cd <this-skill-root> && PYTHONPATH=src${PYTHONPATH:+:$PYTHONPATH} deepspeed src/train/train_sft.py --deepspeed scripts/deepspeed/zero3_offload.json ...
```

That `src/` directory and `scripts/deepspeed/` directory are bundled inside this skill.

## Executable helper scripts

- `sub-skills/sft-training/scripts/sft_command.py`: SFT, LoRA, vision-LoRA, and video-SFT command builder/executor.
- `sub-skills/preference-training/scripts/preference_command.py`: DPO and GRPO command builder/executor.
- `sub-skills/classification-training/scripts/classification_command.py`: classification command builder/executor.
- `sub-skills/serving-and-adapters/scripts/adapter_command.py`: LoRA merge and Gradio command builder/executor.

All helpers are dry-run by default. Add `--run` only after confirming that model weights, data, output directories, GPU availability, and network/service side effects are acceptable.

## Shared flags worth knowing

- `--model_id` / `--model-base` / `--model-path`: choose the base model, adapter checkpoint, or merged checkpoint.
- `--data_path`, `--eval_path`, `--image_folder`, `--eval_image_folder`: point to JSON data and media roots.
- `--image_min_pixels`, `--image_max_pixels`, `--video_min_pixels`, `--video_max_pixels`: control multimodal token budgets.
- `--image_resized_width`, `--image_resized_height`, `--video_resized_width`, `--video_resized_height`: override resolution.
- `--fps` and `--nframes` are mutually exclusive for video.
- `--enable_reasoning` is only for supported reasoning model families.
- `--disable_flash_attn2` is the documented SDPA fallback for Qwen3.5.
- `--tf32` is enabled in the repo launch recipes for training workflows.
- `--bits`, `--double_quant`, and `--quant_type` control 4-bit/8-bit QLoRA loading; do not combine QLoRA with trainable vision modules or Liger.

## SFT-specific flags

- `--freeze_llm`, `--freeze_vision_tower`, `--freeze_merger`
- `--lora_enable`, `--vision_lora`, `--use_dora`
- `--lora_rank`, `--lora_alpha`, `--lora_dropout`, `--lora_namespan_exclude`, `--num_lora_modules`, `--lora_bias`
- `--unfreeze_topk_llm`, `--unfreeze_topk_vision`
- `--vision_lr`, `--merger_lr`
- `--use_liger_kernel`
- `--eval_strategy`, `--generation_max_new_tokens` for generation-based validation

## Preference-training flags

- DPO: `--beta`, `--dpo_loss`, `--precompute_ref_log_probs`
- GRPO: `--temperature`, `--top_p`, `--top_k`, `--min_p`, `--max_completion_length`, `--max_prompt_length`, `--num_generations`, `--use_liger_loss`, `--liger_grpo_loss_type`
- Shared adapter flags: `--lora_enable`, `--vision_lora`, LoRA rank/alpha/dropout/exclusion settings

## Classification flags

- `--loss_type`
- `--focal_alpha`, `--focal_gamma`
- `--class_balanced_beta`
- `--num_labels`
- `--mlp_head_dim`, `--mlp_head_dropout`
- `--early_stopping_patience`, `--early_stopping_threshold`
- `--head_lr`, `--vision_lr`, `--merger_lr`

## Serving flags

- `--device`
- `--load-8bit`, `--load-4bit`
- `--disable_flash_attention`
- `--temperature`, `--repetition-penalty`, `--max-new-tokens`
