# Attack API Reference

## Call and return shapes

```python
raw, clipped, success = attack(model, inputs, labels, epsilons=0.03)
raws, clippeds, successes = attack(model, inputs, labels,
                                    epsilons=[0.0, 0.03, 0.1])
```

Plain labels become `Misclassification(labels)`. A scalar epsilon returns
native/EagerPy tensors shaped like `inputs` plus boolean `success` shaped
`(N,)`. A sequence returns lists with one tensor per epsilon plus boolean
`success` shaped `(K, N)`. `clipped` is the budget-safe result; `raw` is for
algorithm diagnostics and may exceed the budget. If inputs are native tensors,
returned tensors preserve that type.

`Attack.__call__(model, inputs, criterion, *, epsilons, **kwargs)` and
`Attack.repeat(times)` are the stable base contracts. `FixedEpsilonAttack`
implements call-time clipping for numeric epsilons. `MinimizationAttack` runs
once and compares its result against every epsilon; `None` can request no
fixed budget where supported.

## Criteria and distances

```python
criterion = fb.Misclassification(labels)
targeted = fb.TargetedMisclassification(target_classes)
criterion = criterion_a & criterion_b
```

Criteria return one boolean per input. Use `fb.distances.l0`, `.l1`, `.l2`, or
`.linf` when an attack constructor needs a distance. `DatasetAttack()` and
`InversionAttack()` without a distance can run unconstrained but raise an
unknown-distance error when a finite budget is requested.

## Constructor facts

- `LinfPGD(rel_stepsize=0.03333333333333333, abs_stepsize=None, steps=40,
  random_start=True)`.
- `FGSM(random_start=False)`.
- `BoundaryAttack(init_attack=None, steps=25000, spherical_step=0.01,
  source_step=0.01, source_step_convergance=1e-7, step_adaptation=1.5,
  tensorboard=False, update_stats_every_k=10)`.
- `SpatialAttack(max_translation=3, max_rotation=30, num_translations=5,
  num_rotations=5, grid_search=True, random_steps=100)`.
- `ExpectationOverTransformationWrapper(model, n_steps=16)` is a model wrapper,
  not an attack argument.

`es_gradient_estimator` and its full-name alias accept
`AttackCls`, keyword-only `samples`, `sigma`, `bounds`, and `clip`.
