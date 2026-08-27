# Attack Overview

## Fixed-epsilon attacks

These attacks receive a numeric `epsilon` and Foolbox clips their returned
perturbation through the attack's `distance`. Common choices are:

- `L1FastGradientAttack`, `L2FastGradientAttack`, `LinfFastGradientAttack`
  (aliases `FGM`, `FGSM`).
- `L1/L2/LinfProjectedGradientDescentAttack` (aliases `L1PGD`, `L2PGD`,
  `LinfPGD`, `PGD`) and their Adam variants.
- Basic iterative, momentum iterative, DDN, virtual adversarial, sparse L1,
  additive Gaussian/uniform noise, and clipping-aware noise.

Gradient families calculate framework gradients and therefore require a native
PyTorch, TensorFlow, or JAX tensor/model path. Noise attacks can run through a
NumPy wrapper and are useful for black-box smoke tests.

## Minimization and decision-based attacks

Minimization attacks call `run()` once and compare the result against requested
budgets. Depending on the attack, `epsilons=None` requests an unconstrained
result. Examples include `InversionAttack`, contrast reduction, Carlini-Wagner,
EAD, DeepFool, NewtonFool, GaussianBlur, salt-and-pepper, blended noise,
BinarizationRefinement, BoundaryAttack, Brendel-Bethge, FMN, and Pointwise.

Decision/score attacks do not require model gradients, but still need a model
that returns class logits and a criterion. BoundaryAttack needs an adversarial
starting point or a successful initialization attack. DatasetAttack needs
`feed()` calls before `run()`.

## Special and compositional routes

- `SpatialAttack` searches a grid or random samples of rotations and
  translations; it returns `(xp, xp, success)` and does not use epsilon.
- `ExpectationOverTransformationWrapper` belongs to model composition and can
  be attacked with a compatible gradient attack.
- `es_gradient_estimator(AttackClass, samples, sigma, bounds, clip)` wraps an
  attack's `value_and_grad` with an evolutionary-strategy estimate when direct
  gradients are unavailable.
- `attack.repeat(times)` repeats supported attacks and keeps the best result by
  their distance/success policy. Deterministic `SpatialAttack` cannot repeat;
  use its random-search mode instead.

Choose the smallest attack that answers the question. For a benchmark, compare
several complementary families and record all budgets, steps, seeds, and
backend details rather than treating one attack's failure as a robustness proof.
