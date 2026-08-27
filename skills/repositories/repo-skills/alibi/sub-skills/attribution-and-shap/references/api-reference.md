# API Reference

## Purpose

This file records the attribution APIs that the sub-skill routes.

## Constructors

- `KernelShap(predictor, link='identity', feature_names=None, categorical_names=None, task='classification', seed=None, distributed_opts=None)`
- `TreeShap(predictor, model_output='raw', feature_names=None, categorical_names=None, task='classification', seed=None)`
- `IntegratedGradients(model, layer=None, target_fn=None, method='gausslegendre', n_steps=50, internal_batch_size=100)`

## Main call patterns

- `KernelShap.fit(background_data, summarise_background=False, n_background_samples=300, group_names=None, groups=None, weights=None, **kwargs)`
- `KernelShap.explain(X, summarise_result=False, cat_vars_start_idx=None, cat_vars_enc_dim=None, **kwargs)`
- `TreeShap.fit(background_data=None, summarise_background=False, n_background_samples=1000, **kwargs)`
- `TreeShap.explain(X, y=None, interactions=False, approximate=False, check_additivity=True, tree_limit=None, summarise_result=False, cat_vars_start_idx=None, cat_vars_enc_dim=None, **kwargs)`
- `IntegratedGradients.explain(X, forward_kwargs=None, baselines=None, target=None, attribute_to_layer_inputs=False)`

## Output notes

- `KernelShap` returns local or global SHAP-style attributions, plus expected values and raw prediction metadata.
- `TreeShap` can return interaction values when requested and the tree path supports them.
- `IntegratedGradients` returns attributions that match the model or layer shape being explained.

## Optional-backend notes

- `KernelShap` and `TreeShap` are placeholders without the SHAP extra.
- `IntegratedGradients` is a placeholder without the TensorFlow extra.
- If the user only wants to know whether the environment is ready, use the diagnostic script rather than trying a full explanation call.
