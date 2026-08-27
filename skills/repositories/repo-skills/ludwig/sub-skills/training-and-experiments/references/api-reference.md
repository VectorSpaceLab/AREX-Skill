# Training API Reference

## `LudwigModel.train`

Important parameters: `dataset`, `training_set`, `validation_set`, `test_set`, `training_set_metadata`, `data_format`, `experiment_name`, `model_name`, `model_resume_path`, save-skip flags, `output_directory`, `random_seed`, `callbacks`, and preprocessing `**kwargs`.

Return: `TrainingResults` containing `train_stats`, `preprocessed_data`, and `output_directory`.

## `LudwigModel.experiment`

Combines train and evaluate. It accepts training inputs plus `eval_split`, prediction/eval save flags, and collection flags. Use it when the task asks for test metrics or a complete train/evaluate run.

## `train_cli` / `experiment_cli`

The CLI functions accept the same dataset/config/output/resume/backend/GPU/logging concepts as the shell commands. They are useful for embedding command behavior inside Python tools, but `LudwigModel` is the cleaner API for most code.

## Callbacks

Callbacks can be passed at `LudwigModel(...)` construction or per-call. They are used for logging/tracking integrations and lifecycle hooks. Optional contrib integrations such as Aim, W&B, Comet, and MLflow require their packages and credentials.
