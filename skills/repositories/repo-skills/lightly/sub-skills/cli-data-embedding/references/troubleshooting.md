# Troubleshooting Lightly CLI, data, crop, and embedding workflows

## Quick diagnosis order

1. Confirm installation and PATH: `lightly-version`.
2. Build the command without executing it: `python scripts/build_cli_command.py ...`.
3. Validate the input folder: `python scripts/validate_lightly_image_folder.py <input_dir>`.
4. If cropping, validate labels too: `python scripts/validate_lightly_image_folder.py <input_dir> --label-dir <label_dir> --label-names-file <data.yaml>`.
5. Use bounded smoke overrides before expensive runs: `trainer.max_epochs=1 loader.batch_size=2 loader.num_workers=0 trainer.gpus=0 collate.input_size=32`.

## Hydra override failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Override key is rejected or silently ineffective | Misspelled config key | Use `input_dir`, `label_dir`, `checkpoint`, `loader.batch_size`, `trainer.max_epochs`, `collate.input_size`. |
| `input=...` does not behave as expected | The verified config key is `input_dir` | Replace with `input_dir=...`. |
| `labels_dir=...` fails for crop | The verified crop key is `label_dir` | Replace with `label_dir=...`. |
| Shell splits an override value | Unquoted path or list | Quote the entire `key=value` token if it contains spaces or shell metacharacters. |
| A dotted key fails | Wrong namespace | Check the config namespaces in `cli-reference.md`; common namespaces are `model`, `criterion`, `optimizer`, `collate`, `loader`, `trainer`, `checkpoint_callback`, and `summary_callback`. |

Use the command builder's override validation before running:

```bash
python scripts/build_cli_command.py train --input-dir data --override trainer.max_epochs=1
```

## Missing or empty input folders

| Symptom | Likely cause | Fix |
|---|---|---|
| Input directory does not exist | Wrong path or Hydra run-directory confusion | Resolve the path before command execution; prefer absolute or shell-verified paths in automation. |
| Dataset has no files | Empty folder or unsupported extensions | Use supported image/video extensions listed in `data-formats.md`; validate with the bundled folder validator. |
| Root-level images disappear when class folders exist | Mixed flat and class-subdirectory layout | Choose one layout; move all images into class subdirectories or keep all images flat. |
| Output appears inside the input dataset | Default Hydra output under or near the current run directory | Put `hydra.run.dir` and crop `output_dir` outside the input root when possible. |

## Video and PyAV issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Folder contains `.mp4`, `.mov`, `.avi`, or similar and dataset loading fails | Optional video dependencies are missing | Install with `pip install "lightly[video]"`, or extract frames to an image folder. |
| Video loading is very slow | Random frame access from compressed video | Extract frames when speed matters more than disk usage. |
| Timestamp or empty-video errors | Corrupt/empty video or backend timestamp behavior | Remove bad videos, verify they decode with a video tool, or convert/extract frames. |

## YOLO crop problems

| Symptom | Likely cause | Fix |
|---|---|---|
| Crop command cannot find a label file | `label_dir` does not mirror image filenames/subdirectories | For `images/class/img.jpg`, create `labels/class/img.txt`. |
| Label parser raises a value-unpack or conversion error | A row does not contain five numeric values | Use `class_id x_center y_center width height`. |
| Crops are too tight or cut off objects | Padding too small | Increase `crop_padding`, e.g. `crop_padding=0.2`. |
| Output filenames use numeric classes instead of names | No `label_names_file` provided | Add a YAML file with `names: [class0, class1, ...]` and pass `label_names_file=data.yaml`. |
| Crops are missing for some images | Empty label file or no boxes for that image | Confirm whether zero-object images are intended; otherwise add YOLO rows. |

Generate a known-good fixture to isolate command issues from dataset issues:

```bash
python scripts/create_tiny_yolo_crop_fixture.py /tmp/lightly-yolo-fixture
```

## Checkpoint and pretrained model behavior

| Symptom | Likely cause | Fix |
|---|---|---|
| Training tries to load a pretrained model when you expected random initialization | `pre_trained` defaults to `True` | Add `pre_trained=False` for from-scratch training. |
| Pretrained checkpoint download/path fails | The default pretrained model URL/path is unavailable in the current environment | Provide `checkpoint=<local.ckpt>` or use `pre_trained=False`. |
| Resume command cannot find the last checkpoint | Environment variable was set only inside a child process | Capture the printed checkpoint path or set a stable `checkpoint_callback.dirpath`. |
| Checkpoint path works in one shell but not another | Relative path resolved against a different working directory or Hydra run directory | Use a shell-verified absolute path or a path relative to the command's launch directory. |

## Embedding output problems

| Symptom | Likely cause | Fix |
|---|---|---|
| `LIGHTLY_LAST_EMBEDDING_PATH` is empty in the parent shell | Child process environment does not persist upward | Capture command output or search the Hydra run directory for `embeddings.csv`. |
| Expected `embeddings=<path>` override does not choose the output path | The CLI writes `embeddings.csv` in the Hydra working directory | Control `hydra.run.dir` instead, or use Python `lightly.core.embed_images` and save the returned values yourself. |
| Embedding CSV validation fails | Header spelling, whitespace, missing `labels`, malformed `embedding_*` columns, or empty rows | Regenerate with `lightly.utils.io.save_embeddings` or fix the CSV header/body. |
| Embeddings are not in the expected input order | Dataset filename ordering differs from filesystem listing | Use returned `filenames` or CSV `filenames` as the authoritative order. |

## Runtime budget and side effects

- `lightly-version` and the bundled helper scripts are safe to run.
- `lightly-crop` writes cropped images to `output_dir`.
- `lightly-ssl-train`, `lightly-embed`, and `lightly-magic` can create Hydra run directories, checkpoints, downloads/cache access, and embedding CSVs.
- Always choose explicit input/output directories and bounded overrides before running on large datasets.
