# Evaluator Troubleshooting

## Missing Optional Packages

Symptoms:

- `ImportError` mentions `transformers` when calling `evaluator(...)`.
- `ImportError` mentions `scipy>=1.7.1` when constructing an evaluator.
- Transformers warns that no PyTorch, TensorFlow, or Flax backend is installed.

Fix:

- Install evaluator extras or equivalent dependencies for the target environment.
- Treat `transformers` and `scipy` as required for evaluator construction.
- Install a model backend before running real transformer pipelines; without one, only lightweight inspection and non-model code paths are safe.

## Wrong Task Name

Symptoms:

- `KeyError: Unknown task ... available tasks are: ...`.
- A task exists in transformers but not in evaluate's evaluator registry.

Fix:

- Run `python skills/evaluate/sub-skills/evaluator-pipelines/scripts/inspect_evaluator_tasks.py`.
- Use one of the supported names exactly: `text-classification`, `image-classification`, `question-answering`, `token-classification`, `text-generation`, `text2text-generation`, `summarization`, `translation`, `automatic-speech-recognition`, or `audio-classification`.
- `sentiment-analysis` may work as a transformers alias for text classification, but prefer `text-classification` in public examples.

## Invalid Dataset Columns

Symptoms:

- `ValueError: Invalid input_column ... The dataset contains the following columns: ...`.
- Metrics fail because references/predictions have incompatible shapes or label types.

Fix:

- Inspect `dataset.column_names` and pass explicit `input_column`, `label_column`, or task-specific names.
- For paired text classification, pass `second_input_column`.
- For QA, confirm columns for `question`, `context`, `id`, and answer dictionaries.
- For token classification, both input and label columns must be sequences; offset-style label datasets are not supported directly.
- For generation tasks, ensure metric inputs match the metric: text generation sends generated strings as `data`, while text2text/summarization/translation compare `predictions` to `references`.

## Label Mapping Mismatch

Symptoms:

- Accuracy is zero or implausibly low.
- Metric errors show string predictions but numeric references, or vice versa.

Fix:

- Add `label_mapping` for classification tasks so pipeline output labels map to the dataset's reference values.
- For image/audio classifiers, use model config label mappings when available, but confirm direction: evaluator maps predicted pipeline label to reference label value.
- For token classification, prefer `Sequence(ClassLabel(...))` features or string label sequences; plain integer sequences without `ClassLabel` metadata are not implemented.

## Device Mismatch with Prebuilt Pipeline

Symptoms:

- `ValueError` says `device` suggests an accelerator but the prebuilt pipeline is on CPU.
- `ValueError` says the pipeline was instantiated on one device but another `device` was passed to `compute`.

Fix:

- If passing a prebuilt pipeline, set its device when constructing the pipeline and pass `device=None` to `compute(...)`.
- If you want evaluator-managed device placement, pass a model id/path or model object instead of a prebuilt pipeline.
- Use `device=-1` for CPU when constructing evaluator-managed pipelines.

## Incompatible Pipeline Task

Symptoms:

- `ValueError: Incompatible model_or_pipeline...`.

Fix:

- Ensure `pipe.task` matches the evaluator task.
- Translation pipelines are a special case: a pipeline task that starts with `translation` is accepted for the `translation` evaluator.
- Do not pass a text-generation pipeline to a text2text/summarization evaluator or a classifier pipeline to an image/audio evaluator.

## Token Classification Slow Tokenizer

Symptoms:

- `ValueError` says token classification supports only pipelines giving `start` indexes and got `None`.

Fix:

- Use a fast tokenizer-backed token classification pipeline.
- Confirm a smoke call returns token dictionaries with non-null `start` offsets before running the full dataset.

## SQuAD v1/v2 Confusion

Symptoms:

- Warning says SQuAD v2 data is being evaluated with `squad`.
- Warning says SQuAD v1 data is being evaluated with `squad_v2`.
- No-answer examples are scored incorrectly.

Fix:

- Pass `squad_v2_format=True` and `metric="squad_v2"` for datasets with empty answer lists.
- Pass `squad_v2_format=False` and `metric="squad"` for datasets where every question has an answer.
- Do not rely on auto-inference when the dataset slice might hide no-answer examples.

## Bootstrap Cost and SciPy Requirement

Symptoms:

- Runtime explodes after switching to `strategy="bootstrap"`.
- Import or compute errors mention scipy.
- Confidence intervals vary unexpectedly.

Fix:

- Use `strategy="simple"` for routine evaluation.
- For bootstrap smoke tests, use a small dataset slice and low `n_resamples`.
- Set `random_state` when comparing bootstrap outputs across runs.
- Remember bootstrap repeatedly calls the metric on resampled metric inputs; it does not rerun model inference, but it can still be expensive for complex metrics.

## Network, Model, and Dataset Download Constraints

Symptoms:

- Evaluation hangs or fails when loading a Hub model, metric, suite, or dataset.
- Offline CI fails even though local code imports.

Fix:

- Prefer preloaded `Dataset` objects and prebuilt local pipelines in offline or controlled environments.
- Use local model paths or already-cached models when passing `model_or_pipeline` as a string.
- Avoid `EvaluationSuite.load(...)` with a Hub id unless network access is expected; use a local suite path instead.
- Run the registry helper first because it does not download models or datasets.

## EvaluationSuite Args Problems

Symptoms:

- `TypeError` or `KeyError` while running a suite subtask.
- Later suite runs inherit unexpected `model_or_pipeline`, `data`, `subset`, or `split` values.

Fix:

- Set `args_for_task` to a dict for every `SubTask`; include task-specific metric, columns, and label mappings.
- Avoid sharing one mutable `args_for_task` dict across multiple subtasks.
- Remember the runner mutates `args_for_task` by injecting runtime fields before calling `compute(...)`.
- If using `data_preprocessor`, ensure `data` is a dataset name string because the runner loads by name before applying `map(...)`.
