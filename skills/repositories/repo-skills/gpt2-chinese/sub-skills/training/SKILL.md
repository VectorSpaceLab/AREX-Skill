---
name: "training"
description: "Routes GPT2-Chinese corpus preprocessing, model training,
  checkpointing, and perplexity evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training

Use this sub-skill when the task is about training, fine-tuning, checkpointing, or perplexity evaluation in GPT2-Chinese.

## Read first

- `../references/workflows.md` for the end-to-end training and evaluation flow.
- `../references/cli-reference.md` for exact flags and defaults.
- `../references/data-formats.md` for the expected corpus and tokenized file shapes.
- `../references/model-overview.md` when choosing a config file or vocabulary bundle.
- `../references/troubleshooting.md` and this sub-skill's troubleshooting file for workflow-specific failures.
- `../../scripts/check_install.py` before the first training run.

## What belongs here

- Raw corpus preprocessing with `--raw`.
- `train.py` for the normal multi-article corpus path.
- `train_single.py` for one long source document or a single concatenated corpus.
- `eval.py` for perplexity estimation on a trained checkpoint.
- Checkpoint loading and continuation with `--pretrained_model`.
- TensorBoard logging and training-schedule options such as `--gradient_accumulation`, `--log_step`, `--stride`, and `--fp16`.

## What does not belong here

- Prompted text generation belongs in `sub-skills/generation/SKILL.md`.
- Tokenizer selection, vocabulary rebuilding, or BPE setup belongs in `sub-skills/tokenization/SKILL.md`.
- Generic Transformers questions belong in the broader model ecosystem, not this repo skill.

## How to route a training request

1. Match the corpus shape first.
   - JSON list of article strings: use `train.py`.
   - One long document: use `train_single.py`.
2. Match the config and vocab.
   - Use `config/model_config_test.json` for smoke checks.
   - Use `config/model_config_small.json` plus `cache/vocab_small.txt` for the usual compact run.
   - Keep `vocab_size` and `--tokenizer_path` aligned.
3. Decide whether to preprocess in the same run.
   - `--raw` tokenizes and shards the corpus before training.
   - If shards already exist, skip `--raw`.
4. Decide whether you are resuming from a checkpoint.
   - Pass `--pretrained_model` when you want to continue from `save_pretrained` output.
5. Keep the schedule options consistent.
   - `log_step` must divide `gradient_accumulation`.
   - `fp16` needs Apex and a matching CUDA stack.
6. For evaluation, create the output directory first if you want a persisted score file.

## Common decision points

- If the corpus is short and you only need a smoke check, use the test config and a tiny shard count.
- If you are training on a single long novel, prefer `train_single.py` over forcing `train.py` to split the text.
- If you need a perplexity number for a checkpoint, use `eval.py` after the checkpoint is saved.
- If the user is actually asking for generated samples, redirect to generation instead of training.

## Output expectations

- `output_dir/model_epochN/` after each epoch.
- `output_dir/final_model/` after the training loop completes.
- TensorBoard logs under the writer directory if configured.
- Tokenized shards under `tokenized_data_path` when `--raw` is used.
