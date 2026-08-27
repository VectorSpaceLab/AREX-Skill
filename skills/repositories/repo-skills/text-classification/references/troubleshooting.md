# Legacy Text Classification Troubleshooting

Use this page for failures that cross model-family boundaries. For architecture-specific issues, route to the relevant sub-skill after resolving the environment, data, label, and artifact contracts here.

## Start with the safe smoke check

From the repository root:

```bash
python skills/disco/text-classification/scripts/check_legacy_text_classification_env.py
python skills/disco/text-classification/scripts/check_legacy_text_classification_env.py --json
```

The check imports only runtime dependencies, inspects TensorFlow capabilities, parses representative repository files, and statically assesses lightweight helper imports. It does **not** import model modules, create a session, enumerate GPUs, download data, restore checkpoints, or train. Exit code `0` means the required legacy indicators were found; a nonzero exit means at least one required capability or source/helper check failed. Read the emitted `advice` entries rather than treating package presence alone as compatibility proof.

## Runtime and import failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `tensorflow` is missing | The legacy stack is not installed in this interpreter. | Create an isolated Python 3.7-era environment and install a mutually compatible TensorFlow 1.x, TFLearn, NumPy, and h5py set. Do not modify the global environment blindly. |
| `tensorflow` has no `Session`, `placeholder`, or `app.flags` | TensorFlow 2.x is imported through its top-level namespace. | Use genuine TensorFlow 1.x for the source as written. `tf.compat.v1` is reported by the smoke check as an adaptation indicator, not proof of source compatibility. |
| `tensorflow` has no `contrib` | TensorFlow 2.x removed an API used throughout the repository. | Prefer TensorFlow 1.x. A compat-v1 alias does not restore `tf.contrib.layers.optimize_loss`, `batch_norm`, legacy RNN cells, or TPU helpers. |
| Eager execution is enabled | A TF2-style runtime is active, but source expects static placeholders and sessions. | Start a fresh compatible process. Do not mix eager-created state with these graphs. |
| `tflearn` import fails or `tflearn.data_utils` lacks `pad_sequences` | TFLearn and TensorFlow/Python versions are mismatched. | Pin a legacy-compatible stack. If only adapting a main TensorFlow model, replace the small padding dependency deliberately rather than importing TFLearn broadly. |
| `reload`, `sys.setdefaultencoding`, old `print`, or exception syntax fails | Some scripts retain Python 2 idioms. | Patch only the chosen entry point for Python 3.7, preserving encodings and output formats. Do not assume every repository script is Python 3 ready. |
| Importing a model starts a test loop or registers duplicate flags | Several scripts have import-time tests, global `tf.app.flags`, sessions, or runner code. | Inspect source statically first and import only the selected module in a fresh process. Never bulk-import model directories as a discovery mechanism. |
| A local module such as `data_util_zhihu`, `tokenization`, or a model name is not found | Scripts rely on their own directory being on `sys.path` and are not packaged consistently. | Run from the expected model directory or add only that exact directory to `PYTHONPATH`. Confirm the import name matches the checked-in filename; avoid installing the repo as though it were a normal package. |

Direct TF1 evidence includes `a01_FastText/p6_fastTextB_model_multilabel.py`, `a02_TextCNN/p7_TextCNN_model.py`, and `a00_Bert/bert_modeling.py`. TFLearn helper evidence includes `a02_TextCNN/data_util.py` and the `aa2_ClassificationTflearn` examples.

## Data and cache failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| HDF5 file or dataset key is missing | The cache was not downloaded/generated, or its schema differs from the selected loader. | Inspect the loader before the training script. `a00_Bert/utils.py` expects `train_X`, `train_Y`, `vaild_X`, `vaild_Y`, `test_X`, and `test_Y`; spelling such as `vaild` is part of that code's contract. Other model loaders may differ. |
| Pickle unpacking fails | The tuple shape, Python version, or string encoding differs. | Confirm the selected loader's expected tuple and load with an explicit legacy encoding if necessary. Regenerate vocabulary and labels together when the original cache cannot be trusted. |
| Labels are empty or shifted | Raw `__label__` parsing or label-map direction is wrong. | Validate a few raw lines and distinguish `label2index` from `index2label`. Preserve the exact mapping used to build the checkpoint and logits. |
| Seq2seq targets are off by one | Decoder input/output shifts or special tokens differ. | Route to [sequence-and-memory-models](../sub-skills/sequence-and-memory-models/SKILL.md); verify `_GO`, `_END`, `_PAD`, maximum label count, and padding before graph work. |
| Embedding assignment has a shape error | External word2vec vectors and configured `embed_size` differ. | Confirm vocabulary order, binary/text format, vector width, and out-of-vocabulary policy. Disable pretrained assignment for a graph-only probe instead of silently reshaping vectors. |
| Raw samples parse but training fails later | Different scripts use different raw, cached, single-label, multi-label, or paired-text contracts. | Route through [data-preparation](../sub-skills/data-preparation/SKILL.md) and match the exact loader used by the chosen train script. |

The README's cache links and historical 1.8 GB archive are external prerequisites, not bundled runtime guarantees. The smoke check intentionally performs no network access.

## Shapes, batches, losses, and labels

- **Single-label versus multi-label:** sparse integer labels normally pair with softmax/sparse-softmax loss; dense multi-hot labels pair with independent sigmoid loss. Do not change one side without changing the full graph, metrics, and decoding contract.
- **Fixed batch dimensions:** RCNN, memory, and relation variants may allocate tensors with configured `batch_size`. A smaller final batch can fail even when placeholders appear dynamic. Drop or pad the final batch, or refactor every fixed tensor consistently.
- **Sequence geometry:** TextCNN filter sizes cannot exceed the padded length. HAN sentence splitting must be integral. BERT `hidden_size` must be divisible by attention heads and the configured position capacity must cover the sequence length.
- **Pair geometry:** Relation workflows differ between one `EOS`-joined sequence and two separately padded inputs. Confirm the selected source before preparing data.
- **Label order:** Boosting and ensemble arithmetic is valid only when all arrays share example order, class count, and class-index mapping. Shape equality alone does not prove semantic alignment.

## Checkpoint restore failures

When `Saver.restore` reports missing variables, shape mismatches, or no checkpoint:

1. Confirm the directory contains the TensorFlow checkpoint state and matching shard files; a directory name alone is not a checkpoint.
2. Match the exact model source/variant and variable scopes used during training.
3. Match vocabulary size, label count and order, embedding width, hidden sizes, filter sizes, sequence length, batch-sensitive tensors, and BERT config.
4. Keep preprocessing artifacts from the same run. A checkpoint can restore and still decode incorrectly under a different label map.
5. For BERT, keep vocabulary, config, pretrained checkpoint, fine-tuned checkpoint, casing/tokenization choice, and head type together.

Do not use the environment smoke check as a checkpoint validator: it never reads checkpoint or data contents.

## Noisy or implausible predictions

- Verify padding, truncation, unknown-token handling, and raw token order against the training cache.
- Verify sigmoid plus threshold/top-k for independent multi-label outputs versus softmax argmax for single-label outputs.
- Decode a tiny saved-logit sample with the exact `index2label` mapping before blaming model quality.
- Treat README scores and run times as historical context, not acceptance thresholds.
- Route exported-logit issues to [relation-and-ensemble-workflows](../sub-skills/relation-and-ensemble-workflows/SKILL.md) instead of restoring every contributing model.

## Safe escalation order

1. Run the root smoke check in text or JSON mode.
2. Inspect and parse only the chosen source and helper files; do not bulk-import models.
3. Validate raw lines, cache keys, pickle tuple shape, vocabulary, and label order.
4. Build the smallest possible static graph without initializing variables or opening a session.
5. Confirm checkpoint metadata and one tiny batch.
6. Only then consider prediction or training, with explicit data and checkpoint paths.

This guide makes no network, GPU, training, benchmark-reproduction, or modern TensorFlow compatibility claim.
