# Model and Vocabulary Overview

## Purpose

Read this when you need to choose a model size, matching vocabulary, or tokenizer mode.

## Config files

| Config file | Shape | Best use |
| --- | --- | --- |
| `config/model_config_test.json` | `n_ctx=64`, `n_layer=1`, `n_embd=128`, `vocab_size=13317` | Import and generation smoke checks. |
| `config/model_config_small.json` | `n_ctx=1024`, `n_layer=10`, `n_embd=768`, `vocab_size=13317` | Default compact training and generation. |
| `config/model_config.json` | `n_ctx=1024`, `n_layer=12`, `n_embd=768`, `vocab_size=21128` | Larger default model. |

The config controls the model shape; the tokenizer controls how text becomes ids. Keep the two aligned.

## Vocabulary bundles

| Vocab file | Tokenizer mode | Notes |
| --- | --- | --- |
| `cache/vocab_small.txt` | Default char/BERT tokenizer | Good default for the smaller config and smoke checks. |
| `cache/vocab.txt` | Default char/BERT tokenizer | Matches the larger config. |
| `cache/vocab_seg.txt` | Word-level tokenizer | Used by the `--segment` path. |
| `cache/vocab_all.txt` | Default char/BERT tokenizer | Broader coverage. |
| `cache/vocab_guwen.txt` | Default char/BERT tokenizer | Classical-Chinese oriented coverage. |

## Tokenizer modes

### Default character / BERT mode

- Uses `tokenizations/tokenization_bert.py`.
- Tokenizes Chinese text into BERT wordpieces with special-token support.
- This is the usual path unless you intentionally need word segmentation or BPE.

### Word-level mode

- Uses `tokenizations/tokenization_bert_word_level.py`.
- Requires `thulac` and the repo's word-level dictionary file.
- Works best when you want a segmentation-aware vocabulary and have rebuilt the vocab from your corpus.

### BPE mode

- Uses `tokenizations/bpe_tokenizer.py`.
- Requires `tokenizations/encoder.json` and `tokenizations/vocab.bpe`.
- You also need a BPE vocabulary that matches the tokenizer path you pass into the CLI.

## Matching rules

- `model_config*.json` `vocab_size` should match the vocab file you pass to `--tokenizer_path`.
- If you switch tokenizer mode, re-check the vocabulary bundle.
- If you build a new vocabulary, update the config or choose a compatible model checkpoint before training or generation.
