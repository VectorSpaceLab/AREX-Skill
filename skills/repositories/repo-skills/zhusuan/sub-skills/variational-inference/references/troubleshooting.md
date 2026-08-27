# Variational troubleshooting

## Objective / axis mistakes

- `importance_weighted_objective(...)` requires an `axis` argument.
- `vimco()` requires at least two samples along that axis.
- If an objective looks numerically wrong, confirm that the sample axis is the
  one being reduced and not a model batch axis.

## Reparameterization mistakes

- `sgvb()` is only valid for reparameterizable latent variables.
- For discrete or otherwise non-reparameterizable latents, use
  `reinforce()` or `vimco()` depending on the objective.
- If gradients are `None`, check whether the latent sample path was stopped or
  whether the latent helper marks the variable as reparameterizable.

## Legacy API issues

- The `latent` argument on variational objectives is deprecated; use the
  `variational` `BayesianNet` path instead.
- `rws()` was renamed to `importance()`.

## Flow issues

- `planar_normalizing_flow` and `inv_autoregressive_flow` both expect the
  latent sample tensor and log-probability tensor to agree on all but the last
  axis.
- `inv_autoregressive_flow` also needs the hidden tensor and autoregressive
  network callable to return `(m, s)`.
- Shape mismatches usually mean the latent sample rank is wrong or the flow was
  applied before the proposal network returned a consistent tensor shape.

## Example/data issues

- VAE and SVGP examples often need MNIST, UCI, or cached data files that are
  not part of the runtime skill.
- Example scripts may use `scikit-image` or other optional plotting helpers for
  image export.
