---
name: "sft-training"
description: "Plan Qwen-VL SFT, LoRA, vision LoRA, video finetuning, and
  DeepSpeed launch commands."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SFT Training

Use this sub-skill for full finetuning, LoRA/QLoRA, vision LoRA, video finetuning, evaluation during training, and DeepSpeed launch planning.

## Covers

- `train_sft.py` command planning.
- Full finetuning and LoRA variants.
- Vision LoRA and top-k unfreezing.
- Video training and media-resolution choices.
- Generation-based evaluation during SFT.
- ZeRO-2 / ZeRO-3 / offload template selection.
- Checkpointing and save behavior.

## Excludes

- DPO or GRPO preference training.
- Classification training.
- Adapter merge or serving.
- Dataset schema design beyond what SFT needs.

## Read first

- `../../references/workflow-map.md` for route confirmation.
- `../../references/cli-reference.md` for the shared flag surface.
- `../../references/model-compatibility.md` for Qwen family and backend caveats.
- `../../references/troubleshooting.md` for common SFT failures.
- `scripts/sft_command.py` for a safe command builder.
- `../../scripts/deepspeed/zero2.json` and friends for ZeRO templates.

## Typical user requests

- "Give me the exact SFT command."
- "How do I finetune with LoRA or vision LoRA?"
- "How do I train on videos?"
- "Should I use ZeRO-2 or ZeRO-3?"
- "Why is my Qwen3.5 SFT unstable with Flash Attention 2?"

## Workflow

1. Confirm the model family and dataset shape.
2. Decide whether the run is full finetuning, LoRA, or vision LoRA.
3. Decide whether the data contains video and needs video pixel controls.
4. Pick ZeRO-2, ZeRO-3, or an offload template based on memory pressure.
5. Check reasoning and Flash Attention rules for the chosen model family.
6. Emit the command with the bundled command builder.

## Decision rules

- Use `--disable_flash_attn2 True` for Qwen3.5 unless the user explicitly needs another path.
- Do not combine QLoRA with trainable vision-tower knobs.
- For dense Qwen3-VL full finetuning, consider ZeRO-2 and/or turning off Liger if memory or speed is a problem.
- For video, keep `fps` and `nframes` exclusive.
- If the user needs evaluation during training, make sure the eval dataset uses the same schema and media root assumptions.

## Safe command builder

Start with dry-run output from the bundled helper:

```bash
python scripts/sft_command.py --help
python scripts/sft_command.py --variant lora --model-id Qwen/Qwen2.5-VL-3B-Instruct --data-path data/train.json --image-folder data/images --output-dir outputs/sft
```

## If you need more detail

Read `references/workflow.md` for launch patterns and `references/troubleshooting.md` for memory, backend, and config failures.
