# Foolbox API Reference

Read this reference when selecting a wrapper, attack, criterion, distance, or
utility. Facts below were checked against Foolbox 3.3.4 source and live public
signatures.

## Public entry points

```python
import foolbox as fb
```

The package exports `Model`, `NumPyModel`, `PyTorchModel`, `TensorFlowModel`,
`JAXModel`, `Attack`, `Criterion`, `Misclassification`,
`TargetedMisclassification`, `accuracy`, `samples`, `attacks`, `distances`,
`plot`, and `zoo`.

- `fb.accuracy(fmodel, inputs, labels) -> float`
- `fb.samples(fmodel, dataset='imagenet', index=0, batchsize=1,
  shape=(224, 224), data_format=None, bounds=None) -> (images, labels)`
- `fb.NumPyModel(model, bounds, data_format=None)`
- `fb.PyTorchModel(model, bounds, device=None, preprocessing=None)`
- `fb.TensorFlowModel(model, bounds, device=None, preprocessing=None)`
- `fb.JAXModel(model, bounds, preprocessing=None, data_format='channels_last')`

`bounds` is `(lower, upper)` in the user-facing input space. Model wrappers
apply `preprocessing` before calling the underlying model. Supported
preprocessing keys are `mean`, `std`, `axis`, and `flip_axis`. A preprocessing
`axis` must be negative; `-3` is the usual channel-axis convention for
channels-first image tensors.

## Wrapper choices

- `NumPyModel` calls the model with a NumPy array and restores the incoming
  tensor type. Set `data_format` to `channels_first` or `channels_last` when a
  utility or attack needs channel semantics.
- `PyTorchModel` requires a `torch.nn.Module`, moves it to `device` (default is
  CUDA when available, otherwise CPU), and sets `data_format='channels_first'`.
  Put the module in evaluation mode for deterministic inference.
- `TensorFlowModel` requires TensorFlow eager execution. Its data format is
  obtained from Keras.
- `JAXModel` accepts a callable and defaults to `channels_last`; pass
  `data_format=None` only when channel inference must be disabled.
- `fmodel.transform_bounds(new_bounds)` returns a model with equivalent
  predictions under rescaled inputs. For preprocessing wrappers, use
  `inplace=True` only when mutation is intentional; `wrapper=True` forces a
  separate `TransformBoundsWrapper` and cannot be combined with `inplace=True`.
- `ThresholdingWrapper(model, threshold)` binarizes inputs below/above the
  threshold before forwarding them.
- `ExpectationOverTransformationWrapper(model, n_steps=16)` averages model
  outputs over repeated calls. It does not itself make a stochastic model
  deterministic.

## Attack call contract

`attack(model, inputs, criterion, *, epsilons, **kwargs)` accepts either labels
or a `Criterion`; plain labels become `Misclassification(labels)`. Fixed-
epsilon
attacks require numeric epsilons. Minimization attacks may accept `None` to
request an unconstrained result, subject to the concrete attack.

For a scalar epsilon, return `(raw, clipped, success)` where raw and clipped
have the input type and shape and success is boolean `(N,)`. For an iterable of
`K` epsilons, return lists of K raw/clipped tensors and a boolean success tensor
of shape `(K, N)`. `raw` is an algorithm result and can violate the budget;
`clipped` is the budget-safe result to inspect or visualize.

## Criteria and distances

- `Misclassification(labels)` succeeds when `argmax(model(x)) != labels`.
- `TargetedMisclassification(target_classes)` succeeds when the prediction
  equals the target class.
- Criteria compose with `criterion_a & criterion_b`.
- Built-in distances are `fb.distances.l0`, `.l1`, `.l2`, and `.linf`.
  Each computes a per-sample distance and has `clip_perturbation(reference,
  perturbed, epsilon)`.

## Common aliases and wrappers

`fb.attacks.FGSM` is `LinfFastGradientAttack`; `FGM` is the L2 variant;
`PGD`/`LinfPGD` are Linf projected gradient descent; `L2PGD`, `L1PGD`, and
`MIFGSM` are additional aliases. `attack.repeat(times)` returns a repeated
attack when the attack supports it.

`fb.zoo.get_model(url, module_name='foolbox_model', overwrite=False, **kwargs)`
clones and loads a compatible repository. `fb.zoo.fetch_weights(weights_uri,
unzip=False)` downloads and optionally extracts an archive. Both are networked
operations and should be isolated from a normal offline smoke test.
