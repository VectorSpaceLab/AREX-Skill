# ColBERTConfig Reference

`ColBERTConfig` combines run settings, resource paths, document/query/model settings, training settings, indexing/search settings, and tokenizer marker settings. It tracks explicitly assigned fields, which matters when checkpoint metadata is merged with caller overrides.

## Loading and Merging

Use these patterns for checkpoint and tokenizer work:

```python
from colbert.infra import ColBERTConfig

config = ColBERTConfig.load_from_checkpoint("/path/to/checkpoint")
if config is None:
    config = ColBERTConfig(checkpoint="/path/to/checkpoint")

override = ColBERTConfig(query_maxlen=48, doc_maxlen=180)
config = ColBERTConfig.from_existing(config, override)
```

`ColBERTConfig.load_from_checkpoint(checkpoint_path)` behavior:

- For `.dnn` files, loads legacy checkpoint arguments and sets `checkpoint` to the `.dnn` path.
- For Hugging Face repo names, may try to download `artifact.metadata`.
- For local checkpoint directories, looks for `artifact.metadata` and loads its `config` section.
- For generic Hugging Face backbones or directories without ColBERT metadata, returns `None`.

`Checkpoint(name, colbert_config=override)` loads metadata first and then applies assigned fields from `override`. Do not change shape-sensitive values unless the checkpoint weights are compatible.

## Key Defaults

| Field | Default | Meaning |
| --- | ---: | --- |
| `checkpoint` | `None` | Model/checkpoint resource path or name. |
| `model_name` | `None` | Optional backbone/model name override. |
| `dim` | `128` | ColBERT projection dimension. Must match projection weights. |
| `doc_maxlen` | `220` | Maximum document token width after marker insertion. |
| `query_maxlen` | `32` | Query token width after marker insertion, unless full-length search/context changes it. |
| `mask_punctuation` | `True` | Exclude punctuation token IDs from document embeddings/masks. |
| `attend_to_mask_tokens` | `False` | Whether query `[MASK]` padding tokens are attended. |
| `interaction` | `'colbert'` | Late-interaction reducer; alternate paths are guarded in code. |
| `similarity` | `'cosine'` | Scoring similarity; `l2` is supported in `ColBERT.score()`. |
| `query_token` | `'[Q]'` | Logical query marker label. |
| `query_token_id` | `'[unused0]'` | Tokenizer token converted to the query marker ID. |
| `doc_token` | `'[D]'` | Logical document marker label. |
| `doc_token_id` | `'[unused1]'` | Tokenizer token converted to the document marker ID. |
| `amp` | `True` | Mixed precision run setting used by ColBERT utilities. |
| `gpus` | visible CUDA count | Number/list/string of GPUs available to run settings. |
| `nbits` | `1` | Indexing compression setting; not a tokenizer field. |
| `load_index_with_mmap` | `False` | Search setting; route mmap issues to indexing/search. |

## Encoding-Sensitive Fields

Change these deliberately and verify with a tokenization smoke test:

- `query_maxlen`: Controls normal query ID/mask width. Lower values truncate queries sooner; higher values change query embedding token count and scoring cost.
- `doc_maxlen`: Caps passage tokenization. `DocTokenizer` tokenizes with max length `doc_maxlen - 1`, then inserts the document marker.
- `dim`: Controls projection width. Changing it without matching checkpoint weights commonly causes model loading or shape failures.
- `query_token_id` and `doc_token_id`: Must exist in the underlying tokenizer vocabulary. Defaults map to BERT-compatible unused tokens used by ColBERT checkpoints.
- `attend_to_mask_tokens`: After query pad IDs are replaced with `[MASK]`, this determines whether those positions are attended.
- `mask_punctuation`: Builds a skiplist from punctuation strings and token IDs, then zeros/removes matching document embeddings.
- `similarity` and `interaction`: Affect scoring semantics. Keep default `cosine`/`colbert` unless intentionally testing an alternate path.

## Device and Backend Behavior

`colbert.parameters.DEVICE` is CUDA when available, otherwise CPU. Tokenizer tensor outputs are moved to this device, and `BaseColBERT` moves the loaded Hugging Face model to it.

Practical implications:

- CPU inspection of `ColBERTConfig` is safe and should not require GPU.
- Tokenization can work on CPU but still loads Hugging Face tokenizer files from the local checkpoint/cache or remote Hub if allowed.
- Full `Checkpoint` loading may instantiate PyTorch modules, load weights, and compile/load CPU scoring extensions when modeling code is used without GPU.
- Query/document encoding outputs are on the model device unless `to_cpu=True` is passed.
- Document embeddings are cast to half precision on GPU in `ColBERT.doc()`.
- Indexing, training, and production retrieval commonly need CUDA/GPU even when import and config inspection work on CPU.

## Model Name and Checkpoint Compatibility

`BaseColBERT` sets `self.name = config.model_name or name_or_path`. It tries to choose a ColBERT Hugging Face wrapper through `class_factory(self.name)` and falls back to a BERT-style wrapper if needed. Then it calls `from_pretrained(name_or_path, colbert_config=config)` and loads a raw tokenizer with `AutoTokenizer.from_pretrained(name_or_path)`.

For a saved ColBERT checkpoint, prefer a directory that includes model/tokenizer files plus `artifact.metadata`. For a generic backbone such as `bert-base-uncased`, pass an explicit `ColBERTConfig`; remember that this is a model initialization/inspection workflow, not a trained ColBERT retrieval checkpoint.

## Config Inspection Checklist

Before changing max lengths or dimensions:

1. Run `scripts/inspect_checkpoint_config.py --checkpoint <local-checkpoint>`.
2. Confirm `checkpoint`, `model_name`, `dim`, `query_maxlen`, and `doc_maxlen` are what the downstream code expects.
3. If metadata is missing, decide whether to repair the checkpoint metadata or pass an explicit config.
4. Run `scripts/tokenization_smoke.py --checkpoint <local-checkpoint>` after any tokenizer-sensitive override.
5. For `dim` changes, load the model and verify projection weights before indexing/searching.
