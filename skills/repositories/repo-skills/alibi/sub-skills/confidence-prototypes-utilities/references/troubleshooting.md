# Troubleshooting

## TrustScore label mismatch

**Symptoms**
- `fit` or `score` fails because the label count does not match the class layout.

**Likely cause**
- The labels or `classes` argument do not reflect the classifier output.

**Fix**
- Check the class count and make sure the label array matches the training data.
- Use the smoke script on iris-sized data first.

## LinearityMeasure range or mode mismatch

**Symptoms**
- The helper cannot infer a feature range or the score call raises a shape error.

**Likely cause**
- The training data was not supplied or the `model_type` does not match the predictor.

**Fix**
- Fit on representative training data.
- Re-check whether the task is classifier or regressor style.

## ProtoSelect distance or preprocessing error

**Symptoms**
- `fit` or `summarise` fails.

**Likely cause**
- The kernel distance cannot handle the batch shape or the preprocessing function does not return the expected representation.

**Fix**
- Confirm the distance metric and preprocessing contract.
- If `y` is omitted, remember that the selection is treated as unlabeled.

## Save/load round-trip fails

**Symptoms**
- Reloading fails or the explainer behaves differently after load.

**Likely cause**
- The original predictor was not passed back in, or the version changed.

**Fix**
- Reload with the original predictor.
- Treat version warnings as a signal to refresh or rebuild the skill snapshot.

## Optional dependency or utility placeholders

**Symptoms**
- A helper or dataset export is a placeholder.

**Likely cause**
- The matching optional extra is missing.

**Fix**
- Use the root optional-dependency checker if the user wants a missing-backend explanation.

## Where to go next

- Read `references/workflows.md` for the method choice.
- Run `scripts/smoke_confidence_prototypes.py` to confirm the core route.
