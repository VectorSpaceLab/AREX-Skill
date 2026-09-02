---
name: dpo_sequence_logprob_accounting
description: Compute response-only sequence log probabilities for DPO by masking prompts and padding before summing token log probabilities.
---

# DPO Sequence Log Probability Accounting

Use this skill when converting model token scores into the `log pi(y|x)` values consumed by DPO. It is appropriate for full model recovery and for deterministic tests of the DPO objective. Do not use it to normalize preference records or to compute the DPO loss itself.

## Inputs

- Per-position token log-probability tables or logits converted to log probabilities.
- Label token ids for next-token prediction.
- Ignored positions marked as `-100` for prompt and padding tokens.
- Optional `average` flag.

## Outputs

- Response-only summed or averaged sequence log probabilities.
- Token counts and selected token log-probabilities when diagnostics are requested.

## Workflow

1. Ensure each example has aligned per-position token distributions and labels.
2. Shift labels one position to match next-token prediction if using full prompt+response sequences.
3. Ignore labels equal to `-100` so prompt and padding positions do not affect the response probability.
4. Gather the log probability assigned to each unmasked label token.
5. Sum by default; average only when the caller explicitly requests length normalization.

## Validation

Run:

```bash
python scripts/logprob_accounting.py --self-test
python tests/test_logprob_accounting.py
```

## Limitations

The script uses standard-library math and expects log-probability inputs for reduced tests. Full tensor implementations should preserve the same mask semantics.