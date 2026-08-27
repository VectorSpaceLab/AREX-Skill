# Configuration

## Purpose

Read this when editing a JSON config, debugging config parsing, or wiring output directories for a project based on TensorFlow Project Template.

## Example config keys

The repository's `configs/example.json` contains:

```json
{
  "exp_name": "example",
  "num_epochs": 10,
  "num_iter_per_epoch": 10,
  "learning_rate": 0.001,
  "batch_size": 16,
  "state_size": [784],
  "max_to_keep": 5
}
```

| Key | Used by | Meaning in inspected source |
|---|---|---|
| `exp_name` | `utils.config.process_config` | Names the experiment directory under `../experiments/<exp_name>/`. |
| `num_epochs` | `BaseTrain.train` | Upper bound for epoch loop. Because the source uses `num_epochs + 1`, starting at epoch `0` runs one extra epoch. |
| `num_iter_per_epoch` | `ExampleTrainer.train_epoch` | Number of train steps per epoch. |
| `learning_rate` | `ExampleModel.build_model` | Adam optimizer learning rate. |
| `batch_size` | `ExampleTrainer.train_step` | Batch size passed to `DataGenerator.next_batch`. |
| `state_size` | `ExampleModel.build_model` | Appended to `[None]` for the input placeholder shape. Example `[784]` expects flat 784-feature vectors. |
| `max_to_keep` | `ExampleModel.init_saver` | Passed to `tf.train.Saver(max_to_keep=...)`. |

## Config parsing contract

`utils.config.get_config_from_json(json_file)`:

1. Opens the supplied JSON file.
2. Loads it with Python `json.load`.
3. Converts the dictionary to `bunch.Bunch` so values can be read as attributes.
4. Returns `(config, config_dict)`.

`utils.config.process_config(json_file)` calls `get_config_from_json`, then adds:

```python
config.summary_dir = os.path.join("../experiments", config.exp_name, "summary/")
config.checkpoint_dir = os.path.join("../experiments", config.exp_name, "checkpoint/")
```

Those paths are relative to the current process directory. If a future agent runs a main script from a different directory than the original example expected, outputs may be created in an unexpected parent directory.

## CLI contract

`utils.utils.get_args()` defines:

```bash
-c C, --config C
```

The default is the literal string `None`. In the repository's example main, missing or invalid config handling is broad:

```python
try:
    args = get_args()
    config = process_config(args.config)
except:
    print("missing or invalid arguments")
    exit(0)
```

For real automation, replace the bare `except` with explicit handling for missing files, invalid JSON, and missing keys, and exit non-zero on errors.

## Output directory behavior

The example main calls:

```python
create_dirs([config.summary_dir, config.checkpoint_dir])
```

Then `Logger` writes TensorBoard events under:

- `config.summary_dir/train`
- `config.summary_dir/test`

`BaseModel.save(sess)` passes `config.checkpoint_dir` directly to `tf.train.Saver.save(...)`. `BaseModel.load(sess)` passes the same value to `tf.train.latest_checkpoint(...)`.

This creates an ambiguity: TensorFlow save uses a filename prefix, while latest-checkpoint lookup normally wants a directory. When adapting the template, make the checkpoint contract explicit. Two safe options are:

1. Keep `config.checkpoint_dir` as a directory and change `save()` to use `os.path.join(config.checkpoint_dir, "model.ckpt")`.
2. Add separate `checkpoint_dir` and `checkpoint_prefix` fields and use each in the appropriate method.

## Recommended project-specific config additions

For real models, add only keys that code actually reads, and document where each one is used. Common additions are:

| Key | Typical owner |
|---|---|
| `num_classes` | Model output shape and data labels. |
| `seed` | Data sampling, NumPy, and TensorFlow graph reproducibility. |
| `train_data`, `valid_data`, `test_data` | Data generator. |
| `shuffle`, `prefetch`, `num_workers` | Data pipeline. |
| `checkpoint_every`, `summary_every` | Trainer save/log cadence. |
| `resume` or `restore_path` | Main script/model loading. |
| `device` | Session or framework placement policy. |

## Config validation checklist

Before launching a real training run:

- Parse the JSON with `process_config`.
- Check all fields read by model/trainer/data/logger exist.
- Check numeric values are positive where required: `batch_size`, `num_iter_per_epoch`, `max_to_keep`.
- Check `state_size` matches the data generator's feature shape.
- Check label dimensionality matches the model output shape.
- Check summary/checkpoint directories point to a deliberate experiment workspace.
- If using a filename checkpoint prefix, create its parent directory rather than the prefix itself.

The bundled `scripts/check_template_static.py` verifies the example config's required keys and can be used as a starting point for stronger project-specific validation.
