---
name: text-and-sequence
description: "Routes TensorLayer NLP, word-embedding, PTB, and seq2seq workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Text and Sequence

Use this sub-skill for TensorLayer NLP helpers, word-embedding utilities, PTB iteration, text generation, and seq2seq models. This is the route for text workflows that rely on TensorLayer's sequence APIs.

## Typical requests

- Build or inspect a text vocabulary.
- Generate skip-gram batches for word embedding.
- Work with PTB or text-generation examples.
- Instantiate `Seq2seq` or `Seq2seqLuongAttention`.
- Sample from a probability vector or map words to ids.

## Read first

- `references/nlp-reference.md` for the text and sequence API surface.
- `references/workflows.md` for tiny vocabulary, skip-gram, PTB, and seq2seq patterns.
- `references/troubleshooting.md` for vocabulary, sequence-shape, and dataset-download failures.

## Bundled check

- `scripts/smoke_text.py` exercises sentence processing, vocabulary building, skip-gram batches, PTB iteration, probability sampling, and tiny seq2seq construction.

## Boundaries

Include here:
- `tensorlayer.nlp`
- `tensorlayer.models.seq2seq`
- `tensorlayer.models.seq2seq_with_attention`
- PTB and text-generation workflows
- word embedding and sampling helpers

Exclude or route elsewhere:
- generic data preprocessing and TFRecord helpers -> `data-and-utilities`
- core layer/model architecture -> `core-modeling`
- training loops and CLI help -> `training-and-cli`
- vision or RL workflows -> `vision-and-apps` / `reinforcement-learning`

## Fast path

1. Identify whether the request is about tokenization, vocabulary, sampling, or sequence modeling.
2. Prefer a tiny synthetic corpus before any downloaded dataset.
3. Use the smoke script to validate the basic text utilities and model constructors.
