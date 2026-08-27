# Autoguide And Optimizer Reference

Use this reference to choose an autoguide, initialize it safely, choose between
Pyro optimizer wrappers and vanilla PyTorch optimizers, and avoid global
parameter-store surprises.

## Autoguide Families

All autoguides are callable guide objects with the same `*args, **kwargs` as the
model. They lazily run the model once to build a prototype trace and infer latent
sites, shapes, supports, and plates.

| Guide | Signature pattern | Best fit | Watch out |
|---|---|---|---|
| `AutoNormal(model, *, init_loc_fn=init_to_feasible, init_scale=0.1, create_plates=None)` | Per-site diagonal normals with human-readable parameters. | General continuous latent variables; works well with `TraceMeanField_ELBO` because sites remain separate. | Continuous sites only; provide `create_plates` for subsampled local latents. |
| `AutoDiagonalNormal(model, init_loc_fn=init_to_median, init_scale=0.1)` | One flattened diagonal Normal over all continuous latents. | Simple ADVI; compact parameterization. | Less transparent parameter names; no `create_plates` argument in this API. |
| `AutoMultivariateNormal(model, init_loc_fn=init_to_median, init_scale=0.1)` | Dense covariance over flattened continuous latents. | Small/medium latent spaces with strong posterior correlations. | O(latent_dim²) parameters; can be expensive. |
| `AutoLowRankMultivariateNormal(model, init_loc_fn=init_to_median, init_scale=0.1, rank=None)` | Low-rank plus diagonal covariance. | Larger correlated latent spaces when dense covariance is too costly. | Choose `rank` deliberately for memory/speed trade-off. |
| `AutoDelta(model, init_loc_fn=init_to_median, *, create_plates=None)` | Delta guide for MAP/MLE-style optimization in constrained space. | MAP estimates, MLE via masked priors, fast point estimates. | Not a posterior uncertainty approximation. |
| `AutoLaplaceApproximation(model, init_loc_fn=init_to_median)` | Train MAP then call `.laplace_approximation()`. | Approximate Gaussian uncertainty around a MAP point. | Hessian can be expensive or ill-conditioned. |
| `AutoNormalizingFlow(model, init_transform_fn)` / `AutoIAFNormal(...)` | Flow-transformed diagonal base distribution. | Non-Gaussian continuous posteriors when extra transform cost is acceptable. | Static latent dimension; transforms may add optional dependencies if user chooses external transform libraries. |
| `AutoGuideList(model, *, create_plates=None)` | Container of blocked autoguides/custom guides. | Mixed continuous/discrete or hybrid custom guide construction. | Block each part so no two parts cover the same sample site. |
| `AutoDiscreteParallel(model, *, create_plates=None)` | Mean-field parallel-enumerated guide for supported discrete sites. | Bernoulli, Categorical, OneHotCategorical discrete guide pieces. | Use with `TraceEnum_ELBO`; unsupported discrete distributions need custom handling. |

Advanced Gaussian/funsor-backed autoguides exist, but funsor is optional and not
part of the minimum verified runtime. Treat funsor-specific behavior as
optional unless the current environment verifies it.

## Initialization Strategies

Autoguide init functions return constrained initial values for each latent site:

| Init function | Use |
|---|---|
| `init_to_feasible` | Robust default for constrained sites; ignores prior parameters. |
| `init_to_sample` | Random prior sample; useful for stochastic restarts. |
| `init_to_median(num_samples=15, fallback=init_to_feasible)` | Empirical prior median when available; good default for many ADVI guides. |
| `init_to_mean(fallback=init_to_median)` | Prior mean when finite and implemented. |
| `init_to_uniform(radius=2.0)` | Random point in unconstrained space. |
| `init_to_value(values={...}, fallback=...)` | Pin site-specific initial values by sample-site name. |
| `init_to_generated(generate=...)` | Produce a fresh initialization strategy once per model execution. |

Pattern for site-specific initialization:

```python
from pyro.infer.autoguide import AutoNormal, init_to_value, init_to_feasible

init_loc_fn = init_to_value(
    values={"scale": torch.tensor(1.0), "offset": torch.tensor(0.0)},
    fallback=init_to_feasible,
)
guide = AutoNormal(model, init_loc_fn=init_loc_fn, init_scale=0.05)
```

Initialization debugging hints:

- If a support/constraint transform fails, inspect the latent distribution's
  support and use a feasible or explicit site value.
- Use a small positive `init_scale` such as `0.01` to `0.1` when early losses are
  unstable; very small scales can slow exploration.
- For heavy-tailed or constrained priors, `init_to_feasible` is often safer than
  random prior samples.

## Constraints And Supports

- `pyro.param(name, init, constraint=...)` stores an unconstrained parameter
  internally and returns a constrained value. Optimizers step the unconstrained
  tensor.
- Guide distribution support must match the model latent support after any
  transforms. For example, a positive model latent needs a positive guide
  distribution, an explicit transformed distribution, or an autoguide that
  handles support transforms.
- `AutoNormal`, `AutoDiagonalNormal`, and other continuous autoguides transform
  constrained latents to unconstrained space and then sample/optimize there.
- If using a custom guide, match the model site's `.to_event(...)` structure and
  event dimension, not merely the visible tensor shape.

## Combining Guides With `AutoGuideList`

Use `AutoGuideList` when no single autoguide owns all sites cleanly.

```python
import pyro.poutine as poutine
from pyro.infer import SVI, TraceEnum_ELBO
from pyro.infer.autoguide import AutoGuideList, AutoNormal, AutoDiscreteParallel

continuous_model = poutine.block(model, hide=["assignment"])
discrete_model = poutine.block(model, expose=["assignment"])

guide = AutoGuideList(model)
guide.append(AutoNormal(continuous_model))
guide.append(AutoDiscreteParallel(discrete_model))

svi = SVI(model, guide, pyro.optim.Adam({"lr": 0.01}), TraceEnum_ELBO(max_plate_nesting=1))
```

Rules:

- Block guide parts by sample-site name or hide/expose functions.
- No two parts should operate on the same sample site.
- The composite guide and all parts must see compatible model args/kwargs.
- Discrete guide parts require enumeration-aware ELBO selection and often
  sibling enumeration guidance.

## Pyro Optimizer Wrappers

`SVI` requires a `pyro.optim.PyroOptim`, not a raw `torch.optim.Optimizer`.
Pyro wrappers dynamically create a PyTorch optimizer for each parameter as it is
encountered.

| Wrapper | Signature pattern | Use |
|---|---|---|
| `pyro.optim.Adam(optim_args, clip_args=None)` | Wraps `torch.optim.Adam`. | Default SVI optimizer. |
| `pyro.optim.ClippedAdam(optim_args)` | Wraps Pyro's clipped Adam implementation. | Adam with built-in gradient clipping and optional learning-rate decay (`lrd`). |
| `pyro.optim.PyroOptim(optim_constructor, optim_args, clip_args=None)` | Wrap any supported optimizer constructor. | Custom optimizer wrappers or per-parameter settings. |
| `pyro.optim.<TorchOptimizer>(optim_args, clip_args=None)` | Generated wrappers for most `torch.optim` optimizers except unsupported closures such as LBFGS. | Use familiar PyTorch optimizers inside high-level `SVI`. |

Basic patterns:

```python
optim = pyro.optim.Adam({"lr": 0.01})
optim = pyro.optim.Adam({"lr": 0.01}, {"clip_norm": 10.0})
optim = pyro.optim.ClippedAdam({"lr": 0.01, "clip_norm": 10.0, "lrd": 0.999})
```

Per-parameter optimizer options can be a callable. The one-argument callable
receives a normalized parameter name:

```python
def optim_args(param_name):
    if param_name.endswith("scale"):
        return {"lr": 0.005}
    return {"lr": 0.02}

optim = pyro.optim.Adam(optim_args)
```

State management:

```python
pyro.get_param_store().save("params.pt")
optim.save("optim.pt")

pyro.get_param_store().load("params.pt")
optim.load("optim.pt", map_location="cpu")
```

Load optimizer state before the relevant parameters are encountered; `PyroOptim`
keeps state waiting until the matching parameter name appears.

## Vanilla PyTorch Optimizer Pattern

Use this when the user needs PyTorch dataloaders, ordinary `torch.optim`, module
checkpointing, schedulers, or framework integration. The key is to turn the ELBO
into a `torch.nn.Module` by calling it on a model/guide pair.

```python
import torch
import pyro
from pyro.infer import Trace_ELBO
from pyro.infer.autoguide import AutoNormal

pyro.settings.set(module_local_params=True)

model = Model(full_size)
guide = AutoNormal(model)
loss_fn = Trace_ELBO()(model, guide)  # torch.nn.Module

# Initialize lazy autoguide/PyroParam parameters before optimizer construction.
first_batch = next(iter(dataloader))
loss_fn(*first_batch)

optimizer = torch.optim.Adam(loss_fn.parameters(), lr=0.01)
for epoch in range(num_epochs):
    for batch in dataloader:
        optimizer.zero_grad()
        loss = loss_fn(*batch)
        loss.backward()
        optimizer.step()
```

Important details:

- `pyro.settings.set(module_local_params=True)` makes `PyroModule` parameters
  behave more like ordinary `torch.nn.Parameter`s instead of being implicitly
  shared by global parameter-store name.
- Run a mini-batch through `loss_fn` before constructing the optimizer so lazy
  autoguide and `PyroParam` parameters exist.
- Use `.to(device)` on model/guide/loss module and tensors for device placement;
  CUDA behavior is optional and not verified by the minimum runtime.
- This pattern is different from high-level `SVI`: you call `loss.backward()` and
  `optimizer.step()` yourself.

## Choosing Between PyroOptim And Torch Optimizers

| Need | Use |
|---|---|
| Fast ordinary Pyro SVI with `pyro.param` and dynamically appearing params | High-level `SVI` + `pyro.optim.Adam` or `ClippedAdam`. |
| Per-parameter learning rates or clipping while keeping high-level SVI | `pyro.optim.Adam(callable_or_dict, clip_args=...)`. |
| Multiple torch optimizer algorithms in one custom loop | Low-level `Trace_ELBO().differentiable_loss(...)` or `ELBO.__call__` module pattern. |
| Dataloaders, schedulers, framework integration, ordinary module checkpointing | ELBO module + `torch.optim`. |
| `PyroModule` instances should not share params by global names | `pyro.settings.set(module_local_params=True)` and ELBO module pattern. |

## Flow Guide Caveats

- `AutoNormalizingFlow` expects an `init_transform_fn(latent_dim)` that returns a
  transform or transform module.
- `AutoIAFNormal` creates affine autoregressive transforms and is a convenient
  built-in flow guide for continuous latents.
- Flow guides are more expressive but slower and more sensitive to initialization
  and learning rate. Start with `AutoNormal` or `AutoDiagonalNormal` to establish
  a baseline.
- External flow libraries or contrib adapters are optional; do not assume they
  are installed unless the user's environment confirms them.
