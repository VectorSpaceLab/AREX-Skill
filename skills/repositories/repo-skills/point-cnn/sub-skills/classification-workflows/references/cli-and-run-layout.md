# Classification CLI and run layout

## Command-line interface

Run from the project root so the legacy imports (`data_utils`, `pointfly`, `pointcnn_cls`) resolve:

```bash
python3 train_val_cls.py \
  --path /data/modelnet/train_files.txt \
  --path_val /data/modelnet/test_files.txt \
  --save_folder /work/pointcnn-classification \
  --model pointcnn_cls \
  --setting modelnet_x3_l4
```

Aliases and options implemented by `train_val_cls.py`:

| Option | Alias | Required | Meaning |
|---|---|---:|---|
| `--path` | `-t` | yes | Training file list, or the Quick Draw NPZ directory |
| `--path_val` | `-v` | no at argparse level | Validation file list; standard HDF5 settings need it; Quick Draw ignores it |
| `--load_ckpt` | `-l` | no | Exact checkpoint prefix to restore |
| `--save_folder` | `-s` | yes | Parent or direct output folder, depending on timestamp flag |
| `--model` | `-m` | yes | Importable model module, usually `pointcnn_cls` |
| `--setting` | `-x` | yes | Setting module under the model directory |
| `--epochs` | — | no | Override `setting.num_epochs` |
| `--batch_size` | — | no | Override `setting.batch_size` |
| `--log` | — | no | Filename inside the run folder; `-` keeps stdout |
| `--no_timestamp_folder` | — | no | Write directly under `--save_folder` |
| `--no_code_backup` | — | no | Suppress the code-copy side effect |

Use quoted paths when they contain spaces. The historical dataset shell wrappers background the process and use repository-relative paths; for reproducibility and safe smoke tests, use a foreground direct command with explicit absolute or workspace-relative paths instead.

## Dynamic import checks

The model import is `importlib.import_module(args.model)`. The setting import happens after adding the directory beside the model module to `sys.path`, so `-x modelnet_x3_l4` means the file `pointcnn_cls/modelnet_x3_l4.py`, not a dotted path. Check names and syntax before allocating a run:

```bash
python3 -m py_compile train_val_cls.py pointcnn_cls.py \
  pointcnn_cls/modelnet_x3_l4.py pointcnn_cls/scannet_x2_l4.py \
  pointcnn_cls/tu_berlin_x3_l4.py pointcnn_cls/mnist_x2_l4.py \
  pointcnn_cls/cifar10_x3_l4.py pointcnn_cls/quick_draw_full_x2_l6.py
```

A successful compile only proves Python syntax. Importing a setting may import `data_utils`; graph construction additionally needs the legacy TensorFlow API and the PointCNN modules.

## Timestamp, logging, backup, and checkpoint behavior

Unless `--no_timestamp_folder` is set, the trainer creates:

```text
SAVE_FOLDER/
└── MODEL_SETTING_YYYY-MM-DD-HH-MM-SS_PID/
    ├── log.txt                 # unless --log changes it
    ├── ckpts/
    │   ├── iter-<step>.index
    │   ├── iter-<step>.meta
    │   └── iter-<step>.data-*
    ├── summary/
    │   └── events.out.tfevents.*
    └── <code-backup-directory>/ # unless --no_code_backup
```

`--no_timestamp_folder` makes `SAVE_FOLDER` the run root. The code backup copies the trainer's containing code directory and can be large or fail if a destination already exists. Use `--no_code_backup` for a disposable tiny fixture. The trainer also creates `pts/` if the selected setting supplies `save_ply_fn`; this is relevant to Quick Draw.

Before a smoke, choose a new writable output directory and avoid pointing it at a source directory. Do not delete an existing run to recover from an error. To resume, point `--load_ckpt` at the checkpoint prefix (usually `.../ckpts/iter-<step>` without `.index`). If no explicit checkpoint is supplied, the trainer searches the current run's `ckpts/` for the latest checkpoint; this is only useful with `--no_timestamp_folder` or a deliberately reused run folder.

## Graph and metrics

The trainer creates placeholders for indices, X-Conv transforms, rotations, jitter, labels, and an iterator string handle in TensorFlow graph mode. It trains sparse softmax cross entropy and records loss, top-1 accuracy, and mean per-class accuracy under `train` and `val` summary collections. Validation occurs every `setting.step_val` batches and at the final batch. Training progress is printed every ten batches.

With `keep_remainder=True`, the final batch is retained and the feed shapes are reduced to the remainder size. With `False`, the final incomplete batch is dropped. A fixture smaller than the batch size is therefore valid only for a keep-remainder setting.

## Quick Draw invocation

The Quick Draw setting calls its own loader with the `--path` directory. That directory must contain `categories.txt` and one NPZ per category named by the category list. The loader reads all categories and both `train` and `valid` arrays into memory before mapping strokes to 512-point XYZ+normal tensors. Plan RAM accordingly; do not use a full-data invocation as a smoke test. See `references/troubleshooting.md` for the `rotation_order` naming defect in this source revision.
