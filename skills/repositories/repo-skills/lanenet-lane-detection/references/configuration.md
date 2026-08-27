# LaneNet configuration overview

`config/tusimple_lanenet.yaml` is the main runtime config file. It is loaded through `local_utils.config_utils.parse_config_utils.lanenet_cfg`, so repository-relative paths matter.

## Top-level sections

| Section | Purpose | Key values seen in this repo |
| --- | --- | --- |
| `AUG` | Image resize, crop, flip, and augmentation behavior | `TRAIN_CROP_SIZE: [512, 256]`, `EVAL_CROP_SIZE: [512, 256]`, `CROP_PAD_SIZE: 32`, `MIRROR: True` |
| `DATASET` | Dataset root, list files, normalization constants, and class count | `DATA_DIR`, `TRAIN_FILE_LIST`, `VAL_FILE_LIST`, `TEST_FILE_LIST`, `NUM_CLASSES: 2`, `IMAGE_TYPE: rgb` |
| `FREEZE` | Frozen-model filename fragments | `MODEL_FILENAME`, `PARAMS_FILENAME` |
| `MODEL` | LaneNet identity and front-end choice | `MODEL_NAME: lanenet`, `FRONT_END: bisenetv2`, `EMBEDDING_FEATS_DIMS: 4` |
| `TEST` | Evaluation model path | `TEST_MODEL` |
| `TRAIN` | Checkpoint, log, TensorBoard, mIoU, restore, and multi-GPU controls | `MODEL_SAVE_DIR`, `TBOARD_SAVE_DIR`, `SNAPSHOT_EPOCH`, `BATCH_SIZE`, `VAL_BATCH_SIZE`, `MULTI_GPU.*` |
| `SOLVER` | Optimizer and learning-rate schedule | `LR: 0.001`, `LR_POLICY: poly`, `OPTIMIZER: sgd`, `MOMENTUM: 0.9`, `WEIGHT_DECAY: 0.0005` |
| `GPU` | TensorFlow session GPU memory behavior | `GPU_MEMORY_FRACTION: 0.9`, `TF_ALLOW_GROWTH: True` |
| `POSTPROCESS` | DBSCAN clustering and connected-component filtering | `MIN_AREA_THRESHOLD: 100`, `DBSCAN_EPS: 0.35`, `DBSCAN_MIN_SAMPLES: 1000` |
| `LOG` | Logging destination and severity | `SAVE_DIR: ./log`, `LEVEL: INFO` |

## Important path behavior

- `DATASET.DATA_DIR` uses the checked-in placeholder `REPO_ROOT_PATH/data/training_data_example/`.
- `TRAIN_FILE_LIST`, `VAL_FILE_LIST`, and `TEST_FILE_LIST` also use `REPO_ROOT_PATH` placeholders in the shipped config.
- The sample data list files contain placeholder text such as `REPO_ROOT_PATH` or `ROOT_PATH`; replace them before direct use.
- `local_utils.config_utils.parse_config_utils.lanenet_cfg` reads the config with a relative path, so running from the repository root is the safest default.

## Common edits

- Change `MODEL.FRONT_END` to switch the encoder branch (`bisenetv2` or `vgg`).
- Change `TRAIN.MULTI_GPU.ENABLE` and `TRAIN.MULTI_GPU.GPU_DEVICES` to match the available devices.
- Lower `TRAIN.BATCH_SIZE` when using a tiny smoke dataset so the training loop still enters at least one update step.
- Adjust `POSTPROCESS.DBSCAN_EPS` and `POSTPROCESS.DBSCAN_MIN_SAMPLES` when custom data yields empty masks.
