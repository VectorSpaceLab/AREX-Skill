# Checkpoint Utilities

## When to read

Read this when a user wants to merge LoRA weights, reconstruct a delta checkpoint, consolidate a model, or extract projector weights.

## Utilities covered

### `scripts/merge_lora_weights.py`

Merges a LoRA adapter into a base model and saves the merged tokenizer and model.

Command shape:

```bash
python scripts/merge_lora_weights.py \
  --model-path <lora-adapter-path> \
  --model-base <base-model-path> \
  --save-model-path <output-dir>
```

### `python -m llava.model.apply_delta`

Applies a delta checkpoint to a base model.

Command shape:

```bash
python -m llava.model.apply_delta \
  --base-model-path <base-model-path> \
  --target-model-path <output-dir> \
  --delta-path <delta-or-target-path>
```

### `python -m llava.model.make_delta`

Computes a delta checkpoint from a base model and a target model.

Command shape:

```bash
python -m llava.model.make_delta \
  --base-model-path <base-model-path> \
  --target-model-path <target-model-path> \
  --delta-path <output-delta-dir>
```

### `python -m llava.model.consolidate`

Consolidates a checkpoint into a standard saved model directory.

Command shape:

```bash
python -m llava.model.consolidate \
  --src <source-dir> \
  --dst <destination-dir>
```

### `scripts/extract_mm_projector.py`

Extracts projector weights from a checkpoint that stores them in a larger shard set. Use this only if you understand why a projector-only extraction is needed.

## Common requirements

- Base and target model families must match.
- Large checkpoints need disk space and often GPU memory or long CPU load times.
- LoRA merge requires the correct `--model-base`.
- Delta utilities are not training substitutes; they are checkpoint conversion helpers.

## When to tell the user to stop

Stop and ask for more details when:

- the model family is unknown
- the adapter/base pair does not match
- the checkpoint was trained with incompatible prompt or projector settings
- the output directory would overwrite a useful existing model
