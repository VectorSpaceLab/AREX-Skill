# Token and QA API Reference

## Public imports

```python
from simpletransformers.ner import NERArgs, NERModel
from simpletransformers.question_answering import QuestionAnsweringArgs, QuestionAnsweringModel
```

## Constructors

```python
NERModel(
    model_type,
    model_name,
    labels=None,
    weight=None,
    args=None,
    use_cuda=True,
    cuda_device=-1,
    onnx_execution_provider=None,
    **kwargs,
)

QuestionAnsweringModel(
    model_type,
    model_name,
    args=None,
    use_cuda=True,
    cuda_device=-1,
    **kwargs,
)
```

Use `labels` to declare a custom NER label list when the default labels are insufficient. Use `weight` for class weighting where the selected model supports it. Always set `use_cuda=False` for CPU smoke runs.

## Main methods

| Model | Method | Input | Return |
|---|---|---|---|
| `NERModel` | `train_model(train_data)` | DataFrame or CoNLL file path | trains and writes outputs unless disabled |
| `NERModel` | `eval_model(eval_data)` | DataFrame or CoNLL file path | `(result, model_outputs, predictions)` |
| `NERModel` | `predict(to_predict, split_on_space=True)` | list of strings or list of token lists | `(predictions, raw_outputs)` |
| `QuestionAnsweringModel` | `train_model(train_data)` | SQuAD-style list or JSON/JSONL path | trains QA model |
| `QuestionAnsweringModel` | `eval_model(eval_data)` | SQuAD-style list or JSON path | `(result, texts)` style output |
| `QuestionAnsweringModel` | `predict(to_predict)` | list of contexts with `qas` containing `id` and `question` | predictions and n-best style text outputs |

## Args that matter often

- Shared: `max_seq_length`, `train_batch_size`, `eval_batch_size`, `num_train_epochs`, `learning_rate`, `output_dir`, `cache_dir`, `no_save`, `overwrite_output_dir`, `reprocess_input_data`, `use_multiprocessing`, `manual_seed`, `silent`.
- NER: `labels_list`, `classification_report`, `lazy_loading`, `lazy_loading_start_line`, `onnx`, `special_tokens_list`.
- QA: `doc_stride`, `max_query_length`, `max_answer_length`, `n_best_size`, `null_score_diff_threshold`, `lazy_loading`, and early-stopping metric defaults that maximize `correct` rather than minimize loss.

## Model-family notes

NER and QA use Hugging Face token classification and QA backbones through Simple Transformers. Common families in docs/tests include `bert`, `roberta`, `longformer`, `bigbird`, and related Transformer model types. Exact availability is controlled by installed Transformers and local model cache.

For LayoutLM-style token tasks, validate bounding boxes just as carefully as labels. For Longformer/BigBird, check sequence length and global attention settings before assuming a data problem.
