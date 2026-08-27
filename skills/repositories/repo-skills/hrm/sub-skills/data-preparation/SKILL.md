---
name: data-preparation
description: "Prepare, validate, and visualize HRM ARC, Sudoku, and Maze puzzle
  datasets in the repository's shared NumPy layout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# HRM Data Preparation

Use this sub-skill when the task is to create, inspect, validate, or visualize
Hierarchical Reasoning Model (HRM) datasets for ARC, Sudoku, or Maze workflows.
The original repo builders produce a shared directory layout consumed by
`PuzzleDataset` and by `pretrain.py`/`evaluate.py`.

## When to use

- The user asks to build ARC-AGI, ARC-AGI-2, ConceptARC, Sudoku Extreme, or Maze
  datasets for HRM.
- The task names `dataset/build_arc_dataset.py`, `build_sudoku_dataset.py`,
  `build_maze_dataset.py`, `PuzzleDataset`, `PuzzleDatasetMetadata`,
  `identifiers.json`, or `all__inputs.npy` style files.
- A training or evaluation run fails before model execution because dataset
  paths, metadata, `.npy` arrays, split/subset names, token ranges, or puzzle
  index arrays are wrong.
- The user wants a browser visualizer for converted puzzle folders.

## Route map

1. Read [references/data-formats.md](references/data-formats.md) for the exact
   shared dataset directory structure, metadata fields, array meanings, and
   validation invariants.
2. Read [references/workflows.md](references/workflows.md) for ARC, Sudoku,
   Maze, and visualization command recipes, including network/submodule
   prerequisites and safe bounded variants.
3. Use [references/troubleshooting.md](references/troubleshooting.md) when a
   builder cannot find raw data, Hugging Face downloads fail, token ranges look
   invalid, or `PuzzleDataset` yields no batches.
4. Run [scripts/validate_dataset_layout.py](scripts/validate_dataset_layout.py)
   against a converted dataset before long training or evaluation.
5. Use [scripts/run_dataset_builder.py](scripts/run_dataset_builder.py) when a
   future task needs a wrapper that forwards arguments to an HRM checkout from
   any current working directory.
6. Open [scripts/puzzle_visualizer.html](scripts/puzzle_visualizer.html) in a
   browser for local inspection of generated puzzle folders. The required
   `npyjs` asset is bundled under `scripts/assets/`.

## Core workflow

```bash
# ARC-1 from initialized ARC-AGI + ConceptARC submodules
python dataset/build_arc_dataset.py

# ARC-2 from ARC-AGI-2 raw data
python dataset/build_arc_dataset.py \
  --dataset-dirs dataset/raw-data/ARC-AGI-2/data \
  --output-dir data/arc-2-aug-1000

# Sudoku 1K augmented demo
python dataset/build_sudoku_dataset.py \
  --output-dir data/sudoku-extreme-1k-aug-1000 \
  --subsample-size 1000 \
  --num-aug 1000

# Maze 30x30 hard 1K
python dataset/build_maze_dataset.py --output-dir data/maze-30x30-hard-1k
```

After building, validate the shared layout before training:

```bash
python <skill>/sub-skills/data-preparation/scripts/validate_dataset_layout.py \
  data/sudoku-extreme-1k-aug-1000 --splits train test
```

Replace `<skill>` with the root of this generated skill directory. The helper is
self-contained; it does not need the original HRM checkout unless you are
running the original builder scripts.

## Boundaries

- This sub-skill owns dataset builders, converted layout, schema validation,
  and local visualization.
- Use `model-architecture` for HRM ACT v1 config fields, losses, model class
  routing, FlashAttention layers, and sparse puzzle embeddings.
- Use `training-evaluation` for `pretrain.py`, `evaluate.py`, checkpoints,
  W&B, CUDA training, and ARC prediction post-processing.
- Do not run full dataset downloads or raw-data submodule cloning unless the
  user has accepted network and storage costs. Use tiny fixtures and the
  bundled validator for bounded checks.

## Validation expectations

- Builder `--help` commands are safe and should list the documented options.
- Full Sudoku and Maze conversion require network access to Hugging Face
datasets.
- Full ARC conversion requires the ARC/ConceptARC raw-data submodules or an
  equivalent local directory.
- Converted train/test split directories must contain `dataset.json` plus
  `<subset>__inputs.npy`, `<subset>__labels.npy`,
  `<subset>__puzzle_identifiers.npy`, `<subset>__puzzle_indices.npy`, and
  `<subset>__group_indices.npy` for each subset in metadata `sets`.
