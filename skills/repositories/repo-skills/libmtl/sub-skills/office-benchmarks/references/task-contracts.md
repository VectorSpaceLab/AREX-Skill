# Office Task Contracts

This file distills the benchmark-specific task dictionaries, loaders, and
model wiring used by the Office-31 and Office-Home workflows.

## Dataset families

- Office-31: `amazon`, `dslr`, `webcam` with 31 classes each
- Office-Home: `Art`, `Clipart`, `Product`, `Real_World` with 65 classes each

## Task dictionary shape

Each task uses:

- `metrics=['Acc']`
- `metrics_fn=AccMetric()`
- `loss_fn=CELoss()`
- `weight=[1]`

## Model wiring

- Shared encoder: `resnet18(pretrained=True)` followed by a small projection
  block that outputs 512 features.
- Task decoders: one `nn.Linear(512, class_num)` per task.
- The model is multi-input, so each task has its own dataloader.

## Data contract

- Split text files are bundled under `references/data_txt/<dataset>/` for
  reference and under the runtime package's `data_txt/<dataset>/` for actual
  execution.
- Each line stores a relative image path and an integer class id.
- `--dataset_path` points at the raw image root, not the split-file directory.
- The self-contained runtime entry point is `scripts/main.py`; the installable
  console entry point is `libmtl-office` after running
  `scripts/install_office_runtime.py`.

## Runtime notes

- `multi_input` must be `True`.
- The shared trainer still expects CUDA.
- `train`, `val`, and `test` dataloaders all use the same batch size.
