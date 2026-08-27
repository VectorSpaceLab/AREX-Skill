# Token and QA Troubleshooting

## QA answer span mismatch

Symptoms: training crashes, answer supervision seems wrong, or validator reports a mismatch.

Cause: `answer_start` does not point to the exact `answers[0].text` substring in `context`.

Recovery: compute the span from the context string, do not count by hand, and re-run `validate_token_qa_data.py --task qa-json`.

## Impossible QA examples

For training, `is_impossible=True` should have an empty `answers` list. Non-impossible questions need at least one answer. Mixed impossible/non-impossible rows often fail late in preprocessing, so validate first.

## NER CoNLL formatting

Symptoms: merged sentences, missing labels, or unexpected label names.

Use one token per line, blank line between sentences, and keep the last field as the label. If tokens themselves contain whitespace, choose DataFrame format instead.

## Manual tokenization mismatch

If a user supplies manually split prediction tokens, they must pass `split_on_space=False`. Otherwise the model expects raw strings and will split again.

## LayoutLM token boxes

For token-level LayoutLM, every token row needs normalized coordinates. Values outside `[0, 1000]` or reversed corners indicate data-preparation errors, not model configuration errors.

## Model download/training surprises

Even tiny examples instantiate public checkpoints unless cached. Use validators for no-network checks and set `use_cuda=False`, `no_save=True`, and short sequence lengths for smoke runs.

## Transformers compatibility

QA imports may hit the same `SequenceSummary` compatibility errors as classification because Simple Transformers custom model classes are imported by several modules. Resolve dependency compatibility before editing QA or NER data.
