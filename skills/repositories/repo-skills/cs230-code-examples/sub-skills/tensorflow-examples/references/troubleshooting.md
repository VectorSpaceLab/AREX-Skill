# TensorFlow Troubleshooting

## Purpose

Read this when a TensorFlow example command fails, the data layout is wrong, or
TensorFlow 1.15 cannot import cleanly.

## Common issues

### TensorFlow import fails with protobuf 4.x

**Symptoms**
- `TypeError: Descriptors cannot not be created directly`
- Import crashes inside `tensorflow_core` or `google.protobuf`

**Likely cause**
- `protobuf` is too new for TensorFlow 1.15.

**Recovery**
- Pin `protobuf` to a TensorFlow 1.15-compatible 3.20.x release.
- Re-run the shared environment helper after the pin change.

### TensorFlow 1.15 sees GPUs but cannot register them

**Symptoms**
- `Could not load dynamic library 'libcudart.so.10.0'`
- `Could not load dynamic library 'libcudnn.so.7'`
- `Skipping registering GPU devices...`

**Likely cause**
- The host has newer CUDA libraries, but TensorFlow 1.15 expects legacy CUDA
  10 / cuDNN 7 runtime libraries.

**Recovery**
- Use the CPU path for the example workflow when GPU execution is not required.
- If GPU execution is required, install the legacy runtime stack that matches
  TensorFlow 1.15.
- Do not treat a successful CPU import as proof that the GPU path works.

### Missing `params.json`

**Symptoms**
- `AssertionError: No json configuration file found ...`

**Likely cause**
- The selected experiment directory does not contain a starter config.

**Recovery**
- Use one of the starter directories under `tensorflow/vision/experiments/` or
  `tensorflow/nlp/experiments/`.
- Copy the existing `params.json` before changing hyperparameters.
- Re-run the helper in dry-run mode first:

```bash
python scripts/run_workflow.py --domain vision --action train --dry-run
```

### Vision data uses the wrong split name

**Symptoms**
- Evaluation cannot find `dev_signs`.

**Likely cause**
- The processed SIGNS directory was built with the PyTorch split naming or the
  wrong output directory.

**Recovery**
- Rebuild the dataset with the TensorFlow vision helper.
- Confirm the processed output contains `train_signs`, `dev_signs`, and
  `test_signs`.

### NER preprocessing files do not line up

**Symptoms**
- Assertion failures about sentence and label counts.
- Iterator or padding errors during training.

**Likely cause**
- The text files under `train/`, `dev/`, or `test/` do not have matching token
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
  `tensorflow/nlp/data/kaggle/ner_dataset.csv`.

### Overwrite guard blocks training

**Symptoms**
- `Weights found in model_dir, aborting to avoid overwrite`

**Likely cause**
- The experiment directory already contains `best_weights` and you did not pass
  a restore path.

**Recovery**
- Pass `--restore-from` or `--restore_dir` depending on the workflow.
- Or choose a fresh experiment directory before retraining.

### `tf.set_random_seed` deprecation warnings

**Symptoms**
- Warnings about `tf.set_random_seed` being deprecated.

**Likely cause**
- The example code is written against TensorFlow 1.x APIs.

**Recovery**
- Treat the warning as expected for this repository snapshot.
- Do not migrate the generated skill instructions to TensorFlow 2 semantics; the
  example code still depends on TF1 session and lookup-table behavior.

## Next checks

- Use `python ../../scripts/check_env.py --frameworks tensorflow` for a shared
  import check.
- Use `python scripts/run_workflow.py --domain ... --action ... --dry-run` to
  confirm the resolved command before executing it.
