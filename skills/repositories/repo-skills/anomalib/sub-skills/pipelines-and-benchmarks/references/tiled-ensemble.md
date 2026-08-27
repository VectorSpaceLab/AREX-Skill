# Tiled Ensemble Reference

Tiled ensemble divides each input image into tile locations and trains one anomaly model per tile location. It is useful for high-resolution industrial inspection when a full image does not fit comfortably in memory. The feature is explicitly experimental: validate config shape and paths first, and require user approval before expensive execution.

## Public entrypoints

Use the installed package entrypoints rather than source-checkout helper scripts:

```python
from pathlib import Path
from anomalib.pipelines.tiled_ensemble import EvalTiledEnsemble, TrainTiledEnsemble

train = TrainTiledEnsemble()
train_args = train.get_parser().parse_args(["--config", "ensemble.yaml"])
train.run(train_args)

# Evaluate the exact run that training created.
eval_pipeline = EvalTiledEnsemble(root_dir=train.root_dir)
eval_pipeline.run(train_args)

# Or evaluate a previous run by passing the exact versioned run directory.
eval_pipeline = EvalTiledEnsemble(root_dir=Path("results/Padim/MVTecAD/bottle/v0"))
eval_pipeline.run(train_args)
```

`TrainTiledEnsemble` has no constructor arguments and exposes `root_dir` after `run`. `EvalTiledEnsemble` requires `root_dir` at construction time; this must be the ensemble run directory containing the tiled weights and statistics, not the parent results directory.

## Config schema

A small CPU-oriented skeleton looks like this:

```yaml
seed: 42
accelerator: cpu
default_root_dir: results

tiling:
  image_size: [100, 100]
  tile_size: [50, 50]
  stride: 50

normalization_stage: image   # one of: tile, image, none
thresholding_stage: image    # one of: tile, image

data:
  class_path: anomalib.data.MVTecAD
  init_args:
    root: /path/to/MVTecAD
    category: bottle
    train_batch_size: 32
    eval_batch_size: 32
    num_workers: 0
    train_augmentations: null
    val_augmentations: null
    test_augmentations: null
    augmentations: null
    test_split_mode: from_dir
    test_split_ratio: 0.2
    val_split_mode: same_as_test
    val_split_ratio: 0.5

SeamSmoothing:
  apply: true
  sigma: 2
  width: 0.1

TrainModels:
  model:
    class_path: Padim
  trainer:
    max_epochs: 1
```

Required top-level sections are `seed`, `accelerator`, `default_root_dir`, `tiling`, `normalization_stage`, `thresholding_stage`, `data`, `SeamSmoothing`, and `TrainModels`. `TrainModels.model` is required. `TrainModels.trainer` is optional but is the safe place to reduce runtime for experiments, for example with `max_epochs: 1`.

## Tiling behavior and cost

`tiling.image_size` is the full effective image size. `tiling.tile_size` is the input size seen by each tile model. `tiling.stride` controls overlap:

- `stride == tile_size` gives non-overlapping tiles.
- `stride < tile_size` gives overlapping tiles and increases tile count.
- More tile locations means more models, more checkpoints, more predictions, and higher runtime.

For an image size of `[100, 100]`, tile size `[50, 50]`, and stride `50`, the ensemble has a 2×2 grid, so it trains four models. With overlap, the grid grows; for example, a 512 image, 256 tile, and 128 stride gives a 3×3 grid.

The tiled datamodule uses a tile collater so each dataloader batch returns only one tile location. The model pre-processor is adjusted so model input size matches `tile_size`; datamodule transforms are adjusted so the ensemble image size matches `image_size`.

## Training stages

`TrainTiledEnsemble` sets up a shared versioned workspace under:

```text
<default_root_dir>/<ModelName>/<DatasetName>/<category>/<version>
```

Then it assembles these stages:

1. **TrainModels**: one job per tile location. CUDA uses a `ParallelRunner` over visible CUDA devices; CPU uses `SerialRunner`.
2. **Predict validation**: one job per tile location on validation data, reusing the trained engines from stage 1 when available.
3. **Merge**: combines tile-level predictions into image-level predictions.
4. **Seam smoothing**: optional, enabled by `SeamSmoothing.apply`.
5. **Statistics**: computes min/max and image/pixel thresholds from validation predictions and saves them near the lightning weights.

If the datamodule has `val_split_mode: none`, validation-dependent statistics are skipped. Warn the user that later image-level normalization or thresholding may not have the expected stats file.

## Evaluation stages

`EvalTiledEnsemble(root_dir=...)` uses an existing tiled ensemble run. It assembles these stages:

1. **Predict test**: one job per tile location. If no trained engines are passed from training, each tile job loads its checkpoint from `<root_dir>/weights/lightning/model<i>_<j>.ckpt`.
2. **Merge**: reconstructs image-level predictions from tile predictions.
3. **Seam smoothing**: optional, controlled by `SeamSmoothing.apply`.
4. **Normalization**: runs only when `normalization_stage: image`.
5. **Thresholding**: runs only when `thresholding_stage: image`.
6. **Visualization**: writes prediction visualizations under the run's image output directory.
7. **Metrics**: computes evaluator metrics and saves `metric_results.csv` in the run root.

If `test_split_mode: none`, evaluation returns no runners and skips the test phase.

## Normalization and thresholding

`normalization_stage` options:

- `tile`: normalize each tile model output separately by enabling the model post-processor's normalization.
- `image`: normalize after merging tile predictions into image-level outputs.
- `none`: do not min-max normalize outputs; threshold values are read from validation statistics.

`thresholding_stage` options:

- `tile`: keep thresholding at tile level.
- `image`: threshold after image-level merge.

When normalization is active, image/pixel thresholds are treated as `0.5`. When normalization is `none`, thresholds are read from the saved stats JSON produced during validation.

## Results-root selection

For evaluation, `root_dir` must be the exact versioned run directory. It should contain evidence such as:

```text
weights/lightning/model0_0.ckpt
weights/lightning/model0_1.ckpt
weights/lightning/model1_0.ckpt
weights/lightning/model1_1.ckpt
weights/lightning/stats.json          # when validation statistics were calculated
metric_results.csv                    # after evaluation metrics run
images/...                            # after visualization
```

Common wrong choices are:

- `results/` — too high; it contains all runs.
- `results/Padim/` or `results/Padim/MVTecAD/bottle/` — still too high if the versioned run is below it.
- the dataset root — this is `data.init_args.root`, not the ensemble results root.

Use the bundled smoke helper with `--tiled-config` and `--eval-root` to catch obvious path mistakes before running evaluation.

## Runtime caveats

- Treat tiled ensemble as experimental and potentially unstable across Anomalib versions.
- The default example uses CUDA and a real dataset; do not assume it is safe for a CPU-only or time-limited session.
- For a lightweight trial, prefer CPU, small image/tile sizes, `num_workers: 0`, one model, one category, and `max_epochs: 1`.
- The helper scripts from the source repository are useful evidence for argument flow, but this skill intentionally keeps bundled runtime support to import/config smoke checking rather than shipping a training launcher.
