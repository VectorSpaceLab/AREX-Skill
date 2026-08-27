# Training Workflows

## 1. Standard Forecasting Run

1. Clean and validate the CSV in the data-preparation sub-skill.
2. Pick a model name from the root catalog.
3. Build a JSON config with `model_name`, `model_type`, `model_params`, `dataset_params`, `training_params`, `inference_params`, and `metrics`.
4. Validate the config with `scripts/validate_training_config.py`.
5. Run `python -m flood_forecast.trainer -p config.json`.
6. Inspect the saved checkpoint directory and the evaluation metrics.

## 2. Meta / Autoencoder Run

1. Build the same top-level config shape.
2. Switch the dataset and model to the meta / autoencoding path.
3. Run `python -m flood_forecast.meta_train -p config.json`.
4. Confirm that the run uses `forecast_length = 1` and the intended representation-learning flow.

## 3. DA-RNN Run

The DA-RNN workflow is not a package CLI. It is a Python-level helper path.

Typical sequence:

1. Use the preprocessing helpers to build a `TrainData` container.
2. If the object has `features` and `targets`, adapt it to `flood_forecast.da_rnn.custom_types.TrainData(feats, targs)` before training.
3. Call `flood_forecast.da_rnn.train_da.da_rnn()` to create the network and training config.
4. Call `flood_forecast.da_rnn.train_da.train()`.
5. Enable TensorBoard or W&B only if the environment has the matching optional dependencies.

## 4. NARX Smoke Check

Run `python scripts/narx_smoke.py` on a small synthetic fixture to sanity-check the config, forward pass, and closed-loop inference path. Add `--fit` to run a one-epoch training-loop smoke through `train_transformer_style` before inference.

Use this when:

- You want a quick regression check on the `NARX` config contract.
- You need a small deterministic run before launching a larger fit.
- You want to avoid the full `trainer.train_function` post-fit SHAP path during a bounded smoke.

## 5. Resume Or Transfer Learn

When a checkpoint already exists:

- Set `weight_path` to the checkpoint.
- Use `weight_path_add["excluded_layers"]` to drop incompatible layers from the checkpoint.
- Use `weight_path_add["frozen_layers"]` to freeze named modules after load.

## 6. Validation And Evaluation Expectations

- Forecasting runs usually evaluate after training through `inference_params`.
- `GeneralClassificationLoader` and `VariableSequenceLength` use different post-fit validation semantics.
- `EarlyStopper` saves `checkpoint.pth` when the validation loss improves.

## 7. Safe Smoke Strategy

Start with:

- CPU.
- One epoch.
- Small batch sizes.
- A tiny local CSV fixture.
- No cloud upload and no W&B unless you explicitly need it.

That approach catches config and loader mistakes without launching a long fit.
