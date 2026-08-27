# HRM Cross-Cutting Troubleshooting

## Installation stack

HRM is not packaged with `pyproject.toml`; it is a source-tree repository. The
README dependency path is:

1. PyTorch with CUDA.
2. FlashAttention 2 for Ampere or earlier GPUs, or FlashAttention 3 for Hopper.
3. `pip install -r requirements.txt`.
4. W&B login for hosted experiment tracking.

Do not treat a base Python import as enough for train/eval. The repo imports
FlashAttention in `models/layers.py` and imports the fused `adam_atan2` optimizer
in `pretrain.py`.

## Required backend distinction

- Dataset builder help, dataset layout validation, and many schema checks are
  CPU-safe.
- Real HRM model construction, training, and evaluation are CUDA-required.
- Full model forward verification depends on the exact PyTorch/FlashAttention
  behavior; a bounded current-environment smoke found a non-contiguous
  FlashAttention output `.view(...)` issue in `models/layers.py`.

## Safe first checks

```bash
python dataset/build_arc_dataset.py --help
python dataset/build_sudoku_dataset.py --help
python dataset/build_maze_dataset.py --help
python pretrain.py --help
python <skill>/sub-skills/training-evaluation/scripts/check_training_env.py \
  --repo-root /path/to/HRM --require-cuda
```

`evaluate.py --help` is not safe because `evaluate.py` parses OmegaConf CLI
values into `EvalConfig` and requires `checkpoint`.

## Common failure routing

| Symptom | Read next |
|---|---|
| Missing `.npy` files, invalid `dataset.json`, token range errors, or no training batches | `sub-skills/data-preparation/references/troubleshooting.md` |
| FlashAttention import failure, `adam_atan2_backend` missing, bad `module@class` identifier, or model config confusion | `sub-skills/model-architecture/references/troubleshooting.md` |
| W&B login issues, Hydra override errors, checkpoint/evaluation mismatch, or ARC prediction shard problems | `sub-skills/training-evaluation/references/troubleshooting.md` |

## Network and storage caution

Full dataset creation can clone submodules, download Hugging Face CSVs, and
write large augmented NumPy arrays. Full training can run for minutes to many
hours depending on task and GPU count. Ask for explicit permission before
running network-heavy, storage-heavy, or long training commands as verification.
