# Attack Workflows

## Single attack and robust accuracy

```python
import eagerpy as ep
import foolbox as fb

images, labels = ep.astensors(*fb.samples(fmodel, dataset="imagenet", batchsize=8))
clean = fb.accuracy(fmodel, images, labels)
attack = fb.attacks.LinfPGD(steps=40)
epsilons = [0.0, 0.01, 0.03, 0.1]
raw, clipped, success = attack(fmodel, images, labels, epsilons=epsilons)
robust = 1 - success.float32().mean(axis=-1)
```

Use `clipped[k]` for the images at epsilon `epsilons[k]`; `success[k]` says
which examples were actually misclassified within that budget. Cross-check a
reported robust accuracy with `fb.accuracy(fmodel, clipped[k], labels)`.

## Multiple attacks

Run complementary attacks over the same clean batch and stack each success
mask. A worst-case per-sample result is the logical OR/max across attacks at a
fixed epsilon. Keep attack-specific distance semantics separate; an L2 result
is not directly comparable to an Linf result without an explicit benchmark
policy.

## Targeted attacks

Construct `fb.TargetedMisclassification(target_classes)` with one target per
input. Ensure targets differ from the clean class and verify the criterion
before attacking. Some fast gradient attacks explicitly reject targeted
criteria; choose a targeted-capable attack or expect `ValueError("unsupported
criterion")`.

## DatasetAttack

Feed batches before calling the attack. The attack caches model outputs and
selects other dataset members as candidate adversarials:

```python
attack = fb.attacks.DatasetAttack(distance=fb.distances.l2)
attack.feed(fmodel, reference_images)
raw, clipped, success = attack(fmodel, images, labels, epsilons=[0.5, 1.0])
```

Call `feed()` again to append more candidates. Without `feed()`, `run()` raises
a clear error. For `epsilons=None`, a distance is not needed; finite budgets
require one.

## SpatialAttack and EOT

`SpatialAttack` is called without an epsilon budget:

```python
attack = fb.attacks.SpatialAttack(max_translation=6, num_translations=6,
                                  max_rotation=20, num_rotations=5)
xp, _, success = attack(fmodel, images, labels)
```

For a randomized differentiable model, wrap it before using a gradient attack:

```python
eot_model = fb.models.ExpectationOverTransformationWrapper(fmodel, n_steps=16)
_, _, success = fb.attacks.LinfPGD()(eot_model, images, labels, epsilons=0.03)
```

This route is backend-dependent and may multiply model evaluation cost by
`n_steps`.

## Advanced extension patterns

Subclass `FixedEpsilonAttack` for a fixed-budget attack and implement `run()`;
subclass `MinimizationAttack` for a minimal-distance attack. Assign a distance,
validate bounds, preserve input tensor types through `ep.astensor_` and
`restore_type`, and return the standard tuple contract. To alter gradients,
override `value_and_grad` or wrap a compatible attack with
`fb.es_gradient_estimator(...)`.
