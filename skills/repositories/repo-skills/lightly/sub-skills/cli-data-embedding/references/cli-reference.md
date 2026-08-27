# LightlySSL CLI reference

Lightly installs the distribution/import name `lightly` and provides these console entry points:

| Entry point | Use it for | Writes artifacts? |
|---|---|---|
| `lightly-version` | Print the installed LightlySSL package version. | No. |
| `lightly-ssl-train` | Train a self-supervised ResNet embedding model from an image/video folder. | Yes: Hydra run directory and checkpoints. |
| `lightly-embed` | Embed an input folder with a pretrained model or checkpoint. | Yes: `embeddings.csv` in the Hydra run directory. |
| `lightly-magic` | Train, then embed the same input folder. If `trainer.max_epochs=0`, skips training and embeds with the pretrained path behavior. | Yes: train artifacts and embeddings. |
| `lightly-crop` | Crop objects from images using YOLO-format label files. | Yes: cropped image output directory. |

Install guidance for future users: `pip install lightly`. Add `lightly[timm]` for optional TIMM / MAE / ViT-style modules and `lightly[video]` for direct video file datasets requiring PyAV.

## Hydra command syntax

The train, embed, magic, and crop commands use Hydra-style overrides:

```bash
lightly-ssl-train input_dir=data trainer.max_epochs=5 loader.batch_size=128
lightly-embed input_dir=data checkpoint=last.ckpt collate.input_size=224
lightly-magic input_dir=data trainer.max_epochs=10 loader.num_workers=8
lightly-crop input_dir=images label_dir=labels output_dir=crops crop_padding=0.2
```

Use `key=value` tokens separated by spaces. Nested config values use dotted keys such as `loader.batch_size`, `collate.input_size`, and `checkpoint_callback.dirpath`. Quote values if your shell would split them.

Important spelling notes:

- Use `input_dir`, not `input`.
- Use `label_dir`, not `labels_dir`, for `lightly-crop`.
- Use `checkpoint`, not `checkpoint_path`.
- Use `pre_trained=False` to train from scratch; if `pre_trained=True` and no checkpoint is provided, Lightly tries its pretrained model path behavior.
- `lightly-embed` writes `embeddings.csv` in the Hydra working directory; the `embeddings` config key is state-like and should not be treated as a reliable output-path override.

For safe dry-run construction without executing Lightly, use:

```bash
python scripts/build_cli_command.py train --input-dir data --max-epochs 5 --batch-size 128
python scripts/build_cli_command.py crop --input-dir images --label-dir labels --output-dir crops --crop-padding 0.2
```

## Command-specific operating notes

### `lightly-version`

Use this first when diagnosing installation or PATH issues:

```bash
lightly-version
```

Expected shape: `lightly version <version>`.

### `lightly-ssl-train`

Minimum meaningful command:

```bash
lightly-ssl-train input_dir=data
```

Useful bounded overrides:

```bash
lightly-ssl-train input_dir=data trainer.max_epochs=1 loader.batch_size=16 loader.num_workers=0 trainer.gpus=0
```

Artifacts and state:

- The default Hydra run directory pattern is `lightly_outputs/<date>/<time>`.
- Checkpoints are managed by `checkpoint_callback.*` settings.
- The command sets the process environment variable name configured as `environment_variable_names.lightly_last_checkpoint_path`, which defaults to `LIGHTLY_LAST_CHECKPOINT_PATH`. Because child-process environment variables do not persist back into an already-running parent shell, capture printed paths or run follow-up commands in the same controlling process when necessary.

### `lightly-embed`

Minimum meaningful command:

```bash
lightly-embed input_dir=data
```

Embedding from a custom or previous checkpoint:

```bash
lightly-embed input_dir=data checkpoint=last.ckpt collate.input_size=224 loader.batch_size=64
```

Artifacts and state:

- The command saves `embeddings.csv` in the Hydra working directory.
- It sets `LIGHTLY_LAST_EMBEDDING_PATH` inside the running process by default.
- During embedding, Lightly disables dataloader shuffling and `drop_last`, and caps batch size to the dataset length.

### `lightly-magic`

`lightly-magic` combines train and embed:

```bash
lightly-magic input_dir=data trainer.max_epochs=10 loader.batch_size=128 loader.num_workers=8
```

Equivalent conceptual breakdown:

```bash
lightly-ssl-train input_dir=data
lightly-embed input_dir=data checkpoint=$LIGHTLY_LAST_CHECKPOINT_PATH
```

If `trainer.max_epochs=0`, the command skips training and proceeds to embedding with no newly produced checkpoint.

### `lightly-crop`

Required path trio:

```bash
lightly-crop input_dir=images label_dir=labels output_dir=cropped_images crop_padding=0.2
```

With class-name YAML:

```bash
lightly-crop input_dir=images label_dir=labels output_dir=cropped_images label_names_file=data.yaml
```

`label_dir` must contain one YOLO `.txt` file for each input image, matching the image filename with the extension changed to `.txt`. If images are under class subdirectories, mirror those relative subdirectories under `label_dir`.

## Default config keys verified from the bundled CLI config

Top-level keys:

- `input_dir`: input image/video folder.
- `output_dir`: crop output folder.
- `embeddings`: embedding path state key; do not rely on it as the CLI output path.
- `checkpoint`: checkpoint path or empty string for pretrained behavior.
- `label_dir`: YOLO label folder for crop.
- `label_names_file`: YAML file with `names` for crop class names.
- `pre_trained`: boolean; default `True`.
- `crop_padding`: crop padding fraction; default `0.1`.
- `seed`: default `1`.

Nested keys:

| Namespace | Keys |
|---|---|
| `model` | `name`, `out_dim`, `num_ftrs`, `width` |
| `criterion` | `temperature`, `memory_bank_size` |
| `optimizer` | `lr`, `weight_decay` |
| `collate` | `input_size`, `cj_prob`, `cj_bright`, `cj_contrast`, `cj_sat`, `cj_hue`, `min_scale`, `random_gray_scale`, `gaussian_blur`, `sigmas`, `kernel_size`, `vf_prob`, `hf_prob`, `rr_prob`, `rr_degrees` |
| `loader` | `batch_size`, `shuffle`, `num_workers`, `drop_last` |
| `trainer` | `gpus`, `max_epochs`, `precision`, `enable_model_summary`, `weights_summary` |
| `checkpoint_callback` | `save_last`, `save_top_k`, `dirpath` |
| `summary_callback` | `max_depth` |
| `environment_variable_names` | `lightly_last_checkpoint_path`, `lightly_last_embedding_path` |
| `hydra.run` | `dir` |

## Common override bundles

CPU-safe smoke planning:

```bash
trainer.gpus=0 trainer.max_epochs=1 loader.batch_size=2 loader.num_workers=0 collate.input_size=32
```

Fast embedding planning:

```bash
loader.batch_size=64 loader.num_workers=0 collate.input_size=224
```

Crop planning:

```bash
crop_padding=0.1 label_names_file=data.yaml
```

Checkpoint directory control:

```bash
checkpoint_callback.dirpath=checkpoints checkpoint_callback.save_last=True checkpoint_callback.save_top_k=1
```

Hydra output directory control:

```bash
hydra.run.dir=lightly_outputs/manual_run
```
