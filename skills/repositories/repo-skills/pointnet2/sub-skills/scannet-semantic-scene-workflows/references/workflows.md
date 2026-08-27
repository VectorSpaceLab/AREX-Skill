# ScanNet semantic scene workflows

Use this reference to reason about ScanNet preprocessing, training, and evaluation without reopening the original repository files.

## Quick routing table

| User intent | Use | Notes |
|---|---|---|
| "Do I have the right ScanNet files?" | `scripts/validate_scannet_layout.py` | Validate pickles first; raw scene folders and demo outputs are optional separate checks. |
| "How do I preprocess raw ScanNet?" | Raw preprocessing recipe below | Requires external ScanNet data, scene list, path edits, and the correct V1/V2 TSV columns. |
| "How do I train/evaluate ScanNet semantic segmentation?" | Legacy trainer command from `scripts/build_scannet_command.py train` | Python 2 + TensorFlow 1.x workflow; PointNet++ model execution normally needs compiled custom ops. |
| "Why is whole-scene evaluation slow or memory-heavy?" | Whole-scene evaluation section | Memory scales with `batch_size * num_point` and large scenes can generate many tiles. |
| "Can I use RGB or instance ids in the model input?" | Data format contract | The semantic model consumes XYZ only; RGB/instance ids belong to raw `.npy` preprocessing artifacts, not the trainer pickle point arrays. |

## Environment and backend expectations

The ScanNet workflow is a legacy TensorFlow 1.x workflow. The repository evidence was inspected in a legacy Python 2.7 / TensorFlow 1.x CPU environment, and a tiny ScanNet fixture smoke passed there. Full PointNet++ ScanNet training/evaluation remains an optional CUDA/custom-op path because the semantic model uses PointNet++ set-abstraction and feature-propagation layers that normally depend on compiled TensorFlow custom operators.

Practical implications:

- Static command generation, pickle validation, label-table validation, and tiny loader smokes are CPU-safe.
- Running the raw trainer is a Python 2 command path and may fail in Python 3 before reaching TensorFlow.
- Building or executing the full semantic segmentation graph normally requires the shared custom-op guidance from the repo skill's `model-apis-and-custom-ops` sub-skill.

## Preprocessed-data workflow

Preferred route when the user only wants to train/evaluate:

1. Put the preprocessed data under `data/scannet_data_pointnet2/` with `scannet_train.pickle` and `scannet_test.pickle`.
2. Validate the pickles:

   ```bash
   python3 scripts/validate_scannet_layout.py data/scannet_data_pointnet2 --splits train test
   ```

3. If validation passes, construct a legacy command:

   ```bash
   python3 scripts/build_scannet_command.py train --repo-root . --log-dir log_scannet
   ```

4. Run the emitted command only in a compatible legacy checkout/environment.

The trainer creates training and test TensorBoard writers under the chosen log directory, writes `log_train.txt`, saves `model.ckpt` every 10 epochs, and saves `best_model_epoch_<epoch>.ckpt` when the whole-scene calibrated accuracy improves.

## Raw preprocessing workflow

Use this route only when the preprocessed `scannet_data_pointnet2` pickles are unavailable and the user has the original ScanNet download.

1. Prepare a scene-list file such as `scannet_all.txt`.
2. Confirm the raw scene folders contain the required files:

   ```bash
   python3 scripts/validate_scannet_layout.py \
     --raw-scan-root /path/to/scannet_clean_2 \
     --scene-list scannet_all.txt
   ```

3. Confirm the label TSV columns. V1 uses raw column `0` and NYU40 column `6`:

   ```bash
   python3 scripts/validate_scannet_layout.py --label-tsv scannet-labels.combined.tsv --raw-column 0 --nyu40-column 6
   ```

   For ScanNetV2, inspect the V2 header and use the shifted columns instead of blindly reusing `(0, 6)`.

4. Generate a reference command:

   ```bash
   python3 scripts/build_scannet_command.py preprocess --repo-root . --step collect
   ```

5. Before running the legacy collector, edit or wrap its hard-coded paths so that:
   - `SCANNET_DIR` points at the raw ScanNet folder;
   - the working directory contains the expected `scannet_all.txt`;
   - the working directory has the chosen label TSV file;
   - output goes to a writable `scannet_scenes/` directory.

6. Convert the generated `scannet_scenes/*.npy` files into the two trainer pickle objects: a list of XYZ arrays and a list of 1-D semantic label arrays. The raw `.npy` files themselves are `N x 8` and are not a direct replacement for the trainer pickles.

## Label-fetch and demo helper recipes

The reference label-fetch script scans aggregation JSON files and writes `class_names.txt`. Its raw-data path is hard-coded and should be treated as a recipe, not a portable runtime command. Generate its command with:

```bash
python3 scripts/build_scannet_command.py preprocess --repo-root . --step fetch-labels
```

The reference demo reads `scannet_scenes/scene0001_01.npy` and writes OBJ-like files under `demo_output/`. Generate and validate independently:

```bash
python3 scripts/build_scannet_command.py preprocess --repo-root . --step demo
python3 scripts/validate_scannet_layout.py --demo-output demo_output
```

A missing demo output does not prove raw preprocessing is impossible; it only means the demo has not produced the three expected files.

## Legacy trainer flow

The trainer sets:

- `NUM_CLASSES = 21`.
- `DATA_PATH = data/scannet_data_pointnet2` relative to the repository root.
- `TRAIN_DATASET = ScannetDataset(..., split='train')`.
- `TEST_DATASET = ScannetDataset(..., split='test')` for random chopped-scene evaluation.
- `TEST_DATASET_WHOLE_SCENE = ScannetDatasetWholeScene(..., split='test')` for the paper-style whole-scene metric.

Default flags from the source trainer:

| flag | default | meaning |
|---|---:|---|
| `--gpu` | `0` | TensorFlow device id used as `/gpu:<id>`. |
| `--model` | `model` | Import module name. For this repo's semantic model use `pointnet2_sem_seg` with a `PYTHONPATH` that includes `models/`, or copy/symlink the model file into the ScanNet working directory. |
| `--log_dir` | `log` | Output directory for logs, summaries, and checkpoints. |
| `--num_point` | `8192` | Points sampled per block/tile. |
| `--max_epoch` | `201` | Number of epochs. |
| `--batch_size` | `32` | Number of blocks/tiles per model call. Reduce for memory pressure. |
| `--learning_rate` | `0.001` | Initial learning rate. |
| `--momentum` | `0.9` | Momentum optimizer value when `--optimizer momentum`. |
| `--optimizer` | `adam` | `adam` or `momentum`. |
| `--decay_step` | `200000` | Exponential decay step. |
| `--decay_rate` | `0.7` | Exponential decay multiplier. |

Training loop behavior:

1. Shuffle scene indices.
2. Build random blocks via `ScannetDataset`.
3. Apply Z-axis point-cloud rotation and random point dropout.
4. Optimize weighted sparse softmax cross entropy.
5. Every 5 epochs, run random chopped-scene evaluation and whole-scene evaluation.
6. Use whole-scene calibrated average accuracy as the checkpoint-selection metric.

## Semantic segmentation model family

The ScanNet trainer is meant to pair with the semantic segmentation PointNet++ model:

- Inputs: `pointclouds_pl` shape `(batch_size, num_point, 3)`, `labels_pl` shape `(batch_size, num_point)`, and `smpws_pl` shape `(batch_size, num_point)`.
- Set-abstraction layers:
  - `1024` points, radius `0.1`, `32` samples, MLP `[32, 32, 64]`.
  - `256` points, radius `0.2`, `32` samples, MLP `[64, 64, 128]`.
  - `64` points, radius `0.4`, `32` samples, MLP `[128, 128, 256]`.
  - `16` points, radius `0.8`, `32` samples, MLP `[256, 256, 512]`.
- Feature-propagation layers recover per-point features through MLPs `[256, 256]`, `[256, 256]`, `[256, 128]`, and `[128, 128, 128]`.
- Final layers apply a `1x1` convolution to 128 channels, dropout keep probability `0.5`, and a final `1x1` convolution to `num_class` logits.
- Loss is sparse softmax cross entropy weighted by `smpws_pl`.

Because this model consumes only XYZ, do not advise adding RGB channels unless the model placeholder and architecture are changed consistently.

## Random chopped-scene evaluation

`eval_one_epoch` evaluates random blocks from the test split. It:

- rotates blocks around Z before inference;
- computes point accuracy only where `label > 0` and sample weight is positive;
- computes class accuracy for ids `1..20`;
- voxelizes points using a `0.02` resolution helper before voxel-based metrics;
- reports a calibrated average using the fixed 20-class calibration weights from the source script.

This mode is useful for monitoring but is not the same as whole-scene evaluation.

## Whole-scene evaluation

`eval_whole_scene_one_epoch` evaluates tiled full scenes. It:

- obtains all valid tiles for one scene from `ScannetDatasetWholeScene`;
- concatenates tiles across scenes until it reaches `batch_size`;
- keeps overflow tiles for the next model call;
- does not apply the training/eval Z rotation;
- computes the same label-positive point metrics and `0.02`-resolution voxel metrics;
- returns calibrated voxel average accuracy (`caliacc`), which controls the best-checkpoint save.

If a large scene yields many tiles, reducing `--batch_size` reduces per-call memory but does not reduce the total number of tile inferences. Reducing `--num_point` changes the model input shape and should be treated as an experimental change, not a pure memory tweak.

## Virtual-scan support

`ScannetDatasetVirtualScan` creates view-dependent samples by calling `scene_util.virtual_scan` for eight fixed directions. The virtual scan:

- places a camera near the scene center at human height (`z = 1.5`);
- projects points into angular coordinates;
- finds nearest rays on a `200 x 150` ray grid;
- keeps only approximately visible nearest points;
- skips views with fewer than about 300 sampled points.

The README states that virtual scan data is generated on the fly from the preprocessed data. It is a dataset variant rather than the default training/evaluation path used by `scannet/train.py`.

## Native coverage anchors

This sub-skill owns these verification anchors:

- `scannet-command-and-preprocessing-surface`: static command/data-schema coverage of the trainer and preprocessing scripts; native execution only with compatible legacy CUDA/custom-op environment and data.
- `scannet-layout-validator`: CPU-safe tiny-fixture validation of pickle structure, labels, label maps, and raw/demo path checks.
