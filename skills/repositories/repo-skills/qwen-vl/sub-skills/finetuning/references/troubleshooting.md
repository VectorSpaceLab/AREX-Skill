# Qwen-VL finetuning troubleshooting

## Version compatibility

- The prepared inspection environment verified `transformers==4.32.0` together with `peft==0.5.0`.
- Newer `peft` releases may expect newer `transformers` internals such as `Cache`, which breaks the source training script.
- If the training script fails during import, first check that the environment still uses the compatible pair above.

## CUDA / DeepSpeed warnings

- `deepspeed` can import even when `CUDA_HOME` is absent, but optional compiled CUDA extensions will be unavailable.
- If you need DeepSpeed CUDA ops, install a compatible CUDA toolkit and make sure `CUDA_HOME` points to it before trying to compile extensions.
- If a launch template fails immediately with an extension or kernel error, separate the pure import/CLI issue from the training runtime issue before changing the model or dataset.

## Data format errors

Symptoms:

- `KeyError` for `id` or `conversations`.
- Alternation errors between user and assistant turns.
- Grounding examples without both `<ref>` and `<box>`.
- Box coordinates outside the normalized `[0, 1000)` range.

Recovery:

1. Run `python scripts/validate_finetune_data.py --data ...`.
2. Confirm each sample has alternating turns.
3. Check that image markup uses `Picture n: <img>...</img>` and that multiple images are numbered consistently.

## Model / adapter mismatch

- If LoRA training on the base model behaves oddly, remember the source docs say the base model may need trainable embedding/output layers for new chat tokens.
- If Q-LoRA is launched with BF16, correct it to FP16 and an Int4-compatible checkpoint.
- If the user wants to resume from a LoRA adapter, use the inference sub-skill; do not silently merge the adapter unless the user explicitly wants a standalone merged checkpoint.

## Memory and batch sizing

- The official scripts are conservative, but they still assume a real GPU environment.
- If you hit OOM, reduce batch size, gradient accumulation, or sequence length before rewriting the whole workflow.
- Keep `--model_max_length` aligned with the actual data and memory budget.

## Common launch mistakes

- Pointing `--data_path` at a folder instead of the JSON file.
- Forgetting to replace `path_to_data` in the shell templates.
- Using a BF16 checkpoint with the Q-LoRA template.
- Expecting the source scripts to invent checkpoints or datasets automatically.
