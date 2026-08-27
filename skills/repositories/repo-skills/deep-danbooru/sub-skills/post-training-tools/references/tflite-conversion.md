# TensorFlow Lite conversion

## Exact CLI contract

The source command in DeepDanbooru 1.0.0 is:

```text
deepdanbooru conv2tflite \
  [--project-path PROJECT_DIR] \
  [--model-path MODEL_FILE] \
  [--save-path TFLITE_FILE] \
  [--optimize-default] \
  [--optimize-experimental-sparsity] \
  [--verbose]
```

These are the exact Click options:

- `--project-path`: an existing directory. It is used if no direct model is
  supplied.
- `--model-path`: an existing Keras model file. If both paths are provided,
  the direct model wins.
- `--save-path`: the output file path. The source function requires a non-empty
  value, but does not create its parent directory or validate that the result
  is a file.
- `--optimize-default`: requests `tf.lite.Optimize.DEFAULT`.
- `--optimize-experimental-sparsity`: requests
  `tf.lite.Optimize.EXPERIMENTAL_SPARSITY`.
- `--verbose`: prints loading/conversion/saving progress and enables verbose
  warnings. It does not repair an incompatible model.

At least one optimization flag is required by the command's guard. In the
exact source, `--optimize-default` is declared as an `is_flag` with
`default=True`, so normal Click invocation starts with default optimization
selected; there is no generated `--no-optimize-default` option. The
`optimization method must be specified` error remains relevant to a direct
callback/programmatic invocation or a changed Click context. Do not rely on
that default: explicitly record the intended optimization and use the bundled
preflight to reject an empty set.

The converter also rejects a call with neither model nor project:
`You must provide project path or model path.` It rejects an empty save path:
`You must provide a path to save tflite model.` Click path validation catches
missing project/model paths before the delegated function when the CLI is used.
Create the save parent before running because the source opens the output
path directly.

A conservative first run is:

```bash
mkdir -p artifacts
deepdanbooru conv2tflite \
  --model-path /path/to/model.keras \
  --save-path artifacts/model.tflite \
  --optimize-default --verbose
```

Run `deepdanbooru conv2tflite --help` first in the target environment. The
bundled `post_training_preflight.py` checks the path and optimization contract
without importing DeepDanbooru or loading a model.

## Python API

The source function is named, including its doubled `from`,
`convert_to_tflite_from_from_saved_model`:

```python
convert_to_tflite_from_from_saved_model(
    project_path: str,
    model_path: str,
    save_path: str,
    optimizations: list[tf.lite.Optimize] = [tf.lite.Optimize.DEFAULT],
    verbose: bool = False,
)
```

Pass `None` for an unused path and pass an explicit, non-empty optimization
list rather than relying on the mutable default:

```python
import tensorflow as tf
from deepdanbooru.commands import convert_to_tflite_from_from_saved_model

convert_to_tflite_from_from_saved_model(
    project_path=None,
    model_path="/path/to/model.keras",
    save_path="artifacts/model.tflite",
    optimizations=[tf.lite.Optimize.DEFAULT],
    verbose=True,
)
```

The implementation loads a direct model with `tf.keras.models.load_model`, or
loads the project-selected model with `dd.project.load_model_from_project`.
It creates `tf.lite.TFLiteConverter.from_keras_model(model)`, assigns the
provided optimization list, calls `convert()`, and writes the returned bytes.
The API does not independently reject an empty optimization list, create the
save parent, or prove the bytes are useful; the caller must enforce those
invariants.

## Artifact verification and backend boundary

Require all of the following:

1. The process exits successfully.
2. The output exists, is a regular file, and is non-empty (`test -s`).
3. When the same environment provides a TFLite interpreter, load the bytes and
   call `allocate_tensors()`. Record input/output shapes and dtypes and compare
   them with the consumer's preprocessing and postprocessing contract.

The `scripts/tflite_conversion_smoke.py` helper creates a deterministic tiny
Keras fixture, converts it, and checks the non-empty file and interpreter. It
never downloads weights or reads a DeepDanbooru checkout. It is a conversion
smoke test, not evidence that a full DeepDanbooru model or all delegates work.

Start with default optimization on CPU. Experimental sparsity can be combined
with default optimization, but it does not make a dense model sparse and may
expose unsupported operators. Preserve the source Keras model and retry
without sparsity when conversion fails. CPU TensorFlow is the required verified
backend. GPU speedups/delegates are optional and unverified; conversion success
is not GPU verification.

For prediction parity, tag correctness, and image preprocessing, follow
[Inference and evaluation](../../inference-evaluation/SKILL.md). If the
project-selected model is absent or cannot be loaded, route to
[Model training](../../model-training/SKILL.md).
