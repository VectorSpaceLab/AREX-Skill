# Privacy accounting troubleshooting

## Missing required flags

### Symptom
- The CLI exits immediately with a message about a missing flag.

### Likely cause
- `N`, `batch_size`, `noise_multiplier`, or `epochs` was omitted for the forward privacy statement.
- `N`, `batch_size`, `epsilon`, or `epochs` was omitted for the inverse noise search.

### Recovery
- Re-run the bundled CLI helper with all required flags.
- Start from the example command in the sub-skill `SKILL.md`.

## User-level privacy request fails

### Symptom
- The statement says no user-level privacy guarantee is possible.

### Likely cause
- `max_examples_per_user` was not supplied.

### Recovery
- Add a realistic `max_examples_per_user` bound.
- If the user only cares about example-level privacy, omit the user-level request and answer that instead.

## Epsilon or noise search is unrealistic

### Symptom
- The calculated epsilon is far too large, or the inverse search cannot find a matching noise multiplier.

### Likely cause
- The training configuration is too aggressive for the requested privacy target.
- The delta, batch size, epoch count, or microbatching assumption was copied from a different example.

### Recovery
- Reduce epochs, lower the batch size, or increase the noise multiplier.
- Verify the training-side assumptions before changing the privacy target.

## Accountant selection confusion

### Symptom
- The result differs from the one the user expected.

### Likely cause
- `RDP` and `PLD` were swapped.
- The user expected the more conservative default but requested the other accountant.

### Recovery
- State which accountant was used and why.
- If the user did not care, use `RDP` and say so explicitly.

## Tree-aggregation confusion

### Symptom
- A tree-aggregation result looks incompatible with the basic DP-SGD example.

### Likely cause
- The run is using a DP-FTRL / tree-aggregation variant, not the canonical DP-SGD example.

### Recovery
- Read the tree-aggregation section before mixing the formulas.
- Do not compare a tree-aggregation statement against a plain example-level DP-SGD statement without noting the different assumptions.
