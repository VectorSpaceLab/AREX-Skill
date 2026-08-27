# Evaluator API Reference

Evidence: `src/evaluate/evaluator/`, `src/evaluate/evaluation_suite/__init__.py`, `docs/source/base_evaluator.mdx`, `docs/source/evaluation_suite.mdx`, `tests/test_evaluator.py`, `tests/test_evaluation_suite.py`, and `tests/test_trainer_evaluator_parity.py`.

## Factory and Registry

```python
from evaluate import evaluator
from evaluate.evaluator import get_supported_tasks

tasks = get_supported_tasks()
task_evaluator = evaluator("text-classification")
```

`evaluator(task: str = None) -> Evaluator` validates the task against the evaluator registry and compatible `transformers` pipeline tasks, then returns the task-specific evaluator initialized with its default metric.

Supported task registry:

| Task | Evaluator class | Default metric | Key data columns |
| --- | --- | --- | --- |
| `text-classification` | `TextClassificationEvaluator` | `accuracy` | `input_column="text"`, `second_input_column=None`, `label_column="label"` |
| `image-classification` | `ImageClassificationEvaluator` | `accuracy` | `input_column="image"`, `label_column="label"` |
| `question-answering` | `QuestionAnsweringEvaluator` | `squad` | `question_column="question"`, `context_column="context"`, `id_column="id"`, `label_column="answers"` |
| `token-classification` | `TokenClassificationEvaluator` | `seqeval` | `input_column="tokens"`, `label_column="ner_tags"`, `join_by=" "` |
| `text-generation` | `TextGenerationEvaluator` | `word_count` | `input_column="text"`; no references column by default |
| `text2text-generation` | `Text2TextGenerationEvaluator` | `bleu` | `input_column="text"`, `label_column="label"`, `generation_kwargs=None` |
| `summarization` | `SummarizationEvaluator` | `rouge` | `input_column="text"`, `label_column="label"`, `generation_kwargs=None` |
| `translation` | `TranslationEvaluator` | `bleu` | `input_column="text"`, `label_column="label"`, `generation_kwargs=None` |
| `automatic-speech-recognition` | `AutomaticSpeechRecognitionEvaluator` | `wer` | `input_column="path"`, `label_column="sentence"`, `generation_kwargs=None` |
| `audio-classification` | `AudioClassificationEvaluator` | `accuracy` | `input_column="file"`, `label_column="label"` |

The `sentiment-analysis` pipeline alias is accepted and resolves to text classification through the transformers task alias machinery.

## Common Compute Arguments

Most evaluator `compute(...)` methods share these arguments:

| Argument | Meaning |
| --- | --- |
| `model_or_pipeline` | Model id/path, model object, prebuilt `Pipeline`, callable, or `None` for default pipeline construction. |
| `data` | Dataset name string or preloaded `datasets.Dataset`. |
| `subset` | Dataset config name when `data` is a string. |
| `split` | Dataset split or sliced split. If omitted for a dataset name, evaluator infers a split. |
| `metric` | Metric name string or preloaded `EvaluationModule`; `None` uses the task default metric. |
| `tokenizer` | Optional tokenizer when evaluator constructs a pipeline from a model. Ignored for prebuilt pipelines. |
| `feature_extractor` | Optional feature extractor for image/audio pipeline construction. Ignored for prebuilt pipelines. |
| `strategy` | `"simple"` or `"bootstrap"`. |
| `confidence_level` | Bootstrap confidence level, default `0.95`. |
| `n_resamples` | Bootstrap resamples, default `9999`. |
| `device` | `None` for inference, `-1` for CPU, non-negative integer for CUDA device when constructing a pipeline. |
| `random_state` | Optional scipy bootstrap random state. |

Return values include metric keys plus:

- `total_time_in_seconds`: elapsed pipeline inference time.
- `samples_per_second`: throughput over the pipeline output count.
- `latency_in_seconds`: per-sample latency estimate.

## Task-Specific Arguments

### Text Classification

```python
evaluator("text-classification").compute(
    model_or_pipeline=pipe,
    data=dataset,
    input_column="text",
    second_input_column=None,
    label_column="label",
    label_mapping={"NEGATIVE": 0, "POSITIVE": 1},
)
```

- Use `second_input_column` for paired inputs; evaluator passes data as `text` and `text_pair` to the pipeline.
- `label_mapping` maps pipeline output labels to metric reference values.
- Pipeline kwargs include `truncation=True`.

### Image Classification

```python
evaluator("image-classification").compute(
    model_or_pipeline=pipe,
    data=dataset,
    input_column="image",
    label_column="label",
    label_mapping=pipe.model.config.label2id,
)
```

- Predictions use the max-score label from each pipeline output list.
- `label_mapping` maps predicted class labels to reference values.

### Audio Classification

```python
evaluator("audio-classification").compute(
    model_or_pipeline=pipe,
    data=dataset,
    input_column="file",
    label_column="label",
    label_mapping=label_mapping,
)
```

- `input_column` may point to audio file paths or raw waveforms; decoded audio columns can be slow on large datasets.
- Audio file processing may require ffmpeg in the runtime environment.
- Predictions use the max-score label from each pipeline output list.

### Automatic Speech Recognition

```python
evaluator("automatic-speech-recognition").compute(
    model_or_pipeline=pipe,
    data=dataset,
    input_column="path",
    label_column="sentence",
    metric="wer",
    generation_kwargs={"max_new_tokens": 128},
)
```

- Pipeline predictions are read from each output's `text` field.
- `generation_kwargs`, when provided, update pipeline kwargs.
- Pipeline kwargs include `truncation=True` by default.

### Question Answering

```python
evaluator("question-answering").compute(
    model_or_pipeline=pipe,
    data=dataset,
    question_column="question",
    context_column="context",
    id_column="id",
    label_column="answers",
    metric="squad_v2",
    squad_v2_format=True,
)
```

- References are built as `{"id": id, "answers": answers}`.
- Predictions are built as `{"id": id, "prediction_text": answer}` and include `no_answer_probability` for SQuAD v2 format.
- If `squad_v2_format` is omitted, evaluator infers it by checking for empty answer text lists and logs a warning.
- Passing SQuAD v2 data with `squad`, or SQuAD v1 data with `squad_v2`, logs a metric-format warning.

### Token Classification

```python
evaluator("token-classification").compute(
    model_or_pipeline=pipe,
    data=dataset,
    input_column="tokens",
    label_column="ner_tags",
    join_by=" ",
    metric="seqeval",
)
```

- `input_column` and `label_column` must both be sequence features.
- Sequence `ClassLabel` references are converted to label strings before metric computation.
- Integer sequence references without `ClassLabel` metadata are not implemented.
- Dataset rows are joined into strings with `join_by` before pipeline calls.
- The pipeline must return token `start` offsets; slow tokenizers that produce `start=None` are rejected.
- Pipeline kwargs include `ignore_labels=[]`.

### Text Generation

```python
evaluator("text-generation").compute(
    model_or_pipeline=pipe,
    data=dataset,
    input_column="prompt",
    metric="word_count",
)
```

- This evaluator has no reference column by default; generated text is passed to the metric under `data`.
- Pipeline outputs are flattened from nested generated text lists.

### Text2Text, Summarization, Translation

```python
evaluator("summarization").compute(
    model_or_pipeline=pipe,
    data=dataset,
    input_column="article",
    label_column="highlights",
    metric="rouge",
    generation_kwargs={"max_new_tokens": 64},
)
```

- `text2text-generation` reads `generated_text` and defaults to `bleu`.
- `summarization` reads `summary_text` and defaults to `rouge`.
- `translation` reads `translation_text` and defaults to `bleu`.
- `generation_kwargs`, when provided, update pipeline kwargs; default pipeline kwargs include `truncation=True`.

## EvaluationSuite API

```python
from evaluate import EvaluationSuite
from evaluate.evaluation_suite import SubTask

suite = EvaluationSuite.load("path-or-hub-id")
results = suite.run(model_or_pipeline)
```

`SubTask(task_type, data=None, subset=None, split=None, data_preprocessor=None, args_for_task=None)` validates:

| Field | Requirement |
| --- | --- |
| `task_type` | `str`; must name a supported evaluator task when run. |
| `data` | `datasets.Dataset` or dataset name `str`. |
| `subset` | Optional `str`. |
| `split` | Optional `str`. |
| `data_preprocessor` | Optional callable applied through `Dataset.map(...)`. |
| `args_for_task` | Dict of evaluator kwargs such as `metric`, columns, and label mappings. |

`EvaluationSuite.load(...)` loads a suite module by local path or Hub id, imports a concrete class named `Suite`, and instantiates it with the path stem as the suite name. `EvaluationSuite.run(model_or_pipeline)` asserts the suite is nonempty, creates a task evaluator for every `SubTask`, runs `compute(...)`, and returns all result dictionaries.

## Optional Dependencies

Evaluator usage requires `transformers` and `scipy`. Actual model execution through transformers also requires a backend such as PyTorch, TensorFlow, or Flax for most real models. If no backend is installed, registry inspection can still work, but model pipeline execution will fail or warn until a compatible backend is installed.
