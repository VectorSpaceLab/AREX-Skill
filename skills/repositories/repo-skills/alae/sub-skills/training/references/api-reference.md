# Training API reference

## Verified signatures

| Symbol | Signature | Notes |
| --- | --- | --- |
| `Model.__init__` | `Model.__init__(startf=32, maxf=256, layer_count=3, latent_size=128, mapping_layers=5, dlatent_avg_beta=None, truncation_psi=None, truncation_cutoff=None, style_mixing_prob=None, channels=3, generator="", encoder="", z_regression=False)` | Builds the mapping, encoder, decoder, and latent-average buffer. |
| `Model.generate` | `generate(self, lod, blend_factor, z=None, count=32, mixing=True, noise=True, return_styles=False, no_truncation=False)` | Returns generated images, or `(styles, rec)` when `return_styles=True`. |
| `Model.encode` | `encode(self, x, lod, blend_factor)` | Returns `Z[:, :1]` and discriminator prediction. |
| `launcher.run` | `run(fn, defaults, description='', default_config='configs/experiment.yaml', world_size=1, write_log=True, no_cuda=False)` | Adds `-c/--config-file`, appends `.yaml` when needed, and merges trailing YACS `opts`. |
| `TFRecordsDataset.__init__` | `__init__(self, cfg, logger, rank=0, world_size=1, buffer_size_mb=200, channels=3, seed=None, train=True, needs_labels=False)` | Chooses train/test path templates and asserts `PART_COUNT % world_size == 0`. |
| `Checkpointer.__init__` | `__init__(self, cfg, models, auxiliary=None, logger=None, save=True)` | Stores model and auxiliary state under `cfg.OUTPUT_DIR`. |
| `Checkpointer.load` | `load(self, ignore_last_checkpoint=False, file_name=None)` | Reads `OUTPUT_DIR/last_checkpoint`, loads with `strict=False`, and returns remaining checkpoint metadata. |
| `Checkpointer.save` | `save(self, _name, **kwargs)` | Writes `<OUTPUT_DIR>/<name>.pth` and updates `last_checkpoint`. |

## Loader behavior that matters

- `TFRecordsDataset.reset(lod, batch_size)` selects the resolution-specific shard list for `lod`.
- If `needs_labels=True`, each record must contain both `data` and `label`.
- `make_dataloader(...)` applies optional horizontal flips; `make_dataloader_y(...)` preserves labels.

## Important config keys

### Top level

- `NAME`: experiment label used by the config.
- `OUTPUT_DIR`: checkpoint, log, and sample root.
- `PPL_CELEBA_ADJUSTMENT`: metrics-only flag; ignore for training.

### `DATASET`

- `PATH`, `PATH_TEST`: TFRecord path templates formatted with `(resolution_level, part_index)`.
- `PART_COUNT`, `PART_COUNT_TEST`: shard counts for train and test.
- `SIZE`, `SIZE_TEST`: dataset sizes used by the loader and LOD driver.
- `FLIP_IMAGES`: whether the loader applies random horizontal flips.
- `SAMPLES_PATH`: sample-image folder used for saved grids.
- `STYLE_MIX_PATH`: sample-image folder used by figure workflows that share the config.
- `MAX_RESOLUTION_LEVEL`: highest progressive level expected by the shard layout.
- `FFHQ_SOURCE`: source TFRecord path for the FFHQ split workflow.

### `MODEL`

- `LAYER_COUNT`
- `START_CHANNEL_COUNT`
- `MAX_CHANNEL_COUNT`
- `LATENT_SPACE_SIZE`
- `DLATENT_AVG_BETA`
- `TRUNCATIOM_PSI`
- `TRUNCATIOM_CUTOFF`
- `STYLE_MIXING_PROB`
- `MAPPING_LAYERS`
- `CHANNELS`
- `GENERATOR`
- `ENCODER`
- `MAPPING_D`
- `MAPPING_F`
- `Z_REGRESSION`

### `TRAIN`

- `EPOCHS_PER_LOD`
- `BASE_LEARNING_RATE`
- `ADAM_BETA_0`
- `ADAM_BETA_1`
- `LEARNING_DECAY_RATE`
- `LEARNING_DECAY_STEPS`
- `TRAIN_EPOCHS`
- `LOD_2_BATCH_8GPU`
- `LOD_2_BATCH_4GPU`
- `LOD_2_BATCH_2GPU`
- `LOD_2_BATCH_1GPU`
- `SNAPSHOT_FREQ`
- `REPORT_FREQ`
- `LEARNING_RATES`

## Bundled presets in this checkout

- `configs/ffhq.yaml`
- `configs/celeba.yaml`
- `configs/celeba-hq256.yaml`
- `configs/bedroom.yaml`
- `configs/mnist.yaml`
- `configs/mnist_fc.yaml`
