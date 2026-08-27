---
name: sequence-and-memory-models
description: "Operate brightmart/text_classification sequence-generation,
  Transformer, EntityNetwork, and Dynamic Memory Network workflows in a legacy
  TensorFlow 1.x context."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sequence and Memory Models

Use this sub-skill when a task involves the repository's sequence-generation or memory-network model families rather than a flat classifier:

- Seq2seq with attention for multi-label classification framed as fixed-length label-token generation.
- Transformer encoder-decoder seq2seq and the separate encoder-only Transformer classifier.
- Recurrent Entity Network and Dynamic Memory Network story/query/answer workflows.

For raw data validation and vocabulary construction, route to `data-preparation`. For TextCNN, TextRNN, RCNN, HAN, fastTextB, BERT, and TFLearn flat classifiers, route to `classification-models`. For ensemble/logit combination and relation workflows, route to `relation-and-ensemble-workflows`.

## Operating checklist

1. Read [references/model-reference.md](references/model-reference.md) to choose between seq2seq, Transformer, EntityNetwork, and DMN and to confirm expected tensor ranks.
2. If label sequences are involved, read [references/seq2seq-label-workflows.md](references/seq2seq-label-workflows.md) and use [scripts/format_seq2seq_labels.py](scripts/format_seq2seq_labels.py) to verify `_GO`, `_END`, and `_PAD` placement before adapting any model code.
3. Read [references/troubleshooting.md](references/troubleshooting.md) before planning a TensorFlow run. These are legacy TensorFlow 1.x scripts, not an installable package, and full training/prediction depends on external data files, pretrained embeddings, and checkpoints.
4. Prefer safe static or tiny formatting checks first. Do not start by running the original full training or prediction scripts; adapt only after required artifacts, label maps, batch sizes, and TensorFlow 1.x compatibility are known.

## Runtime assumptions

- Treat the repository as a TensorFlow 1.x script collection. Expect `tf.Session`, `tf.placeholder`, `tf.app.flags`, `tf.contrib`, TFLearn padding helpers, and `word2vec` binary embedding loaders.
- Use Python 3.7 / TensorFlow 1.x wording and compatibility expectations. Do not assume TensorFlow 2.x eager execution, Keras-only APIs, or Python 3.13 support.
- Full training often requires external Zhihu-style training files, HDF5/pickle caches, pretrained word2vec binaries, checkpoint directories, and long CPU/GPU runtimes. These artifacts are not bundled with this skill.
