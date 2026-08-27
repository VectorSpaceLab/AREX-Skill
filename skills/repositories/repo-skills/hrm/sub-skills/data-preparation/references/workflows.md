# HRM Data Preparation Workflows

## ARC / ConceptARC

ARC conversion expects local raw-data directories. In the public HRM checkout
these are Git submodules:

```bash
git submodule update --init --recursive
python dataset/build_arc_dataset.py
```

Default ARC-1 inputs are:

- `dataset/raw-data/ARC-AGI/data`
- `dataset/raw-data/ConceptARC/corpus`

ARC-2 uses the ARC-AGI-2 directory instead:

```bash
python dataset/build_arc_dataset.py \
  --dataset-dirs dataset/raw-data/ARC-AGI-2/data \
  --output-dir data/arc-2-aug-1000
```

Important options verified from CLI help:

- `--dataset-dirs [TEXT ...]`: one or more ARC raw-data directories.
- `--output-dir TEXT`: target converted dataset root.
- `--seed INT`: NumPy seed for shuffling and augmentation, default `42`.
- `--num-aug INT`: number of unique color/dihedral augmentations per puzzle,
  default `1000`.

ARC conversion can be CPU-only but may be storage-heavy. Do not run it as a
smoke test unless raw data and output storage are explicitly available.

## Sudoku Extreme

Sudoku conversion downloads CSV files from a Hugging Face dataset repo. The
quick demo in the README uses 1,000 training examples with 1,000 augmentations:

```bash
python dataset/build_sudoku_dataset.py \
  --output-dir data/sudoku-extreme-1k-aug-1000 \
  --subsample-size 1000 \
  --num-aug 1000
```

Important options verified from CLI help:

- `--source-repo TEXT`: Hugging Face dataset repo, default
  `sapientinc/sudoku-extreme`.
- `--output-dir TEXT`: target converted dataset root, default
  `data/sudoku-extreme-full`.
- `--subsample-size INT`: train-only sample count.
- `--min-difficulty INT`: filter by rating/difficulty when present.
- `--num-aug INT`: train augmentation count per puzzle, default `0`.

## Maze

Maze conversion also downloads train/test CSV files from Hugging Face:

```bash
python dataset/build_maze_dataset.py --output-dir data/maze-30x30-hard-1k
```

Important options verified from CLI help:

- `--source-repo TEXT`: default `sapientinc/maze-30x30-hard-1k`.
- `--output-dir TEXT`: default `data/maze-30x30-hard-1k`.
- `--subsample-size INT`: train-only sample count.
- `--aug` / `--no-aug`: enable or disable eight dihedral train transforms.

## Browser visualization

The original repo provides a local browser visualizer. This skill bundles a
copy at `scripts/puzzle_visualizer.html` with its `assets/npyjs.js` parser. To
use it:

1. Open `sub-skills/data-preparation/scripts/puzzle_visualizer.html` in a
   browser.
2. Choose a converted dataset folder, such as `data/arc-aug-1000`.
3. Select split/subset and inspect groups, puzzles, inputs, and labels.

The visualizer is manual and browser-only; automated verification should check
that the HTML references the bundled `assets/npyjs.js` file.

## Safe bounded checks

Use these commands before launching expensive work:

```bash
python dataset/build_arc_dataset.py --help
python dataset/build_sudoku_dataset.py --help
python dataset/build_maze_dataset.py --help
python sub-skills/data-preparation/scripts/validate_dataset_layout.py <dataset-root>
```

Avoid full conversion when network, raw submodules, or output storage are not
available. In that case, create a tiny synthetic fixture and validate the shared
layout rather than pretending the benchmark build succeeded.
