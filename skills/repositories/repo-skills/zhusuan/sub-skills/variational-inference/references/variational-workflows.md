# Variational workflows in ZhuSuan

## 1. ELBO / SGVB / REINFORCE

Typical pattern:

1. Build a generative `MetaBayesianNet`.
2. Build a variational `BayesianNet` that emits the latent samples and log
   probabilities.
3. Call `zs.variational.elbo(model, observed, variational=variational, axis=0)`.
4. Use `lower_bound.sgvb()` for reparameterized latents or
   `lower_bound.reinforce()` for score-function training.

This is the pattern used by the VAE and BNN examples.

## 2. Importance-weighted objectives / IWAE / VIMCO / RWS

Use `zs.variational.importance_weighted_objective(...)` when the same family of
samples should produce a tighter objective or a VIMCO surrogate.

Rules of thumb:

- `axis` is mandatory for multi-sample objectives.
- `vimco()` requires more than one sample along the chosen axis.
- `sgvb()` is only valid when the latent variables are reparameterizable.
- `klpq(...).importance()` gives the inclusive-KL proposal adaptation path.

## 3. Importance-sampling likelihood estimates

`zs.is_loglikelihood(...)` computes the same importance-sampling estimate used
for evaluation in the example scripts. It is useful when you want a log-likeli-
hood metric for a trained variational model.

## 4. Gaussian process SVGP

The GP example uses a small helper module with an RBF kernel and a conditional
GP distribution. The main workflow is:

- create inducing-point latents
- compute the conditional GP for the function values
- train the variational posterior on minibatches
- evaluate predictive uncertainty from the conditional distribution

## 5. Example families and data dependencies

- `examples/variational_autoencoders/vae.py`: MNIST, image grid output
- `examples/variational_autoencoders/iwae.py`: MNIST, importance-weighted eval
- `examples/normalizing_flows/vae_nf.py`: MNIST plus planar flows
- `examples/semi_supervised_vae/vae_ssl.py`: MNIST, classifier branch
- `examples/sigmoid_belief_nets/sbn_vimco.py`: MNIST, discrete latent model
- `examples/bayesian_neural_nets/bnn_vi.py`: UCI Boston housing
- `examples/gaussian_process/svgp.py`: external dataset cache and GP helpers

Most of these example families rely on downloaded datasets or cached files, so
keep them as reference workflows unless the user explicitly wants to run them.
