# Configuration Reference

## Purpose

Read this when you need to understand the runtime config object, the shipped JSON files, or the differences between the two CenterNet model variants.

## Runtime config object

`config.py` defines a singleton named `system_configs`.

### Key defaults from `config.py`

| Key | Default | Notes |
| --- | --- | --- |
| `dataset` | `None` | Set by the selected JSON config; the repo ships `MSCOCO`. |
| `sampling_function` | `kp_detection` | The sample/test pipeline uses this function name. |
| `display` | `5` | Training log interval. |
| `snapshot` | `5000` | Checkpoint save interval. |
| `stepsize` | `450000` | Learning-rate decay step. |
| `learning_rate` | `0.00025` | Base learning rate. |
| `decay_rate` | `10` | Learning-rate decay factor. |
| `max_iter` | `500000` | Default max iteration count before config override. |
| `val_iter` | `100` | Validation interval. |
| `batch_size` | `1` | Overridden by the selected config. |
| `prefetch_size` | `100` | Queue size for data prefetching. |
| `data_dir` | `data` | Root directory for the dataset. |
| `cache_dir` | `cache` | Stores checkpoints and dataset cache files. |
| `config_dir` | `config` | Location of JSON config files. |
| `result_dir` | `results` | Location of evaluation outputs. |
| `train_split` | `trainval` | Internal split name used by the dataset class. |
| `val_split` | `minival` | Internal split name used by the dataset class. |
| `test_split` | `testdev` | Internal split name used by the dataset class. |

## JSON structure

Every shipped config file has the same top-level shape:

```json
{
  "system": { ... },
  "db": { ... }
}
```

### `system`

Common fields in the shipped configs:

- `dataset`: `MSCOCO`
- `batch_size`: `48`
- `sampling_function`: `kp_detection`
- `train_split`: `trainval`
- `val_split`: `minival`
- `learning_rate`: `0.00025`
- `decay_rate`: `10`
- `val_iter`: `500`
- `opt_algo`: `adam`
- `prefetch_size`: `6`
- `max_iter`: `480000`
- `stepsize`: `450000`
- `snapshot`: `5000`
- `chunk_sizes`: `[6, 6, 6, 6, 6, 6, 6, 6]`
- `data_dir`: `../data`

### `db`

Common fields in the shipped configs:

- `rand_scale_min`, `rand_scale_max`, `rand_scale_step`
- `rand_crop`, `rand_color`
- `border`
- `gaussian_bump`
- `input_size`: `[511, 511]`
- `output_sizes`: `[[128, 128]]`
- `test_scales`
- `top_k`: `70`
- `categories`: `80`
- `kp_categories`: `1`
- `ae_threshold`: `0.5`
- `nms_threshold`: `0.5`
- `max_per_image`: `100`
- `merge_bbox` and `weight_exp` appear in the multi-scale variants

## Model variants

| Variant | File | Notes |
| --- | --- | --- |
| `CenterNet-52` | `config/CenterNet-52.json` | Single-stack model (`nstack=1`) with the same COCO class count and loss family. |
| `CenterNet-104` | `config/CenterNet-104.json` | Two-stack model (`nstack=2`) with the same COCO class count and loss family. |
| `CenterNet-52-multi_scale` | `config/CenterNet-52-multi_scale.json` | Same base model with multi-scale evaluation settings. |
| `CenterNet-104-multi_scale` | `config/CenterNet-104-multi_scale.json` | Same base model with multi-scale evaluation settings. |

## Useful selection rules

- The config basename becomes the snapshot name used for checkpoints and result directories.
- `--suffix multi_scale` changes only the config filename and result path; it does not change the checkpoint naming scheme.
- `chunk_sizes` should be chosen with the available GPU count in mind.
- The repository does not register a second dataset class, so changing away from `MSCOCO` requires extending `db/datasets.py`.
