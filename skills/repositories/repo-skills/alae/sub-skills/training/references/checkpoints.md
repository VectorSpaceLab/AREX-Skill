# Checkpoints

## Where checkpoints live

`OUTPUT_DIR` is the root for checkpoints, logs, plots, and sample images. Training creates:

- `last_checkpoint`
- `model_tmp_intermediate_lod<N>.pth`
- `model_tmp_lod<N>.pth`
- `model_final.pth`
- `log.txt`, `log.csv`, `plot.png`, and `sample_<epoch>_<tick>.jpg`

## Save and load conventions

- `Checkpointer.save(name, **kwargs)` serializes `models` plus `auxiliary` state (`encoder_optimizer`, `decoder_optimizer`, `scheduler`, `tracker`) and writes `<OUTPUT_DIR>/<name>.pth`.
- `Checkpointer.tag_last_checkpoint(path)` writes the path string into `last_checkpoint`.
- `Checkpointer.load()` reads `last_checkpoint` automatically unless `ignore_last_checkpoint=True` or `file_name` is supplied.
- Resume is pointer-driven; there is no CLI flag for choosing a weight file.
- The final `model_final` save is awaited with `.wait()`, so let the process exit cleanly.

## Mismatch warnings

`Checkpointer.load()` calls `load_state_dict(..., strict=False)` for each model. That means:

- architecture changes can partially load without stopping;
- missing modules or renamed submodules produce warnings, not hard failures;
- changing `LAYER_COUNT`, `START_CHANNEL_COUNT`, `MAX_CHANNEL_COUNT`, `LATENT_SPACE_SIZE`, `MAPPING_LAYERS`, `GENERATOR`, `ENCODER`, or `Z_REGRESSION` can invalidate a checkpoint.

Always inspect the log after resume and compare the config to the `last_checkpoint` target.

## Practical resume rules

- Use one `OUTPUT_DIR` per experiment.
- If you want to resume from a specific weight file, update `last_checkpoint` to point at that `.pth`.
- The checkpoint dict also carries extra state, and the trainer merges it back into its `arguments` dict.
