# Training API reference

## Purpose

Read this for the verified training-side API shapes and the arguments that matter most in user-facing workflows.

## Verified constructors and helpers

### DP optimizer wrappers

The training sub-skill centers on the Keras DP optimizer family defined in `tensorflow_privacy.privacy.optimizers.dp_optimizer_keras`.

Common usage pattern:

```python
opt = DPKerasSGDOptimizer(
    l2_norm_clip=1.0,
    noise_multiplier=0.5,
    num_microbatches=1,
    learning_rate=0.1,
)
```

The source-level wrapper accepts the DP arguments first, followed by the standard optimizer constructor arguments. The verified factory pattern is:

- `make_keras_generic_optimizer_class(cls)`
- `make_gaussian_query_optimizer_class(cls)`
- `make_keras_optimizer_class(cls)`

Useful verified signatures from the module family:

- `make_keras_generic_optimizer_class(cls: Type[tf.keras.optimizers.Optimizer])`
- `make_gaussian_query_optimizer_class(cls)`
- `make_keras_optimizer_class(cls: Type[tf.keras.optimizers.Optimizer])`

### DP model wrapper

`tensorflow_privacy.privacy.keras_models.dp_keras_model.make_dp_model_class(cls)` returns a DP subclass of a `tf.keras.Model`.

The returned class constructor accepts the DP arguments first:

- `l2_norm_clip`
- `noise_multiplier`
- `num_microbatches=None`
- `use_xla=True`
- `layer_registry=None`
- `sparsity_preserving_dpsgd_config=None`
- then the base-model arguments

The `DPModel` / `DPSequential` names exported from the package come from this factory path.

### Estimator and logistic-regression helpers

Verified signatures:

- `DNNClassifier(hidden_units, feature_columns, model_dir=None, n_classes=2, weight_column=None, label_vocabulary=None, optimizer=None, activation_fn=tf.nn.relu, dropout=None, config=None, warm_start_from=None, loss_reduction='none', batch_norm=False)`
- `compute_dpsgd_noise_multiplier(num_train, epsilon, delta, epochs, batch_size, tolerance=0.01) -> Optional[float]`
- `logistic_dpsgd(train_dataset, test_dataset, epsilon, delta, epochs, num_classes, batch_size, num_microbatches, clipping_norm) -> List[float]`
- `logistic_objective_perturbation(train_dataset, test_dataset, epsilon, delta, epochs, num_classes, input_clipping_norm) -> List[float]`

## Training-specific decision points

### Per-example loss requirement

When a DP optimizer is used with Keras, the loss generally needs to be configured with `reduction=NONE` so the optimizer can handle per-example or per-microbatch gradients.

### Microbatching

`num_microbatches` is the main knob that controls the granularity of DP clipping. It must be compatible with the batch layout.

### Vectorized and sparse variants

The repo also exposes vectorized and sparse variants. Use them when the model and training loop match the variant's assumptions.

### Fast clipping cross-reference

`DPModel` can use fast gradient clipping and sparsity-preserving noise when the layer registry supports the model. Read `../fast-clipping/references/api-reference.md` for those lower-level details.
