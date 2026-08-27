# Workflows

## Tiny vocabulary and skip-gram smoke

1. Split a short sentence with `process_sentence`.
2. Build a vocabulary from the resulting tokens.
3. Convert the token list to ids.
4. Feed a tiny numeric corpus into `generate_skip_gram_batch`.
5. Confirm the returned batch and label shapes are consistent.

## PTB-style sequence batching

Use `tl.iterate.ptb_iterator` on a tiny integer corpus to confirm the batch/step layout before moving to a full text dataset.

## Tiny seq2seq construction

1. Build a small `Embedding` layer with a tiny vocabulary.
2. Instantiate `Seq2seq` or `Seq2seqLuongAttention` with a small GRU cell and hidden size.
3. Run a minimal inference call on a short integer sequence.
4. Confirm the output shape and token ids look reasonable.

## Sampling helper check

Use `sample_top` on a tiny probability vector to confirm that the top-k path returns an integer id.
