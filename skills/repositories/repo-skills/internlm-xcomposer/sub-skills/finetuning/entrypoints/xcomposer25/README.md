# Bundled XComposer2.5 Finetuning Entrypoints

This directory is a self-contained, source-derived training bundle for current InternLM-XComposer2.5 supervised fine-tuning. It avoids any dependency on the original checkout while preserving the source entrypoint names and support modules.

## Contents

- `finetune.py` — Hugging Face Trainer entrypoint for full-parameter and LoRA SFT.
- `data_mix.py` and `ixc_utils.py` — data loader and image preprocessing support imported by `finetune.py`.
- `ds_config_zero2.json` — DeepSpeed ZeRO-2 config copied from the source workflow.
- `merge_peft_adapter.py` — PEFT adapter merge entrypoint.
- `launch_full.sh` and `launch_lora.sh` — wrappers that resolve this bundle directory, select the bundled DeepSpeed config, and then call `torchrun`.
- `data.txt` and `data/` — small source example manifest/files for format inspection. They are not a meaningful training dataset.

## Run gates

Running `launch_full.sh`, `launch_lora.sh`, or `merge_peft_adapter.py` loads model checkpoints, imports torch/Transformers/DeepSpeed/PEFT, and uses CUDA for realistic 7B training or merging. Validate data and confirm GPU/model/output paths before execution.

## Examples

```bash
# Validate data first from the sub-skill root.
python scripts/validate_finetune_data.py entrypoints/xcomposer25/data.txt --family 2.5

# Real LoRA launch after explicit approval. Override DATA/MODEL/OUTPUT_DIR for user data.
cd entrypoints/xcomposer25
MODEL=/models/internlm-xcomposer2d5-7b DATA=/data/my_data.txt GPUS_PER_NODE=8 OUTPUT_DIR=/runs/ixc_lora ./launch_lora.sh

# Merge a trained PEFT adapter into a standalone checkpoint.
python merge_peft_adapter.py \
  --adapter_model_name /runs/ixc_lora \
  --base_model_name /models/internlm-xcomposer2d5-7b \
  --output_name /runs/ixc_lora_merged
```
