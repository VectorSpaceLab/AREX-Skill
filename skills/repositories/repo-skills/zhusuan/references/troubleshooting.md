# ZhuSuan troubleshooting

## Environment and install issues

- Use a TensorFlow 1.x compatible Python environment; this repo is not a TF2
  eager-style project.
- The verified inspection environment used Python 3.6 with TensorFlow 1.15.5,
  SciPy, and mock.
- If `import zhusuan` fails, check that the editable install came from the
  target environment and that `pip check` is clean.

## TensorFlow 1.x compatibility issues

- The package uses `tf.Session`, `tf.placeholder`, `tf.variable_scope`, and
  other TF1 graph APIs.
- Example utilities may reference `tf.contrib`; those helpers are for the old
  example stack, not the core package.
- When moving code to TF2, keep the graph-style semantics in mind or use a TF1
  compatibility layer explicitly.

## Dependency issues

- `scipy` is needed for most distribution, variational, and MCMC tests.
- `mock` is needed for framework tests.
- `scikit-image`, `matplotlib`, and `progressbar2` are optional example extras,
  not core package requirements.

## Legacy API issues

- `latent` on variational objectives is deprecated; use `variational`.
- `rws()` was renamed to `importance()`.
- `BayesianNet` context-manager usage and `query()` / `outputs()` are legacy
  conveniences.
- `StochasticTensor.net` and `.distribution` are compatibility aliases.

## Common modeling issues

- Node names must be unique inside a `BayesianNet`.
- Observations must have the right dtype and a broadcast-compatible shape.
- If the model score looks wrong, check `group_ndims` and the event axis.

## Common inference issues

- `sgvb()` only works for reparameterizable latents.
- `vimco()` needs more than one particle on the sample axis.
- HMC adaptation should be confined to burn-in.
- `HMC.sample(...)` is intended to be called once per sampler object.

## Example-data issues

- Many example scripts expect downloaded or cached data files. If the data is
  missing, use the bundled smoke scripts or the `tests/` suite instead.
- Plotting helpers are optional and may require extra packages beyond the core
  repo install.
