# Fine-Tuning Workflows

## Public wrappers

- `FinetunedTabPFNClassifier`
- `FinetunedTabPFNRegressor`

These are sklearn-style wrappers that fine-tune the underlying TabPFN model on a
single dataset using a dedicated training loop.

## Key constructor controls

Both wrappers expose the same core training controls:

- `device`
- `epochs`
- `time_limit`
- `learning_rate`
- `weight_decay`
- `validation_split_ratio`
- `n_finetune_ctx_plus_query_samples`
- `finetune_ctx_query_split_ratio`
- `n_inference_subsample_samples`
- `random_state`
- `early_stopping`
- `early_stopping_patience`
- `validation_frequency`
- `min_delta`
- `grad_clip_value`
- `use_lr_scheduler`
- `lr_warmup_only`
- `n_estimators_finetune`
- `n_estimators_validation`
- `n_estimators_final_inference`
- `use_activation_checkpointing`
- `save_checkpoint_interval`
- `use_fixed_preprocessing_seed`
- `experiment_logger`
- `model_version`

Classifier-specific and regressor-specific extra kwargs are passed through to the
underlying estimator via `extra_classifier_kwargs` or `extra_regressor_kwargs`.
For the classifier wrapper, this is the main escape hatch for base estimator
configuration such as `n_estimators` or checkpoint selection. For the regressor
wrapper, the extra knobs also include the auxiliary loss weights and clips used
during the fine-tuning objective (`ce_loss_weight`, `crps_loss_weight`,
`crls_loss_weight`, `mse_loss_weight`, `mse_loss_clip`, `mae_loss_weight`,
`mae_loss_clip`) and the regressor eval metric (`mse`).

## How the wrappers behave

- `fit(X, y, X_val=None, y_val=None, output_dir=None)` performs the fine-tuning loop.
- If `output_dir` is provided, checkpoints are saved there.
- If `output_dir` is omitted, progress is not checkpointed.
- The wrappers use a TabPFN estimator configured for batched internal use.
- Validation and final inference can use different ensemble sizes.

## Operational notes

- For distributed runs, the wrappers can cooperate with `torchrun` / DDP.
- Validation split size is bounded so evaluation does not explode on huge datasets.
- The wrappers are intended for a single task and a single dataset family.

## When to use

Use fine-tuning when calibration is not enough and the user wants the model to
adapt to a specific dataset.
