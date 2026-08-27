# ZhuSuan API reference

This is a compact signature map for the public APIs most often used in the
sub-skills. For fuller modeling, variational, or sampling guidance, read the
sub-skill references.

## Core modeling

```python
BayesianNet(observed=None)
meta_bayesian_net(scope=None, reuse_variables=False)
MetaBayesianNet.observe(**kwargs)
```

Common `BayesianNet` helpers:

```python
bn.normal(name, mean=0.0, _sentinel=None, std=None, logstd=None,
          group_ndims=0, n_samples=None, is_reparameterized=True,
          check_numerics=False, **kwargs)
bn.bernoulli(name, logits, n_samples=None, group_ndims=0,
             dtype=tf.int32, **kwargs)
bn.categorical(name, logits, n_samples=None, group_ndims=0,
               dtype=tf.int32, **kwargs)
bn.uniform(name, minval=0.0, maxval=1.0, n_samples=None,
           group_ndims=0, is_reparameterized=True, check_numerics=False,
           **kwargs)
```

Other helpers follow the same pattern as the distribution classes in
`zhusuan.distributions` (`fold_normal`, `gamma`, `beta`, `poisson`,
`binomial`, `multivariate_normal_cholesky`, `matrix_variate_normal_cholesky`,
`multinomial`, `unnormalized_multinomial`, `onehot_categorical`, `dirichlet`,
`inverse_gamma`, `laplace`, `bin_concrete`, `exp_concrete`, `concrete`).

Useful inspection calls:

```python
bn.get(name_or_names)
bn.cond_log_prob(name_or_names)
bn.log_joint()
bn.query(name_or_names, outputs=False, local_log_prob=False)
```

## Variational objectives

```python
elbo(meta_bn, observed, latent=None, axis=None, variational=None)
importance_weighted_objective(meta_bn, observed, latent=None, axis=None,
                               variational=None)
klpq(meta_bn, observed, latent=None, axis=None, variational=None)
is_loglikelihood(meta_bn, observed, latent=None, axis=None, proposal=None)
AIS(meta_bn, proposal_meta_bn, hmc, observed, latent,
    n_temperatures=1000, n_adapt=30, verbose=False)
```

Important methods:

```python
lower_bound.sgvb()
lower_bound.reinforce(variance_reduction=True, baseline=None, decay=0.8)
objective.vimco()
objective.importance()
```

## Samplers

```python
HMC(step_size=1.0, n_leapfrogs=10, adapt_step_size=None,
    target_acceptance_rate=0.8, gamma=0.05, t0=100, kappa=0.75,
    adapt_mass=None, mass_collect_iters=10, mass_decay=0.99)
HMC.sample(meta_bn, observed, latent)

SGLD(learning_rate)
PSGLD(learning_rate, preconditioner='rms', preconditioner_hparams=None)
SGHMC(learning_rate, friction=0.25, variance_estimate=0.0,
      n_iter_resample_v=20, second_order=True)
SGNHT(learning_rate, variance_extra=0.0, tune_rate=1.0,
      n_iter_resample_v=None, second_order=True, use_vector_alpha=True)
```

## Flow helpers

```python
linear_ar(name, id, z, hidden=None)
planar_normalizing_flow(samples, log_probs, n_iters)
inv_autoregressive_flow(samples, hidden, log_probs, autoregressive_nn,
                        n_iters, update='normal')
```

## Diagnostics

`effective_sample_size_1d(samples)` and `effective_sample_size(samples,
burn_in=100)` live in `zhusuan.diagnostics`, not the top-level package.
