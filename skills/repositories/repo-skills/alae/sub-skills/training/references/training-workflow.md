# Training workflow

## Repository organization facts

The README says every script must be run from the ALAE repository root. From a shell, set `PYTHONPATH` to that root before invoking subdirectory scripts. `train_alae.py` is the main training entry point; `launcher.py` merges config files and trailing `opts`, starts DDP, and forwards the resolved config into `train()`. `defaults.py` defines the base YACS tree, while `configs/*.yaml` provide dataset and schedule presets. The training stack is split across `dataloader.py`, `model.py`, `checkpointer.py`, `scheduler.py`, `lod_driver.py`, `tracker.py`, `custom_adam.py`, `lreq.py`, and `losses.py`.

The README also mentions ablation files such as `train_alae_separate.py`, `model_separate.py`, and `celeba_ablation_*.yaml`, but they are absent in this checkout. Do not route training requests there.

## Command patterns

Use one of these patterns from a checkout root:

```bash
cd <alae-repository-root>
export PYTHONPATH="$PYTHONPATH:$(pwd)"

python train_alae.py -c ffhq
python train_alae.py -c configs/celeba.yaml
python train_alae.py -c celeba TRAIN.TRAIN_EPOCHS 1
python train_alae.py -c ffhq MODEL.START_CHANNEL_COUNT 32
```

The `-c/--config-file` option accepts either a bare config name or a YAML path. If the value has no suffix, the launcher adds `.yaml`; if that file is not found, it also checks `configs/<name>.yaml`.

## YACS overrides

Anything after the config argument is merged with `cfg.merge_from_list(...)`.

- Use dotted keys such as `MODEL.LATENT_SPACE_SIZE 512`.
- Keep each override value as one shell token.
- Lists must be written as a single YACS list literal.
- Typos are not ignored.
- The source code spells the truncation fields `TRUNCATIOM_PSI` and `TRUNCATIOM_CUTOFF`; use those exact keys when overriding.

## GPU and world-size behavior

`train_alae.py` passes `torch.cuda.device_count()` into `launcher.run(...)`. The launcher spawns one process per visible GPU when more than one device is present and uses NCCL DDP. With one GPU it stays single-process.

Training-specific consequences:

- `TFRecordsDataset` asserts that `DATASET.PART_COUNT % world_size == 0`.
- Match the `LOD_2_BATCH_*GPU` table to the actual world size.
- Lower the per-GPU batch size if you hit memory pressure.
- The README recommends 8 GPUs; smaller world sizes may change reproducibility.

## Data prerequisites

- Training uses TFRecords via DareBlopy.
- `DATASET.PATH` and `DATASET.PATH_TEST` must match the shard naming pattern expected by `TFRecordsDataset`: the trainer formats them with `(resolution_level, part_index)`.
- `DATASET.SIZE`, `SIZE_TEST`, `PART_COUNT`, and `PART_COUNT_TEST` should agree with the actual shard counts.
- `DATASET.SAMPLES_PATH` is used for saved sample grids when present; if it is set to `no_path`, the trainer falls back to a batch from the loader.
- `OUTPUT_DIR` must be writable; checkpoints, logs, sample images, and the `last_checkpoint` pointer live there.

## Debug recommendations

1. Run the bundled helper from this training sub-skill directory, for example `python scripts/inspect_alae_config.py -c <config> --repo-root <alae-repository-root>`, before the trainer.
2. Start with a tiny override such as `TRAIN.TRAIN_EPOCHS 1` and a reduced batch schedule.
3. Check `OUTPUT_DIR/log.txt`, `log.csv`, `plot.png`, `sample_*.jpg`, and `last_checkpoint`.
4. If the dataset paths are site-specific, change them in config rather than patching the trainer.
5. Use the repository root or `PYTHONPATH` for every subdirectory script; otherwise imports fail.
