# API Reference: Training and Fine-tuning

Import the training entry points from `text2vec`:

```python
from text2vec import CosentModel, SentenceBertModel, BertMatchModel, BgeModel
from text2vec import load_text_matching_train_data, load_text_matching_test_data
from text2vec import load_cosent_train_data, load_bge_train_data
```

## Model constructors

```python
CosentModel(
    model_name_or_path: str = "hfl/chinese-macbert-base",
    encoder_type: str = "FIRST_LAST_AVG",
    max_seq_length: int = 128,
    device: str = None,
)

SentenceBertModel(
    model_name_or_path: str = "hfl/chinese-macbert-base",
    encoder_type: str = "MEAN",
    max_seq_length: int = 128,
    num_classes: int = 2,
    device: str = None,
)

BertMatchModel(
    model_name_or_path: str = "bert-base-chinese",
    max_seq_length: int = 128,
    num_classes: int = 2,
    encoder_type = None,
)

BgeModel(
    model_name_or_path: str = "BAAI/bge-large-zh-noinstruct",
    encoder_type: str = "MEAN",
    max_seq_length: int = 32,
    passage_max_len: int = 128,
    device: str = None,
)
```

Notes:
- `CosentModel`, `SentenceBertModel`, and `BgeModel` use the same sentence encoder backend and `EncoderType` names as embedding inference.
- `BertMatchModel` is a cross-encoder pair classifier. Its `encoder_type` argument is accepted for API symmetry, but the classifier does not use sentence-pooling in the same way as the embedding models.
- For `BgeModel`, `max_seq_length` is the query max length; `passage_max_len` separately controls positives and negatives.
- `SentenceBertModel` and `BertMatchModel` default to `num_classes=2`; NLI-style three-class data needs `num_classes=3` at construction time.

## `train_model` signatures

The three text-matching trainers share this signature:

```python
CosentModel.train_model(
    train_file: str = None,
    output_dir: str = None,
    eval_file: str = None,
    verbose: bool = True,
    batch_size: int = 32,
    num_epochs: int = 1,
    weight_decay: float = 0.01,
    seed: int = 42,
    warmup_ratio: float = 0.05,
    lr: float = 2e-5,
    eps: float = 1e-6,
    gradient_accumulation_steps: int = 1,
    max_grad_norm: float = 1.0,
    max_steps: int = -1,
    use_hf_dataset: bool = False,
    hf_dataset_name: str = "STS-B",
    save_model_every_epoch: bool = True,
    bf16: bool = False,
    data_parallel: bool = False,
)

SentenceBertModel.train_model(<same arguments as above>)
BertMatchModel.train_model(<same arguments as above>)
```

`BgeModel.train_model` adds BGE contrastive-training controls and uses different optimizer defaults:

```python
BgeModel.train_model(
    train_file: str = None,
    output_dir: str = None,
    eval_file: str = None,
    verbose: bool = True,
    batch_size: int = 32,
    num_epochs: int = 1,
    weight_decay: float = 0.0,
    seed: int = 42,
    warmup_ratio: float = 0.05,
    lr: float = 1e-5,
    eps: float = 1e-6,
    gradient_accumulation_steps: int = 1,
    max_grad_norm: float = 1.0,
    max_steps: int = -1,
    use_hf_dataset: bool = False,
    hf_dataset_name: str = "",
    save_model_every_epoch: bool = True,
    bf16: bool = False,
    data_parallel: bool = False,
    train_group_size: int = 8,
    temperature: float = 1.0,
    normalize_embeddings: bool = False,
)
```

All four `train_model` methods return `(global_step, training_details)`. They create `output_dir`, save checkpoints under `checkpoint-<step>-epoch-<n>` when requested, write `training_progress_scores.csv`, and save the best evaluated model at `output_dir`.

## Data loader helpers

| Helper | Input | Return shape / behavior |
|---|---|---|
| `load_text_matching_train_data(path)` | TSV or JSONL text-matching pairs | List of `(text_a, text_b, label_int)`. Missing files return `[]`. JSONL rows without supported field pairs are skipped. File paths containing `STS` convert train labels with `int(score > 2.5)`. |
| `load_text_matching_test_data(path)` | TSV or JSONL text-matching pairs | List of `(text_a, text_b, label_int)`. Missing files return `[]`. Test labels are not STS-binarized. |
| `load_cosent_train_data(path)` | TSV or JSONL pair-score rows | List of flattened `(text, score_float_or_binary)` rows: every valid input pair contributes two training rows. Missing files return `[]`. File paths containing `STS` convert labels with `int(score > 2.5)`. |
| `load_bge_train_data(train_file)` | JSONL file, directory of JSON files, or Hugging Face dataset name | A `datasets.Dataset` when loading succeeds, otherwise `[]`. Local JSON rows must provide `query`, `pos`, and `neg`. |

Dataset wrappers used internally:
- `TextMatchingTrainDataset(tokenizer, data, max_len=64)` and `TextMatchingTestDataset(tokenizer, data, max_len=64)` tokenize two independent sentences for SBERT-style training/evaluation.
- `CosentTrainDataset(tokenizer, data, max_len=64)` tokenizes flattened `(text, score)` CoSENT rows.
- `BgeTrainDataset(tokenizer, data_file_or_name, query_max_len=32, passage_max_len=128, train_group_size=8)` samples one positive and `train_group_size - 1` negatives per query.

## Dataset-source modes

- `use_hf_dataset=True` ignores `train_file` and loads the named Hugging Face dataset path used by the package.
- `use_hf_dataset=False` uses `train_file`; provide `eval_file` for validation and progress metrics.
- For BGE, `use_hf_dataset=True` can load a dataset name into `BgeTrainDataset`; local training expects BGE JSONL or a directory of JSON files.
