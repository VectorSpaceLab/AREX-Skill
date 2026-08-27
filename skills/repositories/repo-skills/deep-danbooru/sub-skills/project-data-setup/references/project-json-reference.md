# `project.json` reference

## Creation

`deepdanbooru create-project PROJECT_PATH` creates the destination directory
(if absent) and serializes the following default context as JSON. It does not
create `tags.txt`, `images/`, a SQLite file, or a model.

```json
{
    "image_width": 299,
    "image_height": 299,
    "database_path": null,
    "minimum_tag_count": 20,
    "model": "resnet_custom_v2",
    "minibatch_size": 32,
    "epoch_count": 10,
    "export_model_per_epoch": 10,
    "checkpoint_frequency_mb": 200,
    "console_logging_frequency_mb": 10,
    "loss": "binary_crossentropy",
    "optimizer": "adam",
    "learning_rate": 0.001,
    "rotation_range": [0.0, 360.0],
    "scale_range": [0.9, 1.1],
    "shift_range": [-0.1, 0.1],
    "mixed_precision": false
}
```

The generated file is indented JSON and is written with UTF-8 text. The
runtime reads it by key; do not delete required keys while customizing it.

## Fields relevant to data setup

| Key | Default | Data contract |
|---|---:|---|
| `image_width` | `299` | Model input width. Keep consistent with the model workflow. |
| `image_height` | `299` | Model input height. |
| `database_path` | `null` | **Must be changed** to the dataset SQLite path before training. |
| `minimum_tag_count` | `20` | A row is eligible only when `tag_count_general >=` this value. |
| `model` | `resnet_custom_v2` | Selects the model filename and training architecture. |
| `minibatch_size` | `32` | Training batch size; not a database filter. |
| `epoch_count` | `10` | Training epochs. |
| `export_model_per_epoch` | `10` | Model-export interval. |
| `checkpoint_frequency_mb` | `200` | Checkpoint interval in megabytes. |
| `console_logging_frequency_mb` | `10` | Logging interval in megabytes. |
| `loss` | `binary_crossentropy` | Multi-label training loss. |
| `optimizer` | `adam` | Optimizer name. |
| `learning_rate` | `0.001` | Optimizer learning rate. |
| `rotation_range` | `[0.0, 360.0]` | Augmentation rotation range. |
| `scale_range` | `[0.9, 1.1]` | Augmentation scale range. |
| `shift_range` | `[-0.1, 0.1]` | Augmentation shift range. |
| `mixed_precision` | `false` | Leave false unless the runtime and hardware are explicitly validated. |

## Path handling

`database_path` is consumed as stored. Use an absolute path when the project
will be launched from different working directories; otherwise a deliberately
stable path relative to the launch context may be used only after testing it.
The SQLite file's parent directory must contain `images/` with the layout in
[`dataset-format.md`](dataset-format.md). A valid JSON file with `null`, a
stale path, or a path to the wrong database is still an unusable project.

## Minimal readiness checklist

```console
python -m json.tool PROJECT_PATH/project.json
python scripts/validate_danbooru_sqlite.py /path/to/dataset.sqlite
python scripts/validate_tags_txt.py PROJECT_PATH/tags.txt
```

These checks do not load a TensorFlow model and do not prove that all image
bytes are decodable. The training handoff must additionally inspect image
existence and select a threshold compatible with the available tag counts.
