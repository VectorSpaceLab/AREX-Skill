# ALAE configuration reference

## When to read

Read this when choosing a config, overriding YACS options, interpreting output paths, or diagnosing config/data/checkpoint mismatches.

## Config loading contract

Most runnable scripts call the shared launcher and accept a config through `-c` / `--config-file` plus trailing YACS overrides:

```bash
python train_alae.py -c ffhq
python train_alae.py -c configs/ffhq.yaml TRAIN.TRAIN_EPOCHS 1
python style_mixing/stylemix.py -c celeba-hq256
```

If the config argument has no extension, the launcher appends `.yaml` and searches `configs/`. The default config for most ALAE generation/training scripts is `configs/ffhq.yaml`.

## Available configs in this checkout

| Config | Main use | Important paths |
| --- | --- | --- |
| `ffhq` | FFHQ 1024x1024 StyleALAE training/generation/demo | `OUTPUT_DIR: training_artifacts/ffhq`, `SAMPLES_PATH: dataset_samples/faces/realign1024x1024`, `STYLE_MIX_PATH: style_mixing/test_images/set_ffhq` |
| `celeba` | CelebA 128x128 training/generation | `OUTPUT_DIR: training_artifacts/celeba`, `SAMPLES_PATH: dataset_samples/faces/realign128x128`, `STYLE_MIX_PATH: style_mixing/test_images/set_celeba` |
| `celeba-hq256` | CelebA-HQ 256x256 workflow | `OUTPUT_DIR: training_artifacts/celeba-hq256`, samples reuse `dataset_samples/faces/realign1024x1024` |
| `bedroom` | LSUN bedroom 256x256 workflow | `OUTPUT_DIR: training_artifacts/bedroom`, samples `dataset_samples/bedroom256x256`; no bundled `style_mixing/test_images/set_bedroom` was found |
| `mnist` | MNIST Style architecture training/debugging | `OUTPUT_DIR: mnist_results`, 1-channel model settings |
| `mnist_fc` | Fully connected/permutation-invariant MNIST variant | `OUTPUT_DIR: mnist_results_fc2z_2`, 1-channel FC generator/encoder settings |

The README mentions `celeba_ablation_*.yaml`, `train_alae_separate.py`, and `model_separate.py`, but those files are absent in this checkout. Do not build routes that depend on them.

## Key config sections

### Top level

- `NAME`: used in many output subdirectories, e.g. `make_figures/output/<NAME>/` and `style_mixing/output/<NAME>/`.
- `OUTPUT_DIR`: checkpoint/log/sample output directory. Model-loading scripts read `OUTPUT_DIR/last_checkpoint`.
- `PPL_CELEBA_ADJUSTMENT`: changes face crop behavior in `metrics/ppl.py` for CelebA-style tightly cropped faces.

### `DATASET`

- `PATH`: train TFRecord pattern, usually containing both resolution and part placeholders, e.g. `.../ffhq-r%02d.tfrecords.%03d`.
- `PATH_TEST`: test TFRecord pattern for reconstruction metrics.
- `FFHQ_SOURCE`: source StyleGAN TFRecord pattern for splitting FFHQ.
- `PART_COUNT` / `PART_COUNT_TEST`: number of train/test TFRecord parts. `TFRecordsDataset` asserts `PART_COUNT % world_size == 0`.
- `SIZE` / `SIZE_TEST`: expected train/test image counts.
- `SAMPLES_PATH`: sample images used by reconstruction/demo/figure scripts.
- `STYLE_MIX_PATH`: folder with `src/` and `dst/` image sets for `style_mixing/stylemix.py`.
- `MAX_RESOLUTION_LEVEL`: log2 maximum resolution. Figure scripts often use `2 ** (MODEL.LAYER_COUNT + 1)` for image size.

Many source configs use `/data/datasets/...` defaults. Override those paths or create deliberate symlinks for a new machine.

### `MODEL`

- `LAYER_COUNT`, `START_CHANNEL_COUNT`, `MAX_CHANNEL_COUNT`, `LATENT_SPACE_SIZE`, and `MAPPING_LAYERS` define model shape and checkpoint compatibility.
- `GENERATOR` and `ENCODER` select registered classes from `net.py` such as `GeneratorDefault`, `EncoderDefault`, `GeneratorFC`, and `EncoderFC`.
- `TRUNCATIOM_PSI` and `TRUNCATIOM_CUTOFF` (source spelling) control truncation in generation scripts.
- `Z_REGRESSION` changes the autoencoder loss target in `train_alae.py`.

Changing model-shape fields after training can cause checkpoint load warnings or ineffective outputs even though `Checkpointer.load()` uses non-strict state loading.

### `TRAIN`

- `TRAIN_EPOCHS`: full training length.
- `EPOCHS_PER_LOD`: progressive-growing schedule.
- `LOD_2_BATCH_1GPU`, `LOD_2_BATCH_2GPU`, `LOD_2_BATCH_4GPU`, `LOD_2_BATCH_8GPU`: batch schedules selected by `LODDriver` according to world size.
- `BASE_LEARNING_RATE`, `LEARNING_RATES`, `LEARNING_DECAY_STEPS`, `LEARNING_DECAY_RATE`: optimizer/scheduler settings.
- `SNAPSHOT_FREQ` and `REPORT_FREQ`: checkpoint and sample-report cadence per resolution stage.

## Validation helpers

- Use `sub-skills/training/scripts/inspect_alae_config.py` to summarize a config and print a training command skeleton.
- Use `sub-skills/data-preparation/scripts/validate_alae_data_layout.py` to check data/sample/style/checkpoint path readiness.
- Use `sub-skills/generation/scripts/check_generation_assets.py` for generation-specific checkpoint/sample/style/direction readiness.
