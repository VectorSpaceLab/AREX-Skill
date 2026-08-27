# Advanced Troubleshooting

Use this guide for scvi-tools failures in optional extras, autotune, MLflow, custom modules, Pyro internals, distributions, and developer APIs.

## `scvi.autotune` import fails

Likely cause: the `autotune` extra is not installed. Default installs may not include Ray, HyperOpt, scib-metrics, or muon.

Checks:

```python
import importlib.util
missing = [name for name in ["ray", "hyperopt", "scib_metrics", "muon"] if importlib.util.find_spec(name) is None]
print(missing)
```

Fix:

- Install `scvi-tools[autotune]` in the active environment.
- If the task only needs a tiny search and HyperOpt is unavailable, use `searcher="random"` after Ray Tune is available.
- Keep public skill examples explicit that autotune is optional-extra gated.

## `run_autotune` rejects arguments

Common errors and fixes:

- `metrics` is `None` or `[]`: pass a string such as `"elbo_validation"` or a non-empty list where the first metric is the optimization target.
- `mode` is invalid: use exactly `"min"` or `"max"`.
- `search_space` has wrong top-level keys: only use `"model_params"` and `"train_params"`.
- `num_samples` is not an integer: pass an `int`, even for a smoke test.
- scheduler/searcher names are misspelled: use `"asha"`, `"hyperband"`, `"median"`, `"fifo"`, `"hyperopt"`, or `"random"`.
- AnnData is not set up for the model class: call `ModelClass.setup_anndata(adata, ...)` before tuning.

## Ray fails to initialize or hangs

Triage:

- Reduce `num_samples`, `max_epochs`, and per-trial `resources`.
- Set `resources={"cpu": 1, "gpu": 0}` for CPU smoke tests.
- Use a short `logging_dir` and explicit `experiment_name` to avoid path surprises.
- If Ray is already running in the process, pass `ignore_reinit_error=True`.
- For debugging only, pass `local_mode=True` and `log_to_driver=True`.
- For MuData, ensure `logging_dir` is writable because autotune writes the MuData file for worker reuse.

## scib-metrics autotune fails

Triage:

- Confirm `scib-metrics` is installed through `scvi-tools[autotune]`.
- Use one recognized metric name: `"Total"`, `"Batch correction"`, `"Bio conservation"`, `"Silhouette label"`, `"Isolated labels"`, `"Leiden"`, `"KMeans"`, `"cLISI"`, `"iLISI"`, `"KBET"`, `"BRAS"`, `"Graph connectivity"`, or `"PCR comparison"`.
- Set `scib_subsample_rows` low for large datasets.
- Try `solver="arpack"`, `"randomized"`, or `"auto"` if PCA/SVD fails.
- Confirm the training plan exposes the expected training or validation epoch outputs when using scib callbacks.

## MLflow does not log

Likely causes:

- `scvi.settings.mlflow_set_tracking_uri` is empty, so the training runner uses normal training.
- `mlflow` is not installed; install `scvi-tools[mlflow]` or `mlflow` plus the MLflow extra dependencies.
- The MLflow server is not reachable from the training process.
- Artifact/table/text helper inputs exceed their `max_size_mb` limits and are skipped with warnings.

Minimal check:

```python
import scvi
print(scvi.settings.mlflow_set_tracking_uri)
print(scvi.settings.mlflow_set_experiment)
```

Fix by setting both before `model.train(...)`, then verify the active run id on the model after training if needed.

## Custom module has invalid tensor shapes

Symptoms include shape mismatch in encoders/decoders, loss reduction errors, invalid `LossOutput`, or distribution broadcasting failures.

Debug sequence:

1. Print registered summary stats from `model.summary_stats`.
2. Inspect one minibatch tensor dictionary and record shapes for `X`, `batch`, `labels`, continuous covariates, and categorical covariates.
3. Run `_get_inference_input(tensors)` and assert all expected keys are present.
4. Run `inference(**inputs)` and assert latent tensors have leading dimension `n_obs_minibatch`.
5. Run `_get_generative_input(tensors, inference_outputs)` and assert decoder inputs align with batch/covariate dimensions.
6. Run `generative(**inputs)` and assert distribution parameters broadcast to `(n_obs_minibatch, n_features)` or the model-specific target shape.
7. Run `loss(...)` and assert `LossOutput.loss` is scalar-like and reconstruction/KL components have consistent minibatch semantics.

Typical fixes:

- Use `self.summary_stats` rather than raw `adata` shape for registered dimensions.
- Include continuous and categorical covariates in encoder inputs only when the module was configured for them.
- Keep labels as integer class indices for classification losses.
- Do not reduce reconstruction loss over observations before building `LossOutput` unless you also pass `n_obs_minibatch`.

## Distribution parameters are invalid

Symptoms include `ValueError` under `validate_args=True`, `nan` loss, `inf` log-probability, or exploding gradients.

Checks:

```python
dist = ZeroInflatedNegativeBinomial(mu=mu, theta=theta, zi_logits=zi_logits, validate_args=True)
log_px = dist.log_prob(x)
assert torch.isfinite(log_px).all()
```

Fixes:

- Constrain positive parameters with `softplus`, `exp` plus clamping, or a small epsilon.
- Ensure `mu`, `theta`, `scale`, `rate`, and `concentration` are positive and finite.
- Keep zero-inflation parameters on logits scale for `zi_logits`; do not pass probabilities unless the API explicitly asks for probabilities.
- Reshape one-dimensional dispersion vectors to broadcast across cells when needed.
- Check that observed count tensors are non-negative and compatible with the chosen likelihood.

## Pyro model or guide fails

Common causes:

- `model` and `guide` signatures differ.
- `_get_fn_args_from_batch` returns different argument structure than the Pyro callables expect.
- `list_obs_plate_vars` does not annotate observation-plate sites used for minibatching.
- Pyro parameter store contains stale values after loading or architecture changes.

Fixes:

- Clear state with `pyro.clear_param_store()` before isolated smoke tests.
- Run one CPU minibatch through the Pyro training plan before scaling out.
- Use `create_predictive(return_sites=(...), num_samples=...)` to isolate posterior predictive failures.
- For loaded Pyro models, inspect `on_load_kwargs` and `pyro_param_store` restoration behavior.

## Hard synthetic cases for verification

- Autotune requested on a default install: a future agent should detect missing `ray`, `hyperopt`, `scib_metrics`, or `muon`, explain `scvi-tools[autotune]`, and avoid writing a misleading runnable sweep.
- Custom module returns decoder parameters with incompatible feature dimensions or negative `theta`: a future agent should isolate the failing stage, enable `validate_args=True`, and propose shape/constraint fixes before training.
