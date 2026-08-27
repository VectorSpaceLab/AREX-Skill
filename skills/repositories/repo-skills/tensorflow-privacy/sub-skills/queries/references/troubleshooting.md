# Queries troubleshooting

## Query state or record shape problems

### Symptom
- The query fails on `initial_sample_state`, `accumulate_record`, or `get_noised_result`.

### Likely cause
- The record type does not match the query's expected structure.
- A nested query was built with incompatible child structures.

### Recovery
- Use the tiny query smoke helper first.
- Compare the record nesting with the query constructor's expected structure.

## Restart or tree-aggregation problems

### Symptom
- The query resets at the wrong time or tree-aggregation state looks inconsistent.

### Likely cause
- The restart indicator period is wrong.
- The tree-aggregation query is being asked to operate on a different step schedule than the one it was configured for.

### Recovery
- Re-check the period or time window.
- Keep the tree-aggregation helper and the accountant assumptions aligned.

## `NormalizedQuery` problems

### Symptom
- The result is scaled incorrectly or a denominator error appears.

### Likely cause
- The denominator does not match the numerator query's scale.
- The caller expects a sum query but has wrapped the numerator in a normalization step.

### Recovery
- Confirm whether the caller needs a normalized average or a raw sum.
- Keep the denominator explicit in the explanation.

## Quantile clipping problems

### Symptom
- Quantile clipping behaves unexpectedly or the adaptive clip value appears unstable.

### Likely cause
- The expected number of records or target quantile is wrong.
- The user is mixing the quantile-estimator and quantile-adaptive clip families.

### Recovery
- Read the constructor signature carefully and keep the intended family separate.
- Start with the simpler estimator query before moving to adaptive clipping.

## Non-private comparison confusion

### Symptom
- A user thinks `NoPrivacy*` is a private mechanism.

### Likely cause
- The query name was not explained.

### Recovery
- Say explicitly that `NoPrivacy*` is a baseline or debugging query, not a privacy-preserving mechanism.
