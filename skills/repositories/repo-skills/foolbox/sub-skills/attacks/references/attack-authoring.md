# Attack Authoring

Foolbox contributor guidance distinguishes three extension levels:

- Subclass `Attack` only for a genuinely custom call contract. Implement
  `__call__` and `repeat` with the same signature and return the standard raw,
  clipped, success values.
- Subclass `FixedEpsilonAttack` when the algorithm receives one numeric epsilon.
  Implement `run(model, inputs, criterion, *, epsilon, **kwargs)` and provide a
  `distance`; the base class clips and evaluates success.
- Subclass `MinimizationAttack` when the algorithm searches for a small
  perturbation. Implement `run(..., early_stop=None, **kwargs)` and provide a
  `distance`; the base class evaluates multiple budgets after one run.

Use `ep.astensor_`/`ep.astensors_` and restore the original type before
returning. Reject unexpected kwargs through the existing helper. Validate input
bounds and criterion support early. For channel-aware algorithms use
`get_channel_axis(model, ndim)` and require a model `data_format` when needed.

Tests should cover scalar and sequence epsilons, native and EagerPy tensor
returns, in-bounds clipping, untargeted and targeted criteria when supported,
`repeat()`, invalid kwargs, and deterministic/stochastic behavior. Follow the
repository's Black/flake8/mypy conventions when contributing to a checkout.
