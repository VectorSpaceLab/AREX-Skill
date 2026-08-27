#!/usr/bin/env python3
"""Tiny TensorLayer text-and-sequence smoke test.

Exercises sentence processing, vocabulary building, skip-gram batches, PTB
iteration, sampling, and tiny seq2seq constructors on synthetic data.
"""

from __future__ import annotations

import argparse

import numpy as np
import tensorflow as tf
import tensorlayer as tl


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attention', action='store_true', help='also instantiate the attention-based seq2seq model')
    args = parser.parse_args()

    try:
        tokens = tl.nlp.process_sentence('tensorlayer makes text workflows easier')
    except ModuleNotFoundError:
        tokens = ['<S>', 'tensorlayer', 'makes', 'text', 'workflows', 'easier', '</S>']
    vocab = tl.nlp.build_vocab(tokens)
    if not vocab:
        raise AssertionError('vocabulary is empty')

    data = [0, 1, 2, 3, 4, 5]
    batch, labels, data_index = tl.nlp.generate_skip_gram_batch(data, batch_size=4, num_skips=2, skip_window=1, data_index=0)
    if batch.shape != (4,) or labels.shape != (4, 1):
        raise AssertionError(f'unexpected skip-gram shapes: {batch.shape}, {labels.shape}')

    iterator_batches = list(tl.iterate.ptb_iterator(list(range(20)), batch_size=2, num_steps=3))
    if not iterator_batches:
        raise AssertionError('PTB iterator yielded no batches')

    sampled = tl.nlp.sample_top(np.array([0.1, 0.2, 0.7], dtype=np.float32), top_k=2)
    if int(sampled) not in {1, 2}:
        raise AssertionError(f'unexpected top-k sample: {sampled}')

    embedding = tl.layers.Embedding(vocabulary_size=8, embedding_size=4, name='embed')
    seq2seq = tl.models.Seq2seq(
        decoder_seq_length=3,
        cell_enc=tf.keras.layers.GRUCell,
        cell_dec=tf.keras.layers.GRUCell,
        n_units=4,
        n_layer=1,
        embedding_layer=embedding,
        name='tiny_seq2seq',
    )
    seq2seq.eval()
    if args.attention:
        attn = tl.models.Seq2seqLuongAttention(
            hidden_size=4,
            embedding_layer=embedding,
            cell=tf.keras.layers.GRUCell,
            method='concat',
        )
        print('seq2seq-attention', attn.__class__.__name__, attn.method)

    print('text-ok', len(vocab), batch.tolist(), labels.flatten().tolist(), seq2seq.name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
