# Classification API Reference

## When to read

Read this when choosing a Simple Transformers classification model class, constructor arguments, or method return shape. It summarizes public API facts from Simple Transformers 0.70.8 source and package-inspection evidence.

## Public imports

```python
from simpletransformers.classification import (
    ClassificationArgs,
    ClassificationModel,
    MultiLabelClassificationArgs,
    MultiLabelClassificationModel,
    MultiModalClassificationArgs,
    MultiModalClassificationModel,
)
```

## Constructors

```python
ClassificationModel(
    model_type,
    model_name,
    tokenizer_type=None,
    tokenizer_name=None,
    num_labels=None,
    weight=None,
    args=None,
    use_cuda=True,
    cuda_device=-1,
    onnx_execution_provider=None,
    global_attention_fn=None,
    **kwargs,
)

MultiLabelClassificationModel(
    model_type,
    model_name,
    num_labels=None,
    pos_weight=None,
    args=None,
    use_cuda=True,
    cuda_device=-1,
    global_attention_fn=None,
    **kwargs,
)

MultiModalClassificationModel(
    model_type,
    model_name,
    multi_label=False,
    label_list=None,
    num_labels=None,
    pos_weight=None,
    args=None,
    use_cuda=True,
    cuda_device=-1,
    **kwargs,
)
```

Use `args` as a dict or a task-specific dataclass. For repeatable smoke tests, set `use_cuda=False`, `no_save=True`, `overwrite_output_dir=True`, and a short `max_seq_length`. For real training, use a deliberate writable `output_dir` and let the user decide checkpoint retention.

## Main methods

| Method | Applies to | Inputs | Return shape / notes |
|---|---|---|---|
| `train_model(train_data, ...)` | all classification classes | DataFrame, lazy file, or supported dataset shape | Trains and writes to `output_dir` unless `no_save=True`. |
| `eval_model(eval_data, ...)` | all | same schema family as train | Usually `(result, model_outputs, wrong_predictions)` for classification/multilabel/multimodal. |
| `predict(to_predict, ...)` | all | list of strings, list pairs, LayoutLM box tuples/lists, or multimodal rows | Usually `(predictions, raw_outputs)`. |
| `rerank(query, passages)` | `ClassificationModel` | cross-encoder query/passages | Scores/ranks passages; use retrieval sub-skill for dense retrieval. |
| `convert_to_onnx(output_dir, ...)` | `ClassificationModel`/`NERModel` style branches | installed ONNX/ONNX Runtime dependencies | Optional export path; treat converter failures as dependency/config issues. |

## Useful args

Shared `ModelArgs` fields include `output_dir`, `best_model_dir`, `cache_dir`, `dataset_cache_dir`, `max_seq_length`, `train_batch_size`, `eval_batch_size`, `num_train_epochs`, `learning_rate`, `scheduler`, `manual_seed`, `use_multiprocessing`, `use_hf_datasets`, `reprocess_input_data`, `overwrite_output_dir`, `no_save`, `save_best_model`, `save_model_every_epoch`, `evaluate_during_training`, `wandb_project`, and `silent`.

Classification-specific fields include:

- `regression`: use with continuous labels and `num_labels=1`.
- `sliding_window` and `stride`: long single-text classification; not a universal fallback for all model families.
- `labels_list` / `labels_map`: custom label ordering and mapping.
- `lazy_loading`, `lazy_delimiter`, `lazy_text_column`, `lazy_labels_column`, `lazy_text_a_column`, `lazy_text_b_column`: file-backed classification datasets.
- `onnx`: use an exported ONNX model where supported.
- `as_reranker`, `pairwise_reranking_format`, `tourney_mode`, `tie_value`: cross-encoder reranking paths.
- `threshold` on `MultiLabelClassificationArgs`: binary decision cutoff for each label.
- `text_label`, `labels_label`, `images_label`, `image_type_extension` on `MultiModalClassificationArgs`: multimodal column naming.

## Model-family notes

Simple Transformers delegates actual model classes to Hugging Face Transformers. Common families in source/docs/tests include `bert`, `roberta`, `distilbert`, `albert`, `xlnet`, `xlm`, `xlmroberta`, `camembert`, `flaubert`, `electra`, `longformer`, `bigbird`, `mobilebert`, `deberta`, `bertweet`, `layoutlm`, and `layoutlmv2`, but exact availability depends on installed Transformers version.

For multimodal classification, source evidence restricts the MMBT path to BERT-style configuration. If MMBT classes are unavailable in the installed Transformers version, treat multimodal import errors as an optional dependency/version compatibility problem rather than a data error.

## Compatibility warning

Simple Transformers 0.70.8 has public metadata requiring `transformers>=4.31.0`, but runtime inspection found that some classification imports can fail under modern Transformers because aliases such as `XLNetSequenceSummary`, `XLMSequenceSummary`, or `FlaubertSequenceSummary` are no longer present where the package imports them. If a user sees these errors, do not debug the dataset first; read [troubleshooting](troubleshooting.md#transformers-compatibility-import-errors).
