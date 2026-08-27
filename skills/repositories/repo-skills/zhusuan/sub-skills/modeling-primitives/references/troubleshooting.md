# Modeling troubleshooting

## Import / install

- Use a TensorFlow 1.x compatible environment.
- If `import zhusuan` fails because TensorFlow is missing or incompatible,
  install a TF1 wheel and retry the editable install.
- The unit tests rely on `scipy` and `mock` in addition to the base package.

## Shape / dtype issues

- Observation tensors must broadcast to the distribution's batch and value
  shapes.
- `group_ndims` controls how many trailing batch axes are scored together.
- `n_samples` adds a leading sample axis; remember to include it when building
  variational or sampling graphs.
- `BayesianNet.normal` and the other distribution helpers inherit the
  underlying distribution's dtype rules. A mismatch usually means the model
  and observation are not aligned.

## Graph / naming issues

- Node names inside one `BayesianNet` must be unique.
- Repeating `model.observe(...)` without `reuse_variables=True` creates a fresh
  TensorFlow variable scope each time.
- `meta_bayesian_net` is the safe way to reuse variables across observations.

## Legacy compatibility

- `BayesianNet` as a context manager is deprecated.
- `query()` and `outputs()` are legacy accessors; prefer `get()` and
  `cond_log_prob()`.
- `StochasticTensor.sample()`, `.prob()`, `.log_prob()`, `.net`, and
  `.distribution` are compatibility shims; use `.dist`, `.bn`, and the
  distribution object directly for new code.
