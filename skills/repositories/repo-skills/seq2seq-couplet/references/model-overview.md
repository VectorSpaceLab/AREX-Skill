# Model Overview

## Purpose

Read this when you need the shape of the TensorFlow graph, the module
responsibilities, or the relationship between the training and inference
workflows.

## Module map

| Module | Responsibility | Notes |
| --- | --- | --- |
| `reader.py` | Reads aligned sentence pairs, encodes tokens, pads batches, and decodes ids back to text. | Input and target files are space-tokenized. |
| `seq2seq.py` | Builds the bidirectional encoder, attention decoder, projection layer, and loss. | Uses TensorFlow 1.x `tf.contrib` seq2seq APIs. |
| `model.py` | Orchestrates the train, eval, and infer graphs and checkpoint handling. | Owns the `Model` class used by the scripts. |
| `bleu.py` | Computes BLEU for evaluation. | Used by `Model.eval`. |
| `server.py` | Legacy Flask service that wraps `Model.infer` and post-processes candidates. | Imported for inspection, not for direct runtime startup. |

## End-to-end flow

1. `SeqReader` loads line-aligned input and target files.
2. Each line is split on spaces, trimmed to the configured maximum length, and
   converted to token ids with the shared vocabulary.
3. The vocabulary must place `<s>` first and `</s>` second. The source code uses
   those indices as the inference start and end tokens.
4. `seq2seq.seq2seq` builds either a training decoder with teacher forcing or a
   beam-search inference decoder.
5. `Model.train` runs the training graph, saves checkpoints, and prints sample
   outputs.
6. `Model.eval` restores the checkpoint and computes BLEU against the eval set.
7. `Model.infer` returns candidate texts and scores for downstream ranking.
8. The Flask wrapper applies extra heuristics before returning JSON.

## Graph details that matter

- The encoder is bidirectional LSTM based.
- Attention uses Bahdanau attention from `tf.contrib.seq2seq`.
- Inference uses beam search with width 10 and a maximum decode length of 100.
- The training path uses a dense projection layer and sparse softmax cross
  entropy masked by target sequence length.
- `Model` keeps separate train, eval, and infer graphs/sessions, so a model
  instance is not a single shared graph.

## Data and checkpoint relationships

- Training and evaluation should use the same vocabulary order.
- Inference only works when the checkpoint matches the vocabulary and hidden
  size that produced it.
- The legacy service expects a trained checkpoint directory and a vocabulary
  file before it can answer requests.
- The helper scripts in this skill make those paths explicit so the user does
  not have to edit hard-coded constants.

## Useful mental model

Think of the repository as three layers:

1. data reader and vocabulary handling,
2. the TensorFlow seq2seq graph,
3. training or inference wrappers around that graph.

When debugging, isolate the layer that is failing before changing hyperparameters
or the checkpoint path.
