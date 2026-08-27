# Inference and export troubleshooting

## `fail to restore model`

Likely causes:

- `--model_dir` points at the wrong directory.
- The checkpoint state file is missing.
- Batch size, embedding count, or normalization mode does not match the training
  run.
- Only some of the checkpoint shards were copied.

Recovery: inspect the checkpoint directory, verify the exact model id, and use
matching hyperparameters.

## `embedding_ids` errors

Likely causes:

- The IDs are not integers.
- The list has only one ID while `--interpolate=1` was requested.
- The IDs do not correspond to styles the checkpoint learned.

Recovery: use comma-separated integers and confirm the labels exist in the
training data and checkpoint.

## Output directory stays empty

Likely causes:

- The source object file is empty or unreadable.
- The model restore failed before generation began.
- The save directory path was wrong or unwritable.

Recovery: inspect `source_obj` with the data-preparation helper, verify the
checkpoint first, and ensure the output directory exists.

## GIF compilation fails

Likely causes:

- No frame PNGs were generated.
- `imageio` is missing or incompatible.
- The frame directory does not contain `frame_*.png` files.

Recovery: generate a few frames first, confirm `imageio` is installed, and run
the inference command without GIF compilation before enabling it.

## Unexpected style mixing or collapse

Likely causes:

- The checkpoint was trained with different labels than the ones requested.
- The source object file does not match the checkpoint's training distribution.
- The batch size or `inst_norm` setting differs from the training run.

Recovery: confirm the style IDs, restore hyperparameters, and compare generated
frames for one style at a time before attempting a larger interpolation chain.

## Export output looks incomplete

`export.py` only saves generator variables. That is expected. If you need the
full training state, keep the original checkpoint directory as well.
