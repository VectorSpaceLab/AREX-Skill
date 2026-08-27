# PyTorch Workflows

## Purpose

Read this when you want the exact command sequence for a PyTorch example.
These commands assume you are reading from the `sub-skills/pytorch-examples/`
sub-skill directory. Use the bundled wrapper at `scripts/run_workflow.py`
instead of trying to run the source scripts directly.

## How to run the helper

The helper understands two domains:

- `--domain vision` for SIGNS image classification.
- `--domain nlp` for named-entity recognition.

It defaults to a dry run. Add `--execute` to run the command after it prints the
resolved working directory and command line.

## Vision workflow

### Data layout

Expected input:

```text
<repo-root>/pytorch/vision/data/SIGNS/
  train_signs/
  test_signs/
```

Expected processed output:

```text
<repo-root>/pytorch/vision/data/64x64_SIGNS/
  train_signs/
  val_signs/
  test_signs/
```

The starter experiment directories under `pytorch/vision/experiments/` contain
`params.json` files you can copy or edit.

### Commands

Resize the SIGNS dataset:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain vision \
  --action build-dataset \
  --data-dir <repo-root>/pytorch/vision/data/SIGNS \
  --output-dir <repo-root>/pytorch/vision/data/64x64_SIGNS \
  --execute
```

Train an experiment:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain vision \
  --action train \
  --data-dir <repo-root>/pytorch/vision/data/64x64_SIGNS \
  --model-dir <repo-root>/pytorch/vision/experiments/base_model \
  --execute
```

Evaluate a checkpoint:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain vision \
  --action evaluate \
  --data-dir <repo-root>/pytorch/vision/data/64x64_SIGNS \
  --model-dir <repo-root>/pytorch/vision/experiments/base_model \
  --restore-file best \
  --execute
```

Search learning rates:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain vision \
  --action search-hyperparams \
  --data-dir <repo-root>/pytorch/vision/data/64x64_SIGNS \
  --parent-dir <repo-root>/pytorch/vision/experiments/learning_rate \
  --execute
```

Aggregate results:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain vision \
  --action synthesize-results \
  --parent-dir <repo-root>/pytorch/vision/experiments/learning_rate \
  --execute
```

### Notes

- `train.py` and `evaluate.py` expect a `params.json` in the selected model
  directory.
- `evaluate.py` uses `--restore-file` to choose which checkpoint to load.
- `train.py` turns CUDA on automatically when the installed torch build and host
  GPU support it.

## NLP workflow

### Data layout

Expected small dataset layout:

```text
<repo-root>/pytorch/nlp/data/small/
  train/
    sentences.txt
    labels.txt
  val/
    sentences.txt
    labels.txt
  test/
    sentences.txt
    labels.txt
```

Expected Kaggle layout before conversion:

```text
<repo-root>/pytorch/nlp/data/kaggle/ner_dataset.csv
```

After `build_kaggle_dataset.py`, the wrapper should leave the train/val/test
text splits under `data/kaggle/`.

The starter experiment directories under `pytorch/nlp/experiments/` contain
`params.json` files you can copy or edit.

### Commands

Convert the Kaggle CSV into text splits:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain nlp \
  --action build-kaggle-dataset \
  --execute
```

Build vocabularies:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain nlp \
  --action build-vocab \
  --data-dir <repo-root>/pytorch/nlp/data/small \
  --execute
```

Train an experiment:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain nlp \
  --action train \
  --data-dir <repo-root>/pytorch/nlp/data/small \
  --model-dir <repo-root>/pytorch/nlp/experiments/base_model \
  --execute
```

Evaluate a checkpoint:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain nlp \
  --action evaluate \
  --data-dir <repo-root>/pytorch/nlp/data/small \
  --model-dir <repo-root>/pytorch/nlp/experiments/base_model \
  --restore-file best \
  --execute
```

Search learning rates:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain nlp \
  --action search-hyperparams \
  --data-dir <repo-root>/pytorch/nlp/data/small \
  --parent-dir <repo-root>/pytorch/nlp/experiments/learning_rate \
  --execute
```

Aggregate results:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain nlp \
  --action synthesize-results \
  --parent-dir <repo-root>/pytorch/nlp/experiments/learning_rate \
  --execute
```

### Notes

- `build_vocab.py` writes `words.txt`, `tags.txt`, and `dataset_params.json`.
- `train.py` and `evaluate.py` require those generated files to exist first.
- `build_kaggle_dataset.py` expects the simple `ner_dataset.csv`, not the full
  `ner.csv` file.
- The data iterator pads sentences and labels to the longest example in each
  batch; mismatched token/label counts are usually a preprocessing bug.

## When to read this file

- You know the framework is PyTorch and need a concrete command.
- You need the expected data layout before launching a command.
- You want the right starter experiment directory or restore flag.
