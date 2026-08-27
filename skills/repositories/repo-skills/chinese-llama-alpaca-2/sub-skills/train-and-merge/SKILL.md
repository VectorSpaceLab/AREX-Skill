---
name: train-and-merge
description: "Routes Chinese-LLaMA-Alpaca-2 dataset prep, training, and LoRA
  merge workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# train-and-merge

Use this sub-skill for any workflow that prepares training data, runs pretraining or supervised fine-tuning, or merges LoRA adapters back into a full model.

## Use it when

- the user mentions `build_dataset.py`, `run_clm_pt_with_peft.py`, `run_clm_sft_with_peft.py`, `run_pt.sh`, or `run_sft.sh`
- the task is about JSON instruction data with `instruction`, `input`, and `output` fields
- the user needs DeepSpeed stage-2 configuration or PEFT/LoRA launch flags
- the task is merging Chinese-LLaMA/Alpaca LoRA weights into HF or PTH outputs

## Workflow

1. Read `references/workflows.md` for the accepted data schema and training flag map.
2. Check that the command is being run from `scripts/training/` so the bundled vendored `peft/` package is importable.
3. Validate the dataset or model-path assumptions before starting any expensive job.
4. Use the shell launchers for a quick example of the expected DeepSpeed and LoRA arguments.
5. Read `references/troubleshooting.md` if the run fails on imports, dataset layout, or adapter merging.

## Bundled runtime files

- `scripts/training/build_dataset.py`
- `scripts/training/run_clm_pt_with_peft.py`
- `scripts/training/run_clm_sft_with_peft.py`
- `scripts/training/run_pt.sh`
- `scripts/training/run_sft.sh`
- `scripts/training/ds_zero2_no_offload.json`
- `scripts/training/peft/`
- `scripts/training/build_dataset.py` also supplies the collator and dataset cache logic used by SFT
- `scripts/merge_llama2_with_chinese_lora_low_mem.py` for LoRA merge/export when a full checkpoint is needed

## What to read first

- `references/workflows.md` for the training data layout and command family
- `references/troubleshooting.md` for local `peft`, DeepSpeed, bitsandbytes, and dataset errors

## Routing notes

- Use this sub-skill before the inference sub-skill when a task needs a freshly trained or merged checkpoint.
- The fine-tuning scripts are intentionally adapter-heavy; do not replace them with a generic Hugging Face recipe unless the user explicitly asks for a rewrite.
- The vendored `peft/` package is part of this sub-skill's runtime surface, not a separate external repository.
