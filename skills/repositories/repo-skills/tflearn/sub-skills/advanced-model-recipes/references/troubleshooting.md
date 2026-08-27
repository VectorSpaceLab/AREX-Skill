# Troubleshooting Advanced Recipes

Use this reference when an advanced recipe fails during import, graph construction, tiny validation, or adaptation from a long example.

## Import and Version Failures

| Signal | Likely cause | Fix |
|---|---|---|
| `ImportError` mentioning `tensorflow.python.util.nest.is_sequence` | TFLearn is being imported with a modern TensorFlow 2.x runtime where that internal symbol is gone. | Use a TensorFlow 1.15-compatible environment for these recipes. Do not patch recipe code as a smoke-test workaround. |
| TensorFlow protobuf descriptor errors during import | TensorFlow 1.15 is paired with protobuf 4.x. | Use protobuf `3.20.3` with TensorFlow 1.15. |
| `ModuleNotFoundError: tensorflow.contrib...` | The recipe uses TF1 contrib seq2seq, factorization, or tensor_forest APIs under TensorFlow 2.x. | Treat the recipe as TF1-only. Use a TF1-compatible runtime or skip that recipe with an explicit compatibility block. |
| Eager/graph behavior errors | TensorFlow 2 behavior is active. | Import `tensorflow.compat.v1 as tf`, call `tf.disable_v2_behavior()`, and use graph/session style. |

## Dataset Downloads and Network Access

Many recipe examples load MNIST, CIFAR-10, Oxford Flowers, IMDB, Shakespeare/city text, Atari environments, or UCI Adult data. They may download files, cache data in the working directory, or use old Python download APIs. For runtime skill validation:

- Do not run those dataset loaders by default.
- Replace them with tiny in-memory arrays that preserve rank, dtype, and label semantics.
- If the user explicitly requests real data, ask about network permission, cache location, expected duration, and optional dependencies first.
- Keep download failures separate from TFLearn graph failures in reports.

## Optional Dependency Failures

| Dependency signal | Recipe area | Action |
|---|---|---|
| `No module named scipy` | VAE plotting/grid helpers. | Skip plotting or install SciPy only if VAE plotting is required. |
| `No module named h5py` | HDF5 large-data examples. | Route detailed HDF5 work to `data-input-pipelines`; use NumPy for model smokes. |
| `No module named dask` | Dask large-array examples. | Route detailed Dask data work to `data-input-pipelines`; use NumPy for recipes. |
| `No module named pandas` | Wide/deep recommender. | Install pandas only for recommender preprocessing, or feed direct NumPy dictionaries. |
| `No module named gym`, Atari ROM/env errors, or `skimage` errors | RL Atari. | Do not install/run by default. Use dummy frame tensors for graph-only checks unless real RL interaction is requested. |
| Matplotlib backend/display errors or notebook magic errors | Autoencoder/GAN/VAE plots and spiral notebook. | Use noninteractive numeric assertions. If plots are required, use a noninteractive backend and avoid notebook magics in scripts. |

## Expensive Training, Hangs, and Side Effects

- Vision examples may request `n_epoch=50`, `100`, `200`, `500`, or `1000`.
- Sequence generators may train large 512-unit LSTMs for dozens of iterations.
- RL Atari is configured for very large step counts, multiple threads, environment rendering, and checkpoint loops.
- Notebook and plotting examples can block on display calls.

Safe adaptation checklist:

1. Reduce dataset to 4-16 samples.
2. Reduce hidden units/filters/recurrent units to 2-32.
3. Use `n_epoch=1` or `2`.
4. Use `batch_size <= len(fixture)`.
5. Set `snapshot_epoch=False` unless checkpointing is under test.
6. Set `tensorboard_verbose=0` unless summaries are under test.
7. Remove or replace plot/render/wait calls.
8. Write temporary artifacts only to a caller-approved or temporary directory.

## GPU Expectations

CPU backend is verified for graph construction, DNN training, `TrainOp`/`Trainer`, and safe synthetic smokes. GPU/CUDA is optional and affects performance only for these skill workflows. Do not claim GPU coverage from a CPU smoke. If the task requires GPU performance or placement, verify TensorFlow GPU availability in that runtime and report device placement separately.

## `SequenceGenerator` Failures

| Signal | Cause | Fix |
|---|---|---|
| `KeyError` during `generate` | `seq_seed` contains a character/word not present in `dictionary`. | Build the dictionary from the same text/word fixture used for training and choose a seed from that fixture. |
| Shape mismatch in generation input | `seq_seed` length does not equal `seq_maxlen` or dictionary size differs from model output units. | Set `seq_maxlen` consistently in data preparation, `input_data`, `SequenceGenerator`, and seed selection. Output units must equal `len(dictionary)`. |
| Division/log warnings or invalid probabilities | `temperature <= 0` or predicted probabilities contain zeros. | Use positive temperatures such as `0.5`, `1.0`, or `1.2`. Avoid `0.0`. |
| Generated text looks random | The smoke used tiny data/few epochs or the model is untrained. | For smoke tests, assert type/length and dictionary coverage, not quality. Increase data/epochs only when the user asks for actual generation quality. |
| Unexpected returned length | `generate(seq_length)` returns seed plus generated tokens. | Expect total length `seq_maxlen + seq_length` for strings or lists. |

## Estimator Caveats

- `tflearn.estimators` relies on TensorFlow 1.x contrib packages such as factorization and tensor_forest. It is not compatible with TensorFlow 2.x contrib removal.
- KMeans and forest wrappers create their own graph/session by default and can start queue runners internally.
- Always pass tiny 2-D arrays and set `max_steps` for smoke fits.
- Random forest classes are work-in-progress and may save checkpoints under the log directory during `fit`.
- If `n_features` or `n_classes` cannot be inferred, pass them explicitly.
- Do not use estimator examples as proof of neural-network DNN behavior; they are separate wrappers.

## Custom `TrainOp` / `Trainer` Problems

| Signal | Cause | Fix |
|---|---|---|
| `ValueError: Unknown Optimizer` from `TrainOp` | A string optimizer name was passed directly to `TrainOp`. | Pass a TensorFlow optimizer instance, e.g. `tf.train.GradientDescentOptimizer(...)`. Use `tflearn.regression` if you want string optimizers. |
| `Unknown Loss type` | Loss is not a TensorFlow tensor. | Build a scalar loss tensor before constructing `TrainOp`. |
| No variables update or wrong branch updates | `trainable_vars` is missing or too broad/narrow. | Retrieve scoped variables with `tflearn.get_layer_variables_by_scope` and inspect names before training. |
| Feed errors for multiple optimizers | `Trainer.fit` feed dicts do not align with train op order or missing placeholders. | Provide a list of feed dicts, one per `TrainOp`, or use dictionaries keyed by named TFLearn inputs/targets for `DNN.fit`. |
| Validation monitor errors | Monitor tensors are large, missing feeds, or not compatible with validation batches. | Use cheap scalar/reduction monitors and feed all placeholders required by the monitor in `val_feed_dicts`. |

## Recommender and Notebook Caveats

- Wide/deep recommender preprocessing expects continuous columns, categorical columns, a binary label, and optionally pandas category mapping. For tiny fixtures, build the required input dictionaries directly or create a minimal DataFrame with every categorical column present.
- Some old download code patterns are not Python 3-safe. Avoid them by using local fixtures.
- Notebook recipes include IPython magics and inline plotting. Convert only the graph/data pattern to a script; do not execute notebook magics in a runtime smoke.
