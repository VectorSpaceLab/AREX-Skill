---
name: relation-and-ensemble-workflows
description: "Operate legacy two-sentence relation, CNN+RCNN hybrid,
  boosting-weight, and ensemble-logit workflows for
  brightmart/text_classification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Relation And Ensemble Workflows

Use this sub-skill when the task involves one of these legacy
`brightmart/text_classification` workflow families:

- two-sentence relation classification, including concatenating the pair with an
  `EOS` token or feeding two separately padded CNN inputs;
- TextCNN plus RCNN hybrid variants where two branches produce compatible logits;
- validation-logit driven boosting weights for sparse-label classification;
- combining already exported model logits and selecting top-k labels.

This is an operating guide for a legacy TensorFlow 1.x script collection. Do not
assume an installable Python package, TensorFlow 2.x eager execution, or Python
3.13 compatibility. Full source-style training/prediction usually requires
external TSV data, HDF5/pickle caches, pretrained word2vec embeddings, and
checkpoint directories that are not bundled here.

## Start Here

1. For model/data-shape decisions, read
   [references/workflows.md](references/workflows.md).
2. For failure triage, read
   [references/troubleshooting.md](references/troubleshooting.md).
3. To compute safe boosting label statistics from exported validation logits,
   use [scripts/compute_boosting_label_weights.py](scripts/compute_boosting_label_weights.py).
4. To combine exported logits without the original checkpoints, use
   [scripts/combine_logits_topk.py](scripts/combine_logits_topk.py).

## Route Elsewhere

- Single-text TextCNN, TextRNN, FastText, or HAN classifier selection belongs to
  `classification-models`.
- Raw file validation, tokenization, vocabulary building, and data-cache
  preparation belong to `data-preparation`.
- Dynamic-memory, entity-network, seq2seq, or memory-cell internals belong to
  `sequence-and-memory-models`.

## Required Caller Facts

Before giving concrete run advice, establish:

- whether the input is a relation pair or a single sequence;
- whether relation pairs are one concatenated `input_x` with `EOS` or two inputs
  `input_x`/`input_x2`;
- the label-map direction and whether every model uses the same class index
  order;
- the shape of any exported logits (`models x examples x classes` preferred);
- whether the user is only post-processing logits or attempting full legacy
  TensorFlow 1.x checkpoint restoration.
