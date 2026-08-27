# Developer Extension Surfaces

This reference is for implementing or debugging custom scvi-tools models, modules, distributions, Pyro components, and neural-network blocks. It intentionally avoids standard user training workflows.

## Model class surface

User-facing model classes should build on `scvi.model.base.BaseModelClass` and mixins such as `VAEMixin`, `RNASeqMixin`, `ArchesMixin`, `UnsupervisedTrainingMixin`, `SemisupervisedTrainingMixin`, `PyroSviTrainMixin`, `PyroSampleMixin`, and `EmbeddingMixin` when appropriate.

Key model responsibilities:

- Define class-level setup methods, usually `setup_anndata(...)` or `setup_mudata(...)`, that create fields, construct an `AnnDataManager`, and call `register_manager`.
- In `__init__`, call `super().__init__(adata)` after setup has registered the AnnData/MuData manager.
- Store the computational module on `self.module` and preserve constructor arguments in scvi-tools' expected init-param mechanisms when following existing model patterns.
- Use `self.summary_stats` for registered dimensions such as number of variables, batches, labels, and covariates rather than recalculating them from raw data.
- Use `self._validate_anndata(adata)` when accepting alternate AnnData objects after construction.

Important `BaseModelClass` behaviors:

- The model tracks `registry_`, `summary_stats`, `is_trained_`, split indices, history, run name, and MLflow run id.
- `model.adata = new_adata` validates registry compatibility and refreshes the instance manager.
- `model.to_device(device)` moves `self.module`; `model.device` reports the module parameter device.
- Models that support minified data must inherit the corresponding minified base class; otherwise minified input raises `NotImplementedError`.

## Module class surface

Custom PyTorch modules should inherit `scvi.module.base.BaseModuleClass` and implement these abstract methods:

- `_get_inference_input(self, tensors: dict[str, torch.Tensor], **kwargs)`: parse the dataloader tensor dictionary into arguments for `inference`.
- `inference(self, *args, **kwargs) -> dict[str, torch.Tensor | torch.distributions.Distribution]`: compute variational/recognition outputs.
- `_get_generative_input(self, tensors: dict[str, torch.Tensor], inference_outputs: dict[str, torch.Tensor], **kwargs)`: combine observed tensors and inference outputs for `generative`.
- `generative(self, *args, **kwargs) -> dict[str, torch.Tensor | torch.distributions.Distribution]`: compute generative likelihood parameters and distributions.
- `loss(self, tensors, inference_outputs, generative_outputs, **kwargs) -> LossOutput`: return a `LossOutput` with a scalar minibatch loss and interpretable components.
- `sample(self, *args, **kwargs)`: generate samples from the learned model.

`BaseModuleClass.forward(...)` orchestrates `_get_inference_input`, `inference`, `_get_generative_input`, `generative`, and optionally `loss`. Use it as the first integration test for custom modules:

```python
inference_outputs, generative_outputs, losses = module.forward(tensors, compute_loss=True)
assert losses.loss.ndim <= 1
assert losses.n_obs_minibatch == tensors["X"].shape[0]
```

Use `@scvi.module.base.auto_move_data` on module methods that receive tensors and must follow the module device.

## LossOutput contract

`scvi.module.base.LossOutput` accepts:

- `loss`: tensor or dictionary of tensors; converted through `dict_sum`.
- `reconstruction_loss`: per-observation tensor or dict; required unless `n_obs_minibatch` is supplied.
- `kl_local`: per-observation KL tensor or dict.
- `kl_global`: scalar/global KL tensor or dict.
- `classification_loss`, `logits`, and `true_labels`: provide logits and labels together when adding classification loss.
- `extra_metrics`: dictionary of additional tensor metrics.
- `n_obs_minibatch`: inferred from reconstruction loss when omitted.

Common bug: returning a Python float or incorrectly reduced reconstruction loss can make `n_obs_minibatch` inference fail or break training-plan logging. Keep per-cell terms shaped like `(n_obs,)` where possible.

## Pyro module surface

Use `scvi.module.base.PyroBaseModuleClass` for Pyro-based modules. Required members:

- `_get_fn_args_from_batch(tensor_dict)`: parse minibatch tensors into positional args or keyword args shared by `model` and `guide`.
- `model` property: returns the Pyro model callable.
- `guide` property: returns the Pyro guide callable.

Useful hooks:

- `list_obs_plate_vars`: annotate minibatch plate name, encoder input positions, and observation-plate sites for minibatch training.
- `create_predictive(model=None, posterior_samples=None, guide=None, num_samples=None, return_sites=(), parallel=False)`: creates an auto-moving `pyro.infer.Predictive` wrapper.
- `on_load(model, **kwargs)`: clears the Pyro parameter store, performs a one-step warmup if needed, restores history, and can restore `pyro_param_store`.

For Pyro training, route through `scvi.train.PyroTrainingPlan`, `LowLevelPyroTrainingPlan`, or the corresponding configs when implementing new train behavior. Confirm Pyro `model` and `guide` signatures match exactly.

## Distributions and constraints

Public distribution classes in `scvi.distributions` include:

- `Poisson`
- `NegativeBinomial`
- `NegativeBinomialMixture`
- `ZeroInflatedNegativeBinomial`
- `BetaBinomial`
- `Normal`
- `Log1pNormal`
- `ZeroInflatedLogNormal`
- `ZeroInflatedGamma`

Negative-binomial family details:

- `NegativeBinomial(mu=..., theta=...)` uses mean/dispersion parameters; both `mu` and `theta` must be provided together.
- Alternative count/logit style parameters must be supplied consistently where supported; avoid mixing incompatible parameterizations.
- `ZeroInflatedNegativeBinomial(mu=..., theta=..., zi_logits=...)` expects positive `mu`/`theta` and real-valued zero-inflation logits.
- `NegativeBinomialMixture` uses component means/dispersion and `pi_logits`; broadcasting must align minibatch and feature dimensions.

For custom likelihoods, instantiate distributions with `validate_args=True` during development. Test `log_prob(x)`, `sample()`, and `mean` or expected moments on small tensors before training.

## Neural-network blocks

Reusable components in `scvi.nn` include:

- `FCLayers`: categorical-covariate-aware fully connected layers used throughout scvi-tools modules.
- `Encoder` and `Decoder`: generic latent encoder/decoder blocks.
- `DecoderSCVI` and `LinearDecoderSCVI`: SCVI-style expression decoder blocks.
- `EncoderTOTALVI` and `DecoderTOTALVI`: totalVI-style RNA/protein blocks.
- `MultiEncoder` and `MultiDecoder`: multimodal/multi-branch blocks.
- `Embedding`: embedding helper.
- `one_hot`: imported from `torch.nn.functional.one_hot`.

When adapting existing modules, preserve expected input dimensions from the registered manager: `n_input`, `n_batch`, `n_labels`, `n_continuous_cov`, and categorical covariate cardinalities. Most shape errors come from forgetting covariates, label dimensions, or batch indices.

## Minimal custom-module validation sequence

1. Register a tiny AnnData/MuData object with the model class setup method.
2. Instantiate the model and access `model.module`.
3. Get one minibatch from `model._make_data_loader(...)` or a compatible `AnnDataLoader`.
4. Run `module.forward(tensors, compute_loss=True)`.
5. Assert no `nan` or `inf` values in distribution parameters and `losses.loss`.
6. Call `model.train(max_epochs=1, accelerator="cpu", devices=1)` for an end-to-end smoke test.
7. Save and load the model if the extension adds custom `on_load`, minified-data, Pyro, or registry behavior.
