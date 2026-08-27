# Attack Troubleshooting

- **`unsupported criterion`**: inspect whether the selected gradient attack
  supports untargeted or targeted criteria. Fast gradient attacks in this
  version reject targeted criteria in `run()`.
- **`FixedEpsilonAttack subclasses do not yet support None in epsilons`**: use a
  number/list for fixed-epsilon attacks; reserve `None` for a minimization
  attack that documents it.
- **`unknown distance`**: pass `distance=fb.distances.l2` (or the relevant
  metric) to flexible minimization attacks before finite-budget calls.
- **Input bounds assertion**: normalize inputs or transform model bounds before
  calling the attack. Do not clip silently outside the declared experiment
  contract.
- **Unexpected keyword argument**: constructor parameters and call-time
  parameters are separate; check the concrete class and do not pass arbitrary
  options to `run()`.
- **Target/label shape errors**: logits must be `(N, classes)` and labels or
  target classes `(N,)`; choose targets only after inspecting the class count.
- **No BoundaryAttack start**: ensure every `starting_points` row is already
  adversarial, or use an initialization attack with enough steps.
- **SpatialAttack failure**: use a 4-D image batch and call it without epsilon.
  It is not an Lp-ball attack. Deterministic grid search cannot be repeated;
  set `grid_search=False` for random repetitions.
- **Stochastic instability**: set framework seeds where supported, report the
  number of repetitions, and use repeated attacks or repeated noise sampling.
- **Missing TensorBoard**: keep `tensorboard=False` or install `tensorboardX`
  when logging is requested.
- **Slow pretrained examples**: the repository examples load external models
  and weights. Use a tiny local model for smoke checks and obtain approval
  before downloads.
