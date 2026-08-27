# Troubleshooting

## Purpose

Use this file when Alibi imports, predictors, or optional backends fail. For workflow-specific details, continue into the matching sub-skill.

## Import fails right away

**Symptoms**
- `import alibi` fails.
- The traceback mentions spaCy, `click`, or another indirect dependency.

**Likely cause**
- The base environment is missing an indirect dependency or the editable install was incomplete.

**Next step**
- Reinstall the package dependencies and rerun `scripts/core_smoke.py`.
- If the message mentions optional exports, use `scripts/check_optional_backends.py` to confirm whether the failure is a missing extra or a broken base install.

## Optional export shows up as a placeholder

**Symptoms**
- `KernelShap`, `TreeShap`, `IntegratedGradients`, `CounterfactualProto`, or another optional symbol is not a real class.

**Likely cause**
- The matching extra is not installed yet.

**Next step**
- Read `references/optional-dependencies.md`.
- Install the matching extra and rerun the checker.

## Predictor shape or type errors

**Symptoms**
- Explain calls complain about input shape, batch dimension, or unexpected return type.
- Anchors on text fail on non-string batches.

**Likely cause**
- The predictor does not match the method's contract.

**Next step**
- Check `references/api-reference.md` and the owning sub-skill's workflow reference.
- For tabular explainers, pass `numpy.ndarray` batches.
- For AnchorText, pass `List[str]` batches.
- For image explainers, pass a single image with channel dimension.

## Save/load issues

**Symptoms**
- Loading an explainer fails because the predictor was not supplied again.
- A warning says the saved version and runtime version differ.

**Likely cause**
- Save/load is intentionally partial and version-sensitive.

**Next step**
- Reload with the original predictor.
- If version drift matters, rebuild the environment or refresh the skill snapshot.

## Optional backend families

**Symptoms**
- SHAP, TensorFlow counterfactuals, or PyTorch similarity workflows are unavailable.

**Likely cause**
- The base install does not include the needed backend extra.

**Next step**
- Do not claim the workflow is verified in a base-only environment.
- Open the appropriate sub-skill and install the extra listed in its backend notes.

## When to stop and ask for more context

Stop when the user wants a GPU/accelerator backend, a private dataset, or a long training run that is not covered by the bundled smoke scripts. Use the matching sub-skill's troubleshooting page for workflow-specific recovery steps.
