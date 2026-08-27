# HRM Dataset Formats

## Purpose

Read this when validating or creating converted datasets for HRM training and
evaluation. ARC, Sudoku, and Maze builders all emit the same high-level layout
consumed by `PuzzleDataset`.

## Directory layout

```text
<dataset-root>/
  identifiers.json                 # puzzle id lookup, mostly for ARC/visualization
  train/
    dataset.json
    <subset>__inputs.npy
    <subset>__labels.npy
    <subset>__puzzle_identifiers.npy
    <subset>__puzzle_indices.npy
    <subset>__group_indices.npy
  test/
    dataset.json
    <subset>__inputs.npy
    <subset>__labels.npy
    <subset>__puzzle_identifiers.npy
    <subset>__puzzle_indices.npy
    <subset>__group_indices.npy
```

`dataset.json` is the serialized `PuzzleDatasetMetadata` pydantic model:

| Field | Meaning |
|---|---|
| `pad_id` | Token used for input padding. |
| `ignore_label_id` | Label token converted to `-100` before loss computation; often `0`. |
| `blank_identifier_id` | Puzzle identifier used for padded examples. |
| `vocab_size` | Number of token ids allowed in input/label arrays. Valid tokens are `0 <= id < vocab_size`. |
| `seq_len` | Width of every row in `inputs` and `labels`. |
| `num_puzzle_identifiers` | Size of the puzzle-id lookup table. |
| `total_groups` | Number of training groups; must equal `len(group_indices) - 1`. |
| `mean_puzzle_examples` | Average examples per puzzle, used to estimate total training steps. |
| `sets` | Subset names available in the split, such as `all`. |

## Array roles

- `<subset>__inputs.npy`: 2D integer array `[num_examples, seq_len]`.
- `<subset>__labels.npy`: same shape as inputs.
- `<subset>__puzzle_identifiers.npy`: 1D integer array with one id per puzzle.
- `<subset>__puzzle_indices.npy`: monotone offsets into examples. It has length
  `num_puzzles + 1`, starts at 0, and ends at `num_examples`.
- `<subset>__group_indices.npy`: monotone offsets into puzzles. It has length
  `num_groups + 1`, starts at 0, and ends at `num_puzzles`.

`PuzzleDataset` uses `group_indices` to sample groups, then samples one puzzle
inside the group, and finally samples examples inside that puzzle. If there are
fewer examples than `global_batch_size`, the final short training batch is
dropped. Tiny fixture tests therefore need enough examples to fill the requested
batch.

## Task-specific encoding

### ARC / ConceptARC

- `seq_len = 30 * 30 = 900`.
- `vocab_size = 12` with `0 = PAD`, `1 = EOS`, and `2..11 = ARC colors 0..9`.
- ARC training applies color permutations, dihedral transforms, and
  translational augmentation. Augmented identifiers include suffixes such as
  `_t3_0123456789` so prediction post-processing can reverse them.
- `identifiers.json` maps numeric ids back to puzzle names and augmentation ids.

### Sudoku

- `seq_len = 81`.
- `vocab_size = 11` with `0 = PAD`, `1..10 = digits 0..9` after the builder adds
  1 to raw digits.
- `ignore_label_id = 0`, so blanks are ignored in the loss after conversion to
  `-100` in `PuzzleDataset`.
- Optional augmentation shuffles digits, transposes, and permutes Sudoku bands,
  rows, stacks, and columns while preserving valid solutions.

### Maze

- `seq_len` is inferred from the square grid length in the CSV.
- `vocab_size = len("# SGo") + 1 = 6`, with `0 = PAD` and the remaining tokens
  encoding wall, space, start, goal, and path/output characters.
- Optional train augmentation applies the eight dihedral transforms.

## Recommended validation

Use the bundled validator before launching a long run:

```bash
python sub-skills/data-preparation/scripts/validate_dataset_layout.py \
  <dataset-root> --splits train test
```

For a partial dataset, pass only the existing split:

```bash
python sub-skills/data-preparation/scripts/validate_dataset_layout.py \
  <dataset-root> --splits train --subsets all --json
```

A valid layout only proves schema consistency. It does not prove that the raw
benchmark acquisition was complete or that the dataset is large enough for the
intended HRM hyperparameters.
