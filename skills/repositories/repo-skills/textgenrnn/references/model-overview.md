# Model Overview

## Purpose

Read this for architecture, config, and artifact background before using any of the route-specific sub-skills.

## High-level shape

`textgenrnn` centers on a single class that wraps a text-generation model, a tokenizer/vocabulary, and a small set of training and analysis utilities.

Verified constructor signature:

```python
textgenrnn(weights_path=None, vocab_path=None, config_path=None, name='textgenrnn', allow_growth=None)
```

## Default configuration

The source defines these default config values:

| Key | Default |
| --- | --- |
| `rnn_layers` | `2` |
| `rnn_size` | `128` |
| `rnn_bidirectional` | `False` |
| `max_length` | `40` |
| `max_words` | `10000` |
| `dim_embeddings` | `100` |
| `word_level` | `False` |
| `single_text` | `False` |

The `name` field is injected at construction time and is used when saving scratch-training artifacts.

## Architecture summary

The model built in `textgenrnn/model.py` follows this pattern:

1. Input of token indices with length `max_length`.
2. Embedding layer of width `dim_embeddings`.
3. Optional `SpatialDropout1D` if dropout is requested.
4. One or more LSTM layers, optionally wrapped in `Bidirectional`.
5. Concatenation of the embedding output and all recurrent outputs.
6. Attention pooling with `AttentionWeightedAverage`.
7. Dense softmax output over the vocabulary.

When context labels are provided, the model adds a context input branch and a second softmax head with loss weights `[0.8, 0.2]`.

## Public artifacts

- Default pretrained assets bundled in the package:
  - `textgenrnn_weights.hdf5`
  - `textgenrnn_vocab.json`
- Scratch-training outputs:
  - `<name>_config.json`
  - `<name>_vocab.json`
  - `<name>_weights.hdf5`
  - optional `<name>_weights_epoch_<epoch>.hdf5`

The `save()` method writes weights only. The `load()` method expects a compatible weights file for the current architecture and vocabulary.

## Analysis-related fact

For the bundled pretrained model, `encode_text_vectors(..., pca_dims=None)` returns raw attention-layer vectors with width 356 before optional PCA or t-SNE reduction. Custom architectures may produce a different width.

## Data and sequence behavior

- Generation and encoding operate on the current `max_length` from the active config.
- `train_from_largetext_file` treats the whole file as one text and sets `single_text=True`.
- Word-level training adds spacing around punctuation before tokenization so words and punctuation can be learned consistently.

## When this matters

Use this reference when you need to reason about why a model file, config file, or vocabulary file must match, or why changing `max_length`/`word_level` changes both training and downstream generation behavior.
