---
name: ksd_bootstrap_gof
description: Calibrate a KSD U-statistic goodness-of-fit test with the centered multinomial bootstrap for degenerate U-statistics.
---

# KSD Bootstrap Goodness-of-fit Test

Use this skill when you already have a pairwise Stein kernel matrix and need the paper's KSD-U goodness-of-fit decision. The skill implements Algorithm 1's centered multinomial bootstrap, which is designed for the degenerate U-statistic null distribution.

Do not use this skill for ordinary non-degenerate bootstrap tests, V-statistic-only diagnostics, or linear-time KSD calibration.

## Inputs

- `stein_matrix`: finite square matrix `U` where `U[i,j] = u_q(x_i, x_j)`.
- `alpha`: significance level, usually `0.05`.
- `num_bootstrap`: bounded number of bootstrap replicates.
- `seed`: integer random seed for reproducibility.

## Outputs

- `ksd_u`: unbiased KSD U-statistic.
- `scaled_observed`: `n * ksd_u`.
- `bootstrap_scaled`: bootstrap null samples.
- `p_value`: fraction of bootstrap statistics greater than the observed statistic.
- `reject`: boolean decision `p_value < alpha`.

## Workflow

1. Validate the square Stein matrix and exclude diagonal entries for observed KSD-U.
2. Draw multinomial bootstrap counts of size `n` with uniform category probabilities.
3. Center the counts as `(w_i - 1/n)` before forming pairwise products.
4. Compare the observed scaled statistic against the bootstrap scaled statistics using the strict `>` tail rule.
5. Log the seed and bootstrap count for reproducibility.

## Validation

Run:

```bash
python tests/test_ksd_bootstrap_gof.py
```

The tests cover U-statistic calculation, reproducibility, and rejection behavior for a strongly positive Stein matrix.

## Limitations

- Bootstrap counts are intended for bounded recovery and smoke checks; large paper-scale replicates may be expensive.
- The skill assumes the Stein matrix was computed correctly by a scoring skill.

## Refinement Notes

Refinement invariant: treat multinomial draws as empirical probabilities before centering. For a draw count `count_i`, Equation (16) is implemented as `(count_i / n - 1 / n)`, not raw `count_i - 1 / n`; raw counts make the bootstrap null too wide and suppress valid KSD-U rejections.
