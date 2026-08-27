# Bundled Runtime Source and Executable Workflows

This skill is self-contained for the selected repository workflows. It includes the repo Python source and launch configuration that the training, merge, and serving commands need at runtime.

## Bundled runtime tree

- `src/` contains the copied repo modules for datasets, model loading, losses, trainers, training entrypoints, adapter merge, and Gradio serving.
- `scripts/deepspeed/zero2.json`, `zero2_offload.json`, `zero3.json`, and `zero3_offload.json` are the bundled DeepSpeed configurations used by the command builders.
- `references/source-requirements.txt` and `references/source-environment.yaml` preserve the repository dependency/configuration files needed to recreate an install without reopening the original checkout.
- `references/source-LICENSE` preserves the source repository license for the bundled runtime source.
- `sub-skills/*/scripts/*_command.py` are executable workflow helpers. They derive the skill root from their own location, run from that root, and set `PYTHONPATH=src` so the bundled source imports `model`, `trainer`, `dataset`, `train`, and `utils` without depending on an external checkout.

## Training workflows

Use the sub-skill command builders first. Without `--run`, they print the exact command they would execute; with `--run`, they execute the bundled source from this skill tree.

```bash
# SFT / full finetuning / LoRA / vision LoRA / video SFT
python sub-skills/sft-training/scripts/sft_command.py \
  --variant lora \
  --model-id Qwen/Qwen2.5-VL-3B-Instruct \
  --data-path data/train.json \
  --image-folder data/images \
  --output-dir outputs/sft

# DPO or GRPO
python sub-skills/preference-training/scripts/preference_command.py \
  --mode dpo \
  --model-id Qwen/Qwen2.5-VL-3B-Instruct \
  --data-path data/dpo.json \
  --image-folder data/images \
  --output-dir outputs/dpo

# Classification
python sub-skills/classification-training/scripts/classification_command.py \
  --model-id Qwen/Qwen2.5-VL-3B-Instruct \
  --data-path data/cls_train.json \
  --image-folder data/images \
  --output-dir outputs/cls
```

The printed commands have the form:

```bash
cd <this-skill-root> && PYTHONPATH=src${PYTHONPATH:+:$PYTHONPATH} deepspeed src/train/train_sft.py --deepspeed scripts/deepspeed/zero3_offload.json ...
```

That `src/train/...` path is the bundled source inside this skill, not the original repository checkout.

## LoRA merge workflow

```bash
python sub-skills/serving-and-adapters/scripts/adapter_command.py merge \
  --model-path outputs/sft \
  --model-base Qwen/Qwen2.5-VL-3B-Instruct \
  --save-model-path outputs/merged \
  --safe-serialization
```

Add `--run` only after confirming the source adapter path, base model, and output directory. The helper executes `src/merge_lora_weights.py` from the bundled runtime tree.

## Gradio serving workflow

```bash
python sub-skills/serving-and-adapters/scripts/adapter_command.py gradio \
  --model-path outputs/merged \
  --device cuda \
  --disable-flash-attention
```

Add `--run` only after model weights are available and a network-facing Gradio process is desired. The helper executes the bundled `src.serve.app` module with `PYTHONPATH=src`.

## Direct execution fallback

If a future agent bypasses the helpers, it must still run from the skill root with the bundled source on `PYTHONPATH`:

```bash
cd <this-skill-root>
PYTHONPATH=src${PYTHONPATH:+:$PYTHONPATH} deepspeed src/train/train_sft.py --help
PYTHONPATH=src${PYTHONPATH:+:$PYTHONPATH} python src/merge_lora_weights.py --help
PYTHONPATH=src${PYTHONPATH:+:$PYTHONPATH} python -m src.serve.app --help
```

Do not rewrite these commands to point at a separate source checkout. If the bundled `src/` tree is missing or stale, refresh this repo skill before running training, merge, or serving workflows.
