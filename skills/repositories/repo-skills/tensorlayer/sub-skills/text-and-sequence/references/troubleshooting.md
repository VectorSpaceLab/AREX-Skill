# Troubleshooting

## Vocabulary and tokenization issues

### `nltk` is missing for `process_sentence`

`tl.nlp.process_sentence` uses NLTK tokenization. If the dependency is absent, install `nltk` or fall back to a manual token list in the smoke path.

### Sentence processing gives the wrong tokens

Check the `start_word` and `end_word` arguments to `process_sentence`. Keep the synthetic corpus small enough that the resulting token ids are easy to inspect.

### Vocabulary files do not match the corpus

If you use `create_vocab`, make sure the file path is writable and that the same tokenization rules were applied to the sentences first.

## Skip-gram and sampling issues

### `generate_skip_gram_batch` returns unexpected labels

Verify `num_skips`, `skip_window`, and `batch_size`. The batch size must be consistent with the skip settings.

### `sample_top` behaves unpredictably

That helper is stochastic by design. Use a fixed probability vector and inspect the returned integer id rather than expecting a fixed sample.

## Seq2seq issues

### Constructor fails because the embedding layer is incomplete

The sequence models expect an embedding layer with `vocabulary_size` and `embedding_size` attributes. Build the embedding layer before constructing the seq2seq model.

### `Seq2seqLuongAttention` raises a `TypeError` when you pass `name=`

In this release the constructor forwards its `name` argument positionally into the base `Model` initializer. Omit `name` when instantiating `Seq2seqLuongAttention`.

### Inference fails because the input shape is wrong

Pass an integer tensor of token ids. Keep the source sequence tiny and match the `seq_length`/`start_token` or `sos` values to the model call.

### Attention or PTB examples are too heavy

Use the smoke script first. The bundled help focuses on constructor availability and tiny sequence behavior, not on long training runs.

## Dataset-download issues

### PTB or text-generation examples try to download data

That is expected for the full tutorials. Use the smoke script or a synthetic corpus instead of the full example unless you explicitly need the dataset.
