---
name: deberta_race_multiple_choice_protocol
description: Build and evaluate RACE style multiple choice candidate records for DeBERTa recovery experiments.
---

# DeBERTa RACE Multiple Choice Protocol

Use this skill when a DeBERTa recovery needs a RACE-style article, question, four-option candidate layout, and accuracy calculation. The skill owns label handling and metric computation; attention and decoder helpers should return scores, not final benchmark semantics.

## Inputs

- Article text.
- Question text.
- Four answer option strings.
- Gold label `A`, `B`, `C`, or `D`.
- Optional token budget.

## Outputs

- Four candidate records containing article, question, option, label, candidate text, token positions, and absolute option position.
- Predicted label from candidate logits.
- Accuracy as a numeric metric.

## Workflow

1. Normalize whitespace.
2. Tokenize deterministically for reduced recovery, or preserve supplied tokenizer output in full recovery.
3. Build one candidate per option using the conceptual layout `[CLS] article [SEP] question option [SEP]`.
4. Score candidates externally.
5. Use `scripts/race_protocol.py` to choose the maximum-logit label and compute accuracy.

## Validation

The tests confirm four-option validation, label preservation, packed candidate records, and exact accuracy behavior.

## Limitations

This skill does not download or parse the full RACE benchmark. A reduced recovery item must clearly mark whether it is benchmark-style or resource-derived.

The standard-library tokenizer is only a recovery proxy. When truncation is used, record the requested `max_seq_len`, the emitted candidate token lengths, and whether absolute positions refer to the original untruncated item or the truncated packed sequence.
