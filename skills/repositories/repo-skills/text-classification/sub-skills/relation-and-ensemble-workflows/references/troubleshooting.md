# Troubleshooting Relation And Ensemble Workflows

Use this guide when a relation, boosting, hybrid, or ensemble workflow fails
before or during legacy TensorFlow 1.x execution, or when the bundled
post-processing helpers reject exported JSON.

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Relation loader reports split errors or produces empty second sentence | Malformed TSV: the pair text does not contain exactly one tab before `__label__`, or the label separator is missing | Validate the record format before padding. For the two-CNN relation variant, reject or repair lines that cannot split into `text1` and `text2`. |
| Concatenated relation model performs as if the two questions are one sentence | `EOS` is missing from the vocabulary or was treated as padding/unknown | Add a real `EOS` token to the word vocabulary and preserve it between the two token lists before padding. |
| Predictions use plausible class indices but wrong topic/relation names | Label map mismatch across training, checkpoint, exported logits, or ensemble post-processing | Keep one canonical index-to-label map for all models. For ensembling, verify every logits column uses that exact class order. |
| TensorFlow flags fail before graph construction with a duplicate-name error | A source-style script declares the same `tf.app.flags` name more than once in one process | Rename/remove duplicate flag declarations when porting, or run conflicting predictors in separate processes. This is common in ad hoc ensemble scripts. |
| Full ensemble predictor stops with “can't find checkpoint” | Source-style prediction expects external checkpoint directories that are not bundled | Either provide the matching checkpoint tree and graph hyperparameters, or export logits separately and use `scripts/combine_logits_topk.py`. |
| Bundled logit combiner exits with a shape error | Model logits have different numbers of examples/classes, or a single-model array was nested incorrectly | Use `[models][examples][classes]` for multiple models. Confirm every model emits the same `num_examples` and `num_classes`. |
| Ensemble top-k labels are shifted or nonsensical | Model order, batch order, or label-map direction is inconsistent | Check weights are in model order, examples are in identical order, and `label-map-json` maps class indices to labels or labels to indices unambiguously. |
| Hybrid TextCNN+RCNN graph errors on batch dimensions | RCNN boundary variables were created with fixed `[batch_size, embed_size]` shapes | Feed the configured batch size, pad/drop incomplete batches, or refactor boundary tensors to dynamic shapes before claiming variable batch inference. |
| Multi-label hybrid accuracy is always constant | The graph's multi-label branch uses a placeholder/fake accuracy constant | Compute multi-label metrics outside the graph from logits and true multi-hot labels. Do not report the graph accuracy as real. |
| Weighted sparse softmax loss rejects `weights` | Weight vector length or dtype does not match the current batch | Create one float weight per example in `answer_list`, in the same order as `labels`, and feed it to the same batch loss call. |
| Boosting weights explode for rare/never-correct labels | Accuracy is zero or near zero | Keep the cap (`--max-weight`, source pattern `1.5`) and epsilon (`0.001`) unless there is validation evidence for a different schedule. |
| TensorFlow import errors mention `tf.contrib`, eager execution, or missing `tflearn` | Running under TensorFlow 2.x or an incompatible Python environment | Recreate with Python 3.7-era TensorFlow 1.x/TFLearn compatibility. Do not assume Python 3.13 or modern TensorFlow APIs. |
| Source training appears to hang or repeatedly rebuild data | External caches, pretrained embeddings, or large training files are absent | Treat full training as a long-running legacy workflow. Verify external data, word2vec binaries, and cache/checkpoint paths before starting. |

## Fast Isolation Checklist

1. Identify the workflow: concatenated relation, two-input relation, hybrid
   single-sequence classifier, boosting, or ensemble post-processing.
2. Print the first parsed example before padding and the first padded example
   after padding.
3. Print logits shape and label shape before any loss or ensemble operation.
4. For relation data, prove `EOS` or `text1`/`text2` splitting matches the
   selected variant.
5. For ensembles, prove label maps and example order are identical before
   looking at accuracy.
