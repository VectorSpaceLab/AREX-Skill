---
name: classification-models
description: "Route classic TensorFlow 1.x text classification model selection,
  graph inspection, training, prediction, and artifact prerequisites for
  brightmart/text_classification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Classification Models

Use this sub-skill when the task is to choose, inspect, train, restore, or adapt one of the repository's classic classification model families:

- fastTextB averaged embeddings for multi-label baselines.
- TextCNN convolution, max-pooling, and sigmoid multi-label classification.
- TextRNN, TextRCNN, and Hierarchical Attention Network variants.
- BERT fine-tuning/classification heads and online prediction patterns.
- Legacy TFLearn toy classification examples.

This repository is a legacy TensorFlow 1.x script collection, not an installable Python package. Assume Python 3.7-era compatibility work and TensorFlow 1.x/TFLearn semantics. Do not assume TensorFlow 2.x eager execution, `tf.keras` rewrites, or Python 3.13 compatibility.

## Route by task

- For architecture choice, placeholders, tensor shapes, and safe graph-construction probes, read [references/model-reference.md](references/model-reference.md).
- For training, prediction, checkpoint, cache, and embedding prerequisites, read [references/training-and-prediction.md](references/training-and-prediction.md).
- For TensorFlow 1.x, TFLearn, checkpoint, data-cache, and model-specific failure modes, read [references/troubleshooting.md](references/troubleshooting.md).
- To inspect small TensorFlow 1.x graphs without running full training, use [scripts/inspect_tf1_model_shapes.py](scripts/inspect_tf1_model_shapes.py).

## Boundaries

Use this sub-skill only for the classification families above. Route seq2seq, Transformer classification/generation, entity networks, and dynamic memory networks to `sequence-and-memory-models`. Route relation models, two-sentence models, boosting, hybrid CNN+RCNN, and ensemble prediction workflows to `relation-and-ensemble-workflows`. Route raw data cleaning, vocabulary construction, HDF5 generation, and label validation to `data-preparation`.

## Safety posture

Full training usually requires external HDF5/pickle caches, optional word2vec binaries, checkpoint directories, and long runtimes. These artifacts are not bundled with the skill. Prefer tiny graph construction and shape inspection first; run training or prediction scripts only after data, vocabulary, label, checkpoint, and TensorFlow 1.x compatibility are confirmed.
