# Corpus and Vocabulary Format

## Input layout

The package expects one sentence pair per line, with the two sentences separated by a single tab.

Example:

```text
Welcome to the\tthe jungle
I can stay\there all night
```

There is no built-in tokenizer in this package. Prepare whatever tokenization you want before calling `bert-vocab` or constructing `WordVocab` directly.

## How `WordVocab` reads text

`WordVocab(texts, max_size=None, min_freq=1)` accepts an iterable of lines or token lists.

- If it receives a string line, it strips newlines and tabs, then splits on whitespace.
- That means both sides of the tab-separated pair contribute to the vocabulary counts.
- Special tokens are always added first.

Fixed special-token ids:

| Token | Id |
| --- | --- |
| `<pad>` | `0` |
| `<unk>` | `1` |
| `<eos>` | `2` |
| `<sos>` | `3` |
| `<mask>` | `4` |

## `BERTDataset` item layout

`BERTDataset(corpus_path, vocab, seq_len, encoding='utf-8', corpus_lines=None, on_memory=True)` reads the same tab-separated corpus.

`__getitem__` returns a dict of tensors:

| Key | Meaning |
| --- | --- |
| `bert_input` | Masked input ids, padded or truncated to `seq_len`. |
| `bert_label` | Token ids for masked-language-model targets; unmasked positions are `0`. |
| `segment_label` | Segment ids: `1` for the first sentence and `2` for the second. |
| `is_next` | `1` for the true next-sentence pair, `0` for a random pair. |

## Serialization behavior

- `WordVocab.save_vocab(path)` writes a Python pickle.
- `WordVocab.load_vocab(path)` reads that pickle back.
- Treat the pickle as trusted input only.

## Tiny smoke recipe

1. Create a tiny corpus with `python scripts/make_tiny_corpus.py --output /tmp/bert-pytorch-corpus.txt`.
2. Run `python sub-skills/data-preparation/scripts/build_vocab_smoke.py` to build and reload a vocab.
3. Inspect the printed dataset sample to confirm the corpus and labels are wired correctly.

## Practical rules

- Prefer `on_memory=True` for tiny or smoke-sized corpora.
- Use an explicit `corpus_lines` value when streaming is required.
- Keep `seq_len` large enough to hold both sentences plus the special tokens.
- If `seq_len` is too small, the package truncates the sequence.
