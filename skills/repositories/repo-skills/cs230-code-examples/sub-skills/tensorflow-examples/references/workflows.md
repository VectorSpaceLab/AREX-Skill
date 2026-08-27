# TensorFlow Workflows

## Purpose

Read this when you want the exact command sequence for a TensorFlow example.
These commands assume you are reading from the `sub-skills/tensorflow-examples/`
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
<repo-root>/tensorflow/vision/data/SIGNS/
  train_signs/
  test_signs/
```

Expected processed output:

```text
<repo-root>/tensorflow/vision/data/64x64_SIGNS/
  train_signs/
  dev_signs/
  test_signs/
```

The starter experiment directories under `tensorflow/vision/experiments/`
contain `params.json` files you can copy or edit.

### Commands

Resize the SIGNS dataset:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain vision \
  --action build-dataset \
  --data-dir <repo-root>/tensorflow/vision/data/SIGNS \
  --output-dir <repo-root>/tensorflow/vision/data/64x64_SIGNS \
  --execute
```

Train an experiment:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain vision \
  --action train \
  --data-dir <repo-root>/tensorflow/vision/data/64x64_SIGNS \
  --model-dir <repo-root>/tensorflow/vision/experiments/test \
  --execute
```

Evaluate a checkpoint:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain vision \
  --action evaluate \
  --data-dir <repo-root>/tensorflow/vision/data/64x64_SIGNS \
  --model-dir <repo-root>/tensorflow/vision/experiments/test \
  --restore-from best_weights \
  --execute
```

Search learning rates:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain vision \
  --action search-hyperparams \
  --data-dir <repo-root>/tensorflow/vision/data/64x64_SIGNS \
  --parent-dir <repo-root>/tensorflow/vision/experiments/learning_rate \
  --execute
```

Aggregate results:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain vision \
  --action synthesize-results \
  --parent-dir <repo-root>/tensorflow/vision/experiments/learning_rate \
  --execute
```

### Notes

- `train.py` expects `params.json` in the model directory and refuses to
  overwrite an existing `best_weights` tree unless you pass a restore path.
- `evaluate.py` uses `--restore-from`, which can point at either the
  `best_weights` directory or a specific checkpoint file.
- Vision preprocessing writes `dev_signs`, not `val_signs`.

## NLP workflow

### Data layout

Expected small dataset layout:

```text
<repo-root>/tensorflow/nlp/data/small/
  train/
    sentences.txt
    labels.txt
  dev/
    sentences.txt
    labels.txt
  test/
    sentences.txt
    labels.txt
```

Expected Kaggle layout before conversion:

```text
<repo-root>/tensorflow/nlp/data/kaggle/ner_dataset.csv
```

After `build_kaggle_dataset.py`, the wrapper should leave the train/dev/test
text splits under `data/kaggle/`.

The starter experiment directories under `tensorflow/nlp/experiments/`
contain `params.json` files you can copy or edit.

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
  --data-dir <repo-root>/tensorflow/nlp/data/small \
  --execute
```

Train an experiment:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain nlp \
  --action train \
  --data-dir <repo-root>/tensorflow/nlp/data/small \
  --model-dir <repo-root>/tensorflow/nlp/experiments/base_model \
  --execute
```

Evaluate a checkpoint:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain nlp \
  --action evaluate \
  --data-dir <repo-root>/tensorflow/nlp/data/small \
  --model-dir <repo-root>/tensorflow/nlp/experiments/base_model \
  --restore-from best_weights \
  --execute
```

Search learning rates:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain nlp \
  --action search-hyperparams \
  --data-dir <repo-root>/tensorflow/nlp/data/small \
  --parent-dir <repo-root>/tensorflow/nlp/experiments/learning_rate \
  --execute
```

Aggregate results:

```bash
python scripts/run_workflow.py \
  --repo-root <repo-root> \
  --domain nlp \
  --action synthesize-results \
  --parent-dir <repo-root>/tensorflow/nlp/experiments/learning_rate \
  --execute
```

### Notes

- `build_vocab.py` writes `words.txt`, `tags.txt`, and `dataset_params.json`.
- `train.py` and `evaluate.py` require those generated files to exist first.
- `build_kaggle_dataset.py` expects the simple `ner_dataset.csv`, not the full
  `ner.csv` file.
- The TensorFlow NER code uses TF1 session and lookup-table semantics, so a
  TensorFlow 1.15-compatible environment is required.

## When to read this file

- You know the framework is TensorFlow and need a concrete command.
- You need the expected data layout before launching a command.
- You want the right starter experiment directory, restore option, or overwrite
  guard behavior.
