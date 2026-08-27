# Protein API Reference

This reference orients future agents to PaddleHelix protein tokenizer and sequence model APIs. Import model classes only in environments with compatible PaddlePaddle installed; tokenizer inspection is lighter weight but still belongs to the `pahelix` package.

## ProteinTokenizer

Import path:

```python
from pahelix.utils.protein_tools import ProteinTokenizer
```

Core methods and constants:

| API | Purpose |
| --- | --- |
| `ProteinTokenizer.vocab` | Ordered token-to-id mapping with special tokens and uppercase residue symbols |
| `tokenize(sequence)` | Splits a sequence string into individual characters |
| `convert_token_to_id(token)` | Returns token id, or `<unk>` id `4` for unknown tokens |
| `convert_tokens_to_ids(tokens)` | Converts a token list to ids |
| `gen_token_ids(sequence)` | Prepends `<cls>`, appends `<sep>`, and converts the sequence to ids |
| `padding_token_id`, `mask_token_id`, `class_token_id`, `seperate_token_id`, `unknown_token_id` | Special-token ids used by dataloaders and models |

Minimal usage:

```python
tokenizer = ProteinTokenizer()
ids = tokenizer.gen_token_ids("MKT")
# [2, 16, 14, 23, 3]
```

Behavior to remember:

- The tokenizer does no biological validation and no case normalization.
- In-vocabulary ambiguous symbols include `B`, `O`, `U`, `X`, and `Z`.
- Unknown characters map to id `4`, so validation should warn rather than assume the model will reject them.

## Sequence Model Family

Import path:

```python
from pahelix.model_zoo.protein_sequence_model import ProteinEncoderModel, ProteinModel, ProteinCriterion
```

Class orientation:

| Class | Role |
| --- | --- |
| `LstmEncoderModel` | Bidirectional LSTM encoder selected by `model_type: "lstm"` |
| `TransformerEncoderModel` | Transformer encoder selected by `model_type: "transformer"` |
| `ResnetEncoderModel` | 1D residual CNN encoder selected by `model_type: "resnet"` |
| `ProteinEncoderModel` | Factory wrapper that chooses the encoder from `model_config` |
| `ProteinModel` | Adds the task head from `model_config.task` |
| `ProteinCriterion` | Selects cross-entropy for classification/pretraining or MSE for regression |

Task head selection:

| `model_config.task` | Head class | Prediction shape |
| --- | --- | --- |
| `pretrain` | `PretrainTaskModel` | per-token vocabulary logits |
| `seq_classification` | `SeqClassificationTaskModel` | per-token class logits |
| `classification` | `ClassificationTaskModel` | per-sequence class logits using the first encoder token |
| `regression` | `RegressionTaskModel` | per-sequence scalar prediction using the first encoder token |

Model configuration keys used by the source model code:

- Encoder choice: `model_type` (`transformer`, `lstm`, `resnet`).
- Shared dimensions: `emb_dim`, `hidden_size`, `n_layers`.
- Transformer-specific: `n_heads`.
- ResNet-specific: `kernel_size`.
- Task-specific: `task`, `class_num`, `label_name`.

## Dataloader and Metrics Orientation

The TAPE app dataloader builds batches from NPZ shards and returns `(text, pos, label)` tensors.

| Component | Responsibility |
| --- | --- |
| `PfamDataset` | Iterates pretraining shards, applies BERT-style masking, and yields masked token labels |
| `SequenceDataset` | Iterates per-token classification/regression labels for sequence annotation tasks |
| `NormalDataset` | Iterates per-sequence classification/regression labels |
| `pad_to_max_seq_len` | Pads token id and position lists to the batch max length |
| `create_dataloader` | Selects dataset class from `model_config.task` |
| `get_metric` | Selects pretrain accuracy/perplexity, classification accuracy, or regression MSE/Spearman |

## Function-Prediction API Orientation

DeepFRI, ProteinSIGN, and PTHL are app-level graph workflows rather than reusable `pahelix.model_zoo` sequence classes.

- DeepFRI uses a `DeepFRI` model, `MyDataset`, PGL `Dataloader`, and saved-state metadata merged into test args.
- ProteinSIGN uses `ProteinSIGN`, `GoTermDataset`, and `GoTermDataLoader` with graph/angle features.
- PTHL uses primary-tertiary hierarchical learning classes and does not expose a scoped test launcher in the same way as DeepFRI/ProteinSIGN.

Treat these as command-driven app workflows with explicit graph, label, split, and checkpoint paths.

## Evidence Labels

`pahelix/utils/protein_tools.py`; `pahelix/model_zoo/protein_sequence_model.py`; `apps/pretrained_protein/tape/data_gen.py`; `apps/pretrained_protein/tape/metrics.py`; DeepFRI, ProteinSIGN, and PTHL app parsers.
