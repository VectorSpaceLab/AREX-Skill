---
name: deberta_enhanced_mask_decoder
description: Apply DeBERTa enhanced mask decoder scoring that injects absolute position evidence only at candidate decoding time.
---

# DeBERTa Enhanced Mask Decoder

Use this skill when a reduced recovery or unit test needs to preserve DeBERTa's decoder-time absolute-position rule. The skill separates relative-context scoring from absolute-position scoring so an experiment can prove that absolute position was not mixed into encoder inputs.

## Inputs

- Candidate records with `label`, `text`, and `absolute_position`.
- Relative-context scores from an encoder, attention helper, or deterministic proxy.
- Optional absolute-position target and weight.

## Outputs

- Candidate logits with separate `relative_score` and `emd_score` fields.
- Predicted label.
- EMD ablation result with the absolute-position contribution disabled.

## Workflow

1. Build candidate records from a masked-token or multiple-choice protocol.
2. Keep relative-context scores separate from absolute-position features.
3. Call `scripts/enhanced_mask_decoder.py` to add the EMD term at candidate scoring time.
4. Save both full and no-EMD scores in recovery logs when using this skill as mechanism evidence.

## Validation

Run the skill-tree validator with `--run-tests`. The tests check that relative-only candidates can tie, EMD breaks an absolute-position-sensitive tie, and disabling EMD changes the chosen score path.

## Limitations

This is a standard-library proxy for the EMD contract. It does not implement the full Transformer decoder stack or masked language model head.
