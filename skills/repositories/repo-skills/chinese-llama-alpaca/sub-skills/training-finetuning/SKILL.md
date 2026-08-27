---
name: training-finetuning
description: "Guide Chinese-LLaMA-Alpaca data validation, CLM pretraining, SFT,
  LoRA/PEFT parameters, DeepSpeed templates, and checkpoint handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Fine-Tuning Router

Use this sub-skill when a user wants to validate Chinese-LLaMA-Alpaca training data, plan continued CLM pretraining, plan supervised instruction fine-tuning, adapt LoRA/PEFT arguments, or understand checkpoints produced by the bundled training scripts. The commands below assume the current working directory is this sub-skill directory.

Do not launch long-running training unless the user has explicitly approved the model paths, training data, GPU/backend use, output directory policy, and cost/time budget. This repository releases LoRA adapters, not original full LLaMA weights. Chinese LLaMA workflows are base/continuation-oriented; Chinese Alpaca workflows are instruction/chat-oriented. Alpaca tokenizers differ from LLaMA tokenizers.

## Fast Route

1. **Validate the dataset shape first.** Use [`scripts/validate_training_data.py`](scripts/validate_training_data.py):
   - SFT JSON: `python scripts/validate_training_data.py --mode sft --input templates/instruction_sample.json`
   - PT text: `python scripts/validate_training_data.py --mode pt --input templates/pretrain_sample.txt`
   - Add `--max-records N` for a quick prefix check.
2. **Choose the workflow.** Use [`references/data-formats.md`](references/data-formats.md) for SFT/PT data contracts and [`references/training-workflows.md`](references/training-workflows.md) for command construction.
3. **Adapt the bundled templates, not source checkout files.** Start from [`templates/run_pt.sh`](templates/run_pt.sh), [`templates/run_sft.sh`](templates/run_sft.sh), and [`templates/ds_zero2_no_offload.json`](templates/ds_zero2_no_offload.json).
4. **Inspect exact script arguments when needed.** Use [`references/api-reference.md`](references/api-reference.md) for dataclasses, option names, LoRA parameters, `peft_path`, `resume_from_checkpoint`, `force_resize_embeddings`, and `SavePeftModelCallback` outputs.
5. **Handle failures conservatively.** Use [`references/troubleshooting.md`](references/troubleshooting.md) before changing data caches, tokenizers, DeepSpeed settings, or output directories.

## Bundled Runtime Files

- [`scripts/run_clm_pt_with_peft.py`](scripts/run_clm_pt_with_peft.py): copied CLM pretraining / continued-pretraining PEFT script.
- [`scripts/run_clm_sft_with_peft.py`](scripts/run_clm_sft_with_peft.py): copied supervised instruction fine-tuning PEFT script.
- [`scripts/build_dataset.py`](scripts/build_dataset.py): copied SFT prompt/tokenization and collator helper used by the SFT script.
- [`scripts/validate_training_data.py`](scripts/validate_training_data.py): safe schema/text validator with `--mode {sft,pt}`, `--input`, and optional `--max-records`.
- [`templates/instruction_sample.json`](templates/instruction_sample.json) and [`templates/pretrain_sample.txt`](templates/pretrain_sample.txt): tiny fixtures only; they are not training corpora.

## Scope Boundaries

- For tokenizer extension before training or merging a newly trained LoRA adapter after training, route to the sibling model-reconstruction guidance.
- For inference, chat, or API serving with the resulting model/adapters, route to the sibling inference-deployment guidance.
- The credential-bound prompt crawler from the source release is intentionally not bundled as a runnable script because it requires an OpenAI API key, network access, and paid/credentialed calls. Treat it as excluded evidence, not a runtime dependency.
