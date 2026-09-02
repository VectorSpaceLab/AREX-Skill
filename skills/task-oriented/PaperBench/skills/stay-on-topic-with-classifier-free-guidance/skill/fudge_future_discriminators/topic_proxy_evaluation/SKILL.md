---
name: topic_proxy_evaluation
description: Evaluate reduced FUDGE topic-control recovery with topic-token metrics and explicit mechanism checks.
---

# Topic-Control Proxy Evaluation

Use this skill to score a small mechanism-faithful recovery of FUDGE topic control. It is intended for soft-mode reduced/proxy experiments, not for claiming full Table 4 reproduction.

## Inputs
- Generated tokens or selected next tokens.
- Target topic words and optional heldout words.
- Decoder audit traces from FUDGE rescoring and composition.
- Optional reduced-training trace.

## Outputs
- `topic_token_rate`, `topic_word_coverage`, and `distinct_1`.
- Mechanism checks for prefix labels, future probabilities, composition, adjusted logits, normalization, and optimizer parameter changes.

## Workflow
1. Compute topic-token metrics.
2. Verify audit traces contain future probabilities and adjusted logits.
3. Verify probabilities are normalized.
4. If reduced training is claimed, verify loss and parameter changes.
5. Return metrics and checks for `recovery_result.json`.

## Validation
Run `python tests/test_topic_eval.py`.
