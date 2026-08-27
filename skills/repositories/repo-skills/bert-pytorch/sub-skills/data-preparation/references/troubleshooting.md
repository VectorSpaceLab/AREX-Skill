# Data Preparation Troubleshooting

## A line is not a valid sentence pair

Symptoms:

- `bert-vocab` or `BERTDataset` fails while reading the corpus.
- The dataset looks like it only contains one sentence per line.

Likely cause:

- The corpus is missing the tab separator or has extra tabs.

Recovery:

- Reformat the corpus so every line contains exactly two sentences separated by one tab.
- Re-run `python scripts/make_tiny_corpus.py --output /tmp/bert-pytorch-corpus.txt` to compare your corpus against a known-good fixture.

## The vocab looks wrong

Symptoms:

- Rare tokens dominate the vocab.
- The vocab seems too small or does not match your expectations.

Likely cause:

- The source text was not tokenized before building the vocab.
- `min_freq` or `vocab_size` was set too aggressively.

Recovery:

- Tokenize first, then rebuild the vocab.
- Lower `min_freq` or raise `vocab_size` for a diagnostic run.

## `load_vocab` fails or the pickle looks stale

Symptoms:

- `WordVocab.load_vocab()` raises a pickle-related exception.
- The loaded vocab does not match the one you saved.

Likely cause:

- The file was not created by this package, was corrupted, or came from an incompatible environment.

Recovery:

- Rebuild the vocab from the original corpus.
- Keep the pickle private and trusted; it is executable Python serialization.

## Streaming mode is awkward

Symptoms:

- `BERTDataset(..., on_memory=False)` behaves unpredictably.
- Iteration seems to depend on hidden state.

Likely cause:

- `corpus_lines` was omitted.

Recovery:

- Use `on_memory=True` for smoke-sized corpora.
- If you must stream, supply an exact `corpus_lines` count.

## The printed sample is truncated

Symptoms:

- The dataset output appears shorter than the original text.

Likely cause:

- `seq_len` is too small.

Recovery:

- Increase `seq_len` and rebuild the smoke sample.
- Keep the smoke configuration tiny but long enough to hold the sentence pair and special tokens.
