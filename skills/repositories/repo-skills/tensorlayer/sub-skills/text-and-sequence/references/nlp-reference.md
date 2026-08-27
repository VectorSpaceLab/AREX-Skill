# NLP Reference

## Verified helpers

- `generate_skip_gram_batch(data, batch_size, num_skips, skip_window, data_index=0)`
- `process_sentence(sentence, start_word="<S>", end_word="</S>")`
- `create_vocab(sentences, word_counts_output_file, min_word_count=1)`
- `build_vocab(data)`
- `word_to_id(word)` on the vocabulary helper objects
- `sample_top(a=None, top_k=10)`

## Sequence-model constructors

- `Seq2seq(decoder_seq_length, cell_enc, cell_dec, n_units=256, n_layer=3, embedding_layer=None, name=None)`
- `Seq2seqLuongAttention(hidden_size, embedding_layer, cell, method, name=None)`

## Practical notes

- `process_sentence` adds start and end tokens unless you disable them.
- `generate_skip_gram_batch` expects a numeric corpus list and returns a batch/label pair.
- `Seq2seq` and `Seq2seqLuongAttention` both depend on an embedding layer that exposes `vocabulary_size` and `embedding_size`.
- PTB workflows rely on iterator-style sequence batching and usually need a vocabulary file or dataset file.

## Evidence summary

This page distills TensorLayer's NLP utility tests, seq2seq model code, word-embedding examples, PTB notes, text-generation notes, and text-classification guides into the helper and constructor guidance above. The bundled smoke uses a synthetic corpus.
