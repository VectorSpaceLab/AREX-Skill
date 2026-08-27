# Attribution Workflows

## Purpose

Use this file to choose between SHAP-style attribution and integrated gradients.

## Workflow choice

| Method | Best for | Main inputs | Notes |
| --- | --- | --- | --- |
| `KernelShap` | Model-agnostic SHAP on tabular data | predictor, background data, feature names, optional categorical grouping | needs the SHAP extra |
| `TreeShap` | Tree-based model attribution | tree estimator, background data or tree-path mode, optional categorical names | needs the SHAP extra |
| `IntegratedGradients` | Gradient attribution for TensorFlow/Keras models | model, optional layer, baselines, target or target_fn | needs the TensorFlow extra |

## Kernel SHAP flow

- Fit on background data before explaining instances.
- Use `link='logit'` for probabilistic classifiers when the output should be moved into logit space.
- Use `summarise_background` when the background set is large.
- Use categorical grouping or summarization when encoded categorical features need to collapse back to one feature-level attribution.

## Tree SHAP flow

- Pass a supported tree estimator.
- Decide whether you want the path-dependent or interventional variant.
- Use `model_output='raw'` or `model_output='probability'` only when the estimator and objective support it.
- Keep `feature_names` and `categorical_names` aligned with the columns the model sees.

## Integrated gradients flow

- Pass a TensorFlow / Keras model.
- Decide whether the explanation should be with respect to the input or an internal layer.
- Provide baselines with the same shape as the explained input.
- Use either `target_fn` or explicit targets when the model output is vector-valued.

## Safe usage pattern

1. Run `scripts/check_optional_attribution_backends.py` on a base install.
2. Install the extra only when the user truly needs the optional path.
3. Start with a tiny background data set or a tiny TensorFlow model before scaling up.
4. If the task is actually anchors or counterfactuals, route away from this sub-skill.

## Read next

- `api-reference.md` for constructor signatures and output notes.
- `troubleshooting.md` for missing-extra and shape-mismatch failures.
- `scripts/check_optional_attribution_backends.py` for a clean placeholder check.
