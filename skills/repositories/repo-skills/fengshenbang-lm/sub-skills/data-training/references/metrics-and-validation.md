# Metrics and validation

This reference covers the metric helpers that appear in the repo’s training code and the tiny validation checks that future agents should use before a larger run.

## Core helpers

| Helper | Signature | Input contract | Output |
|---|---|---|---|
| `get_entities` | `get_entities(seq, id2label, markup='bio', middle_prefix='I-')` | Sequence of tag ids or tag strings plus an `id2label` map when needed | List of `[entity_type, start, end]` spans. |
| `bert_extract_item` | `bert_extract_item(start_logits, end_logits)` | Start and end logits for a span-based extractor | List of `(label_id, start, end)` tuples. |
| `EntityScore` | `EntityScore().update(true_subject=..., pred_subject=...)` | Exact span tuples | Aggregate precision / recall / F1 plus per-type metrics. |
| `SeqEntityScore` | `SeqEntityScore(id2label, markup='bios').update(label_paths, pred_paths)` | Full tag sequences | Decodes with `get_entities` and computes span metrics. |
| `metrics_mlm_acc` | `metrics_mlm_acc()(logits, labels, masked_lm_metric)` | Masked-LM logits and mask map | Accuracy over masked positions only. |

## `get_entities` in practice

`get_entities` accepts `bio`, `bios`, or `bioes` markup. If you feed integer labels, pass an `id2label` mapping. If you feed strings, the mapping can be a minimal identity map or a lookup from ids to strings.

Example:

```python
seq = ["B-PER", "I-PER", "O", "S-LOC"]
id2label = {0: "O", 1: "B-PER", 2: "I-PER", 3: "S-LOC"}
# get_entities(seq, id2label, markup="bios") -> [["PER", 0, 1], ["LOC", 3, 3]]
```

The helper asserts that `markup` is one of the supported values, so a typo is a hard failure rather than a silent fallback.

## Sequence-tagging validation path

Sequence-tagging training and prediction should follow the same span conversion path:

1. normalize labels such as `M-` -> `I-` when the loader expects it,
2. use the matching `decode_type`,
3. decode spans with `get_entities`,
4. update `EntityScore` or `SeqEntityScore`,
5. compute per-type and aggregate F1 only after the full batch/epoch.

### What the repo expects

- `linear` and `crf` paths compare token labels after masking special tokens.
- `span` uses `bert_extract_item` on start and end logits.
- `biaffine` compares span matrices and filters out the padding region.

## Span evaluation gotchas

- `EntityScore` and `SeqEntityScore` require exact tuple equality.
- If the label inventory and the decode type disagree, your spans will look valid but F1 will collapse.
- In the sequence-tagging loader, the entity-type inventory differs between `linear/crf` and `span/biaffine`; do not reuse the same `labels.txt` blindly.

## Summary / QA / generation metrics

The seq2seq examples use standard generation metrics on top of the tokenized text:

- ROUGE via `torchmetrics.text.ROUGEScore`
- BLEU via `nltk.translate.bleu_score.corpus_bleu`
- simple string F1 over tokenized outputs

For Chinese text, the repo often applies a character/token normalization step before ROUGE or F1. If you adapt a new dataset, keep the same normalization path on both predictions and references.

## Tiny validation checks to run first

Use the bundled checker scripts before a real training job:

- [scripts/check_ner_labels.py](../scripts/check_ner_labels.py) for BIO / BIOES tag sanity
- [scripts/inspect_training_args.py](../scripts/inspect_training_args.py) for parser coverage

A useful smoke test is a three-token entity example and a single `S-` entity example. If those fail, do not start a distributed run.

## Metric interpretation reminders

- `EntityScore.result()` returns `acc`, `recall`, and `f1`, where `acc` is precision.
- `SeqEntityScore.result()` returns the same shape with per-type breakdowns.
- `bert_extract_item` returns label ids, not label strings; convert them with `id2label` before comparing to text spans.
- `metrics_mlm_acc` only counts masked positions, so it is not a plain token accuracy.

## Related references

- [data-formats.md](data-formats.md)
- [troubleshooting.md](troubleshooting.md)
