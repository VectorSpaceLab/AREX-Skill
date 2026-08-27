# SVI Workflows

This reference covers practical Pyro SVI construction in the 1.9.1 API family.
It assumes the model itself is already valid Pyro code; for primitive, parameter,
plate, and distribution-shape basics, route to sibling sub-skills before tuning
SVI.

## Core API Facts

| Object | Runtime signature pattern | Use |
|---|---|---|
| `SVI(model, guide, optim, loss, loss_and_grads=None, num_samples=0, num_steps=0, **kwargs)` | `optim` must be a `pyro.optim.PyroOptim`; `loss` is usually an ELBO instance. | High-level SVI loop. Prefer `step()` over deprecated `run()` and avoid deprecated `num_samples` / `num_steps`. |
| `SVI.step(*args, **kwargs)` | Passes all args/kwargs to both model and guide. | Computes gradients, steps the Pyro optimizer, zeroes gradients, and returns a Python float loss. |
| `SVI.evaluate_loss(*args, **kwargs)` | Runs under `torch.no_grad()`. | Estimate loss without updating params; useful for validation curves. |
| `Trace_ELBO(...)` and siblings | Common args include `num_particles`, `max_plate_nesting`, `vectorize_particles`, `strict_enumeration_warning`, `ignore_jit_warnings`, `jit_options`, `retain_graph`. | Select estimator behavior; see below. |
| `ELBO.__call__(model, guide)` | Returns a `torch.nn.Module` loss wrapper. | Use with `torch.optim`, PyTorch dataloaders, schedulers, Lightning-like trainers, or module-local parameters. |

Minimal high-level SVI skeleton:

```python
import pyro
import pyro.distributions as dist
from pyro.infer import SVI, Trace_ELBO
from pyro.optim import Adam
from torch.distributions import constraints


def model(data):
    loc = pyro.sample("loc", dist.Normal(0.0, 1.0))
    with pyro.plate("data", data.size(0), dim=-1):
        pyro.sample("obs", dist.Normal(loc, 1.0), obs=data)


def guide(data):
    loc_q = pyro.param("loc_q", data.new_tensor(0.0))
    scale_q = pyro.param(
        "scale_q", data.new_tensor(0.1), constraint=constraints.positive
    )
    pyro.sample("loc", dist.Normal(loc_q, scale_q))

pyro.clear_param_store()
svi = SVI(model, guide, Adam({"lr": 0.02}), Trace_ELBO())
for step in range(num_steps):
    loss = svi.step(data)
    if not torch.isfinite(torch.as_tensor(loss)):
        raise RuntimeError(f"non-finite SVI loss at step {step}: {loss}")
validation_loss = svi.evaluate_loss(heldout_data)
```

## Model-Guide Pairing Rules

- Model and guide must accept the same inputs. If the model uses `model(x, y=None)`,
  the guide should accept `guide(x, y=None)` even if it ignores `y`.
- Guide sample sites represent an approximate posterior for model latent sample
  sites. A non-auxiliary guide site with no matching model site is suspicious;
  an unobserved model site with no guide site is suspicious unless it is
  enumerated/marginalized.
- A guide may include auxiliary sample sites for reparameterized constructions
  by marking them `infer={"is_auxiliary": True}`.
- Model and guide sample sites with the same name must agree in event dimension
  and compatible shape. Most fixes are in distribution `.to_event(...)`, plate
  structure, or guide parameter shape.
- Clear global state before repeated experiments: `pyro.clear_param_store()`.
  If using `PyroModule` with vanilla `torch.optim`, prefer module-local params as
  described in the optimizer reference.

## Manual Hierarchical Guide Recipe

For hierarchical models, a custom guide often mirrors every unobserved model
site with constrained parameters. The pattern is:

```python
def model(y, sigma):
    num_groups = y.size(0)
    with pyro.plate("group", num_groups, dim=-1):
        eta = pyro.sample("eta", dist.Normal(y.new_zeros(num_groups), 1.0))
        mu = pyro.sample("mu", dist.Normal(y.new_zeros(1), 10.0))
        tau = pyro.sample("tau", dist.HalfCauchy(y.new_ones(1) * 25.0))
        theta = mu + tau * eta
        pyro.sample("obs", dist.Normal(theta, sigma), obs=y)


def guide(y, sigma):
    num_groups = y.size(0)
    loc_eta = pyro.param("loc_eta", lambda: y.new_zeros(num_groups))
    scale_eta = pyro.param(
        "scale_eta", lambda: y.new_ones(num_groups) * 0.1,
        constraint=constraints.positive,
    )
    loc_mu = pyro.param("loc_mu", lambda: y.new_zeros(1))
    scale_mu = pyro.param(
        "scale_mu", lambda: y.new_ones(1) * 0.1,
        constraint=constraints.positive,
    )
    loc_log_tau = pyro.param("loc_log_tau", lambda: y.new_zeros(1))
    scale_log_tau = pyro.param(
        "scale_log_tau", lambda: y.new_ones(1) * 0.1,
        constraint=constraints.positive,
    )
    with pyro.plate("group", num_groups, dim=-1):
        pyro.sample("eta", dist.Normal(loc_eta, scale_eta))
        pyro.sample("mu", dist.Normal(loc_mu, scale_mu))
        pyro.sample("tau", dist.LogNormal(loc_log_tau, scale_log_tau))
```

This recipe illustrates three durable rules: initialize guide scales narrowly but
positively, match every latent site name exactly, and match plate structure when
latent tensors are group-indexed. For many hierarchical models, `AutoNormal` is
a quicker baseline; keep the custom guide when domain knowledge or constrained
parameterization materially helps.

## ELBO Selection

| Situation | Prefer | Why / caveat |
|---|---|---|
| Ordinary continuous latent variables, custom guides, autoguides, simple plates | `Trace_ELBO()` | Default estimator; no dependency restrictions beyond valid model/guide shape. |
| Non-reparameterizable guide sites where provenance-aware variance reduction or baselines matter | `TraceGraph_ELBO()` | Uses denser dependency tracking; slower, but supports more fine-grained score-function variance reduction. |
| Discrete latent variables that can be exactly enumerated | `TraceEnum_ELBO(max_plate_nesting=...)` | Supports exhaustive enumeration. Mark sites for parallel/sequential enumeration or use `config_enumerate`; route mechanics to `../effect-handlers-and-enumeration/`. |
| Mean-field, fully reparameterized guide where analytic KL terms are available and model/guide order satisfies the mean-field restriction | `TraceMeanField_ELBO()` | Can use analytic KL divergences. Incorrect if mean-field restriction is violated; validation warns when it cannot verify ordering. |
| Static-structure model/guide and profiler shows Python overhead dominates | `JitTrace_ELBO`, `JitTraceGraph_ELBO`, `JitTraceEnum_ELBO`, or `JitTraceMeanField_ELBO` | JIT has strict static-structure/input rules; debug with non-JIT first. |
| Multiple particles for lower-variance estimates | Any ELBO with `num_particles > 1` | More compute per step. Pair with `vectorize_particles=True` only for static structure and valid plate nesting. |

Common ELBO constructor pattern:

```python
elbo = Trace_ELBO(
    num_particles=4,
    vectorize_particles=True,
    max_plate_nesting=1,     # set explicitly for enumeration or dynamic plates
    ignore_jit_warnings=False,
)
```

When using `vectorize_particles=True`, Pyro wraps model and guide in an outer
particle plate. Static model/guide structure is required, and `max_plate_nesting`
may need to be explicit so particle dimensions do not collide with data plates or
enumeration dimensions.

## JIT Rules

Use JIT variants only after a non-JIT loop is correct.

JIT-compatible SVI should satisfy:

- model and guide have static control flow and static sample-site structure;
- model and guide do not read mutable global data except Pyro's parameter store;
- tensor inputs are passed positionally through `*args`;
- non-tensor configuration is passed via `**kwargs`; a new trace can be compiled
  for each unique non-tensor kwarg pattern;
- warnings are not ignored until the non-JIT and JIT losses agree on a tiny run.

If JIT warnings are expected and understood, set
`ignore_jit_warnings=True` or pass `jit_options={...}` to the ELBO. Do not use
JIT to hide dynamic-structure bugs.

## Minibatching And Subsampling

### `pyro.plate` Automatic Subsampling

For a dataset where the model can index into data by a subsample, let `plate`
choose minibatches and scale the likelihood to the full data size:

```python
def model(data):
    weight = pyro.sample("weight", dist.Normal(0, 1))
    with pyro.plate("data", len(data), subsample_size=batch_size) as ind:
        batch = data[ind]
        pyro.sample("obs", dist.Normal(weight, 1), obs=batch)
```

The guide must use compatible plate names/dims when it samples local latent
variables. If using autoguides for a model with subsampling, provide a
`create_plates(*args, **kwargs)` callback when the autoguide supports it (for
example `AutoNormal` or `AutoDelta`) so guide-side plates match the model's
subsampled plates.

```python
def create_plates(data):
    return pyro.plate("data", len(data), subsample_size=batch_size, dim=-1)

guide = AutoNormal(model, create_plates=create_plates)
```

### Manual PyTorch DataLoader Pattern

When using a PyTorch dataloader, pass each minibatch to a model whose plate knows
the full dataset size and the current batch size:

```python
class Model(pyro.nn.PyroModule):
    def __init__(self, full_size):
        super().__init__()
        self.full_size = full_size
        self.register_buffer("zero", torch.tensor(0.0))

    def forward(self, covariates, data=None):
        coeff = pyro.sample("coeff", dist.Normal(self.zero, 1.0))
        bias = pyro.sample("bias", dist.Normal(self.zero, 1.0))
        scale = pyro.sample("scale", dist.LogNormal(self.zero, 1.0))
        with pyro.plate("data", self.full_size, len(covariates)):
            loc = bias + coeff * covariates
            return pyro.sample("obs", dist.Normal(loc, scale), obs=data)
```

Then use the ELBO module / `torch.optim` pattern in the optimizer reference.
This is a good fit when the user needs dataloaders, schedulers, ordinary
`torch.nn.Module` composition, or framework integration.

## Low-Level Custom Objective Pattern

When high-level `SVI.step()` is too restrictive, call an ELBO's
`differentiable_loss(model, guide, *args, **kwargs)` directly:

```python
elbo = Trace_ELBO()
loss = elbo.differentiable_loss(model, guide, x_batch, y_batch)
loss = loss / normalizer + regularizer(model, guide)
loss.backward()
optimizer.step()
optimizer.zero_grad()
```

Use this pattern for custom regularizers, manual loss scaling, multiple raw
PyTorch optimizers, or experimental objectives. If you still want high-level
`SVI`, a custom loss callable can be passed as `loss=`; it should accept
`(model, guide, *args, **kwargs)`, trace/replay the model-guide pair correctly,
and return a differentiable tensor when gradients are needed.

## Training Loop Checklist

1. Set seed only when reproducibility matters: `pyro.set_rng_seed(seed)`.
2. Clear stale parameters: `pyro.clear_param_store()` for global-param SVI.
3. Initialize model/guide once if parameters are created lazily, especially
   autoguides and PyTorch optimizer loops.
4. Track both training loss and `evaluate_loss()` on validation data. Use a
   running average for noisy objectives.
5. Guard against non-finite losses and parameters.
6. For gradient explosion, lower the learning rate, use `ClippedAdam`, pass
   `clip_args` to a Pyro optimizer wrapper, or clip manually in a low-level
   `torch.optim` loop.
7. Save both parameters and optimizer state if training will resume. For
   Pyro-optimizer loops, use `pyro.get_param_store().save(...)` and
   `optim.save(...)` / `optim.load(...)`.

## Evaluation And Prediction Handoff

- Use `svi.evaluate_loss(...)` for a no-gradient loss estimate.
- For point summaries from autoguides, prefer `guide.median(...)` or
  `guide.quantiles([...], ...)` when implemented.
- For posterior predictive samples, use `pyro.infer.Predictive` and route
  detailed predictive-shape and return-site debugging to `../mcmc-and-prediction/`.
- Do not use deprecated `SVI.run()` or deprecated `num_samples` on `SVI` for new
  prediction code.

## Discrete Latent Variable Decision

If a model has discrete latent variables:

1. Decide whether they can be enumerated exactly. If yes, use `TraceEnum_ELBO`
   and mark sites for enumeration; route dimension/allocation details to
   `../effect-handlers-and-enumeration/`.
2. If mixing continuous and discrete guide pieces, use `AutoGuideList` with
   blocked submodels so no two guide parts cover the same site. A common pattern
   is a continuous autoguide for continuous sites plus `AutoDiscreteParallel`
   for supported Bernoulli/Categorical/OneHotCategorical sites.
3. If exact enumeration is infeasible, use a custom guide or a relaxation
   strategy and make the approximation explicit. Do not apply a continuous-only
   autoguide to a genuinely discrete latent site without a deliberate transform
   or relaxation.
