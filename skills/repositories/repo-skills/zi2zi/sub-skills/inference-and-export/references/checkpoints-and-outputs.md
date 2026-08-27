# Checkpoints and outputs

## Checkpoint contract

The original TensorFlow model expects a checkpoint directory that can be
resolved with `tf.train.get_checkpoint_state`. The directory normally contains:

- a `checkpoint` state file;
- one or more `unet.model-*` shard files;
- optional generator-export files if `export.py` has already been run.

Inference restores generator variables, not the full training graph state.
When the model directory contains a checkpoint from a different batch size or
embedding configuration, restore may fail because variable shapes or names no
longer match.

## Output naming

### Normal inference

- Files: `inferred_0000.png`, `inferred_0001.png`, ...
- Save directory: user-specified `--save_dir`
- Content: concatenated output grids from the generated fake glyphs

### Interpolation

- Files: `frame_<src>_<dst>_step_<idx>.png`
- Optional GIF: the file named by `--output_gif`
- The frames are generated after linearly overwriting embedding and conditional
  instance-normalization variables in the graph.

### Export

- Generator export writes a checkpoint with a generator model prefix.
- Exported variables include the style embedding table and generator weights.
- The export directory should be treated as a checkpoint root for future
  generator-only use.

## Interpreting output content

The generated PNGs are concatenated image grids. They are useful for visual
inspection of transfer quality, but not as a dataset format.

When validating a run, check:

- output files exist and are non-empty;
- the number of files matches the number of batches or interpolation steps;
- styles change in the expected direction as embedding IDs change;
- the image grid is not blank, collapsed, or the wrong size.

## Batch-size implications

The script constructs fixed-size batches and may pad source examples. If the
batch size differs from training, the model may still run for some checkpoints,
but restore or output quality can degrade. Treat a changed batch size as a
compatibility risk unless the checkpoint and graph were validated together.
