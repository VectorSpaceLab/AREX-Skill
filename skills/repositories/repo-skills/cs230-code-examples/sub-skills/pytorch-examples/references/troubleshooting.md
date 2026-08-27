# PyTorch Troubleshooting

## Purpose

Read this when a PyTorch example command fails, the data layout is wrong, or a
checkpoint/config file is missing.

## Common issues

### Missing `params.json`

**Symptoms**
- `AssertionError: No json configuration file found ...`

**Likely cause**
- The selected experiment directory does not contain a starter config.

**Recovery**
- Use one of the starter directories under `pytorch/vision/experiments/` or
  `pytorch/nlp/experiments/`.
- Copy the existing `params.json` before changing hyperparameters.
- Re-run the helper in dry-run mode first:

```bash
python scripts/run_workflow.py --domain vision --action train --dry-run
```

### SIGNS dataset path is wrong

**Symptoms**
- `Couldn't find the dataset at ...`
- Resize or loader commands fail before any training starts.

**Likely cause**
- The source images are not under `data/SIGNS/train_signs` and
  `data/SIGNS/test_signs`.

**Recovery**
- Download the SIGNS dataset, place it under `data/SIGNS`, and rebuild the
  processed dataset into `data/64x64_SIGNS`.
- Confirm the vision workflow reference before re-running.

### Processed SIGNS split is missing

**Symptoms**
- Training or evaluation cannot find `train_signs`, `val_signs`, or
  `test_signs` under the processed output root.

**Likely cause**
- `build_dataset.py` was not run, or it wrote to a different output directory.

**Recovery**
- Re-run the build helper with the intended output directory.
- Make sure the output root contains the expected split names for the active
  framework.

### NER preprocessing files do not line up

**Symptoms**
- Assertion failures about sentence and label counts.
- Padding or iterator errors during training.

**Likely cause**
- The text files under `train/`, `val/`, or `test/` do not have matching token
  and label lines.

**Recovery**
- Rebuild the text splits with `build_kaggle_dataset.py`.
- Rebuild the vocabularies with `build_vocab.py` after the split is correct.
- Check that each sentence has the same number of tokens and tags.

### Kaggle CSV is the wrong file

**Symptoms**
- `ner_dataset.csv file not found` or unexpected parsing failures.

**Likely cause**
- The full Kaggle file `ner.csv` was downloaded instead of the simple
  `ner_dataset.csv`.

**Recovery**
- Download the simple dataset file and keep it at
  `pytorch/nlp/data/kaggle/ner_dataset.csv`.

### Checkpoint or metrics file is missing

**Symptoms**
- Evaluation cannot find `best.pth.tar`, `last.pth.tar`, or metric JSON files.

**Likely cause**
- Training never completed, or the model directory was changed between runs.

**Recovery**
- Re-run training with the correct `--model_dir`.
- Verify the helper points to the same experiment directory for train and
  evaluate.

### CUDA is available but not required

**Symptoms**
- The workflow silently uses the GPU on a CUDA-capable host.

**Likely cause**
- The example scripts set `params.cuda` from `torch.cuda.is_available()`.

**Recovery**
- Use the repo on a CPU-only environment when you want the portable path.
- Do not treat CUDA as required for the PyTorch example workflows.

## Next checks

- Use `python ../../scripts/check_env.py --frameworks pytorch` for a shared import
  check.
- Use `python scripts/run_workflow.py --domain ... --action ... --dry-run` to
  confirm the resolved command before executing it.
