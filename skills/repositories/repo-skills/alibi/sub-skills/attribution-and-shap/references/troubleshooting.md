# Troubleshooting

## The export is a placeholder

**Symptoms**
- `KernelShap`, `TreeShap`, or `IntegratedGradients` is not a real class.

**Likely cause**
- The matching optional extra is missing.

**Fix**
- Run `scripts/check_optional_attribution_backends.py`.
- Install the extra that the script recommends.

## Background data or grouping is wrong

**Symptoms**
- `KernelShap` fails while fitting or explaining.
- The result shape does not match the number of groups or encoded columns.

**Likely cause**
- Background data is too large, the columns are misaligned, or grouped categorical features were not described correctly.

**Fix**
- Check `feature_names`, `categorical_names`, `groups`, and `weights`.
- If necessary, summarise the background data first.

## TreeShap model mismatch

**Symptoms**
- TreeShap rejects the estimator or the `model_output`.

**Likely cause**
- The model is not a supported tree estimator or the output mode does not match the training objective.

**Fix**
- Use the tree-based path only with supported tree estimators.
- Keep the output mode consistent with the estimator and the task.

## IntegratedGradients baseline / target mismatch

**Symptoms**
- The explainer complains about baselines, targets, or model output shape.

**Likely cause**
- The baseline shape does not match the input, or the target choice does not match the model output.

**Fix**
- Match the baseline shape to the input shape.
- For vector outputs, decide whether to pass `target_fn` or explicit targets.

## Distributed SHAP is unavailable

**Symptoms**
- The distributed option is missing or ignored.

**Likely cause**
- The Ray extra is not installed.

**Fix**
- Install the Ray extra only when the user truly needs distributed explanation execution.

## Where to go next

- Read `references/workflows.md` for the method flow.
- Use the diagnostic script before attempting a full explanation run.
