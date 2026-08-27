# Enumeration And Reparameterization

This reference covers Pyro 1.9.1 discrete enumeration, posterior decoding,
Tensor Monte Carlo caveats, poutine reparameterizers, and selected `pyro.ops`
utilities that commonly support inference code.

## When To Enumerate

Enumeration is for discrete latent variables whose distributions implement
`enumerate_support()` and expose `has_enumerate_support=True`, for example
`Bernoulli`, `Categorical`, and compatible discrete distributions.

Use enumeration when:

- a discrete latent variable appears in a model and a continuous autoguide would
  be invalid;
- exact marginalization is tractable because the discrete dependency graph has
  narrow treewidth;
- you need posterior MAP or sampled discrete states after conditioning on
  observations;
- you need to reduce score-function variance in SVI by summing out discrete
  choices.

Avoid or rethink enumeration when:

- a parallel-enumerated value controls Python branching, tensor shapes, or loop
  counts; use sequential enumeration in the guide or rewrite to tensorized code;
- the number of dependent discrete variables creates wide treewidth or huge
  enum tensors;
- the target is generic MCMC over discrete variables; Pyro's HMC/NUTS do not
  directly sample discrete latent sites;
- a domain-specific `pyro.contrib.funsor` workflow is required but `funsor` is
  not installed in the active environment.

## Core Enumeration API Map

| API | Signature pattern | Use | Notes |
|---|---|---|---|
| `config_enumerate(guide=None, default="parallel", expand=False, num_samples=None, tmc="diagonal")` | decorator or function | Annotate sample sites with enumeration metadata. | Exhaustive mode annotates unobserved sample sites whose distribution has enumerable support. With `num_samples`, performs local parallel Monte Carlo sampling. Does not overwrite existing `infer={"enumerate": ...}`. |
| `TraceEnum_ELBO(...)` | common args include `num_particles`, `max_plate_nesting`, `vectorize_particles`, `strict_enumeration_warning`, `ignore_jit_warnings`, `jit_options` | SVI ELBO that supports exhaustive discrete enumeration and local parallel sampling. | Model-side enumeration must be `parallel`; guide sites may be `parallel` or `sequential`. |
| `JitTraceEnum_ELBO(...)` | same core args as `TraceEnum_ELBO` | JIT-compiled enum ELBO for static-structure models. | Use only when model/guide structure is static. Tensor inputs should be passed via args; non-tensor compile keys via kwargs. |
| `infer_discrete(fn=None, first_available_dim=None, temperature=1, strict_enumeration_warning=True)` | decorator or wrapper | Sample (`temperature=1`) or MAP decode (`temperature=0`) model-enumerated discrete sites conditioned on observations. | Requires negative `first_available_dim`. Log probabilities in the inferred trace are not meaningful for the inferred model. |
| `TraceEnum_ELBO.compute_marginals(model, guide, ...)` | method on `TraceEnum_ELBO(num_particles=1)` | Compute marginal distributions at model-enumerated sites. | Not compatible with multiple particles or guide enumeration. |
| `TraceEnum_ELBO.sample_posterior(model, guide, ...)` | method on `TraceEnum_ELBO(num_particles=1)` | Sample joint posterior of model-enumerated sites. | Not compatible with multiple particles or guide enumeration. |
| `TraceTMC_ELBO(...)` | imported from `pyro.infer` | Tensor Monte Carlo / local parallel sampling objective. | Use `config_enumerate(..., num_samples=N, tmc="diagonal" or "mixture")`. JIT TMC is not available in the standard 1.9.1 API. |
| `poutine.enum(fn=None, first_available_dim=None)` | wrapper for diagnostics | Apply the parallel enumeration messenger directly. | Mostly useful to inspect shapes with `poutine.trace(poutine.enum(...))`. |
| `iter_discrete_traces(graph_type, fn, *args, **kwargs)` | from `pyro.infer.enum` | Iterate sequentially over all discrete choices. | Exponential in number of sites; useful for tiny exact checks. |

## TraceEnum_ELBO Workflow

Minimal finite mixture pattern:

```python
import torch
import pyro
import pyro.distributions as dist
from torch.distributions import constraints
from pyro.infer import SVI, TraceEnum_ELBO, config_enumerate
from pyro.optim import Adam
from pyro.ops.indexing import Vindex


@config_enumerate
def model(data):
    weights = pyro.param("weights", torch.tensor([0.5, 0.5]), constraint=constraints.simplex)
    locs = pyro.param("locs", torch.tensor([-1.0, 1.0]))
    scale = pyro.param("scale", torch.tensor(0.5), constraint=constraints.positive)
    with pyro.plate("data", data.size(0), dim=-1):
        z = pyro.sample("z", dist.Categorical(weights), infer={"enumerate": "parallel"})
        pyro.sample("obs", dist.Normal(Vindex(locs)[z], scale), obs=data)


def guide(data):
    # No guide site for model-enumerated z; it is marginalized by TraceEnum_ELBO.
    pass

pyro.clear_param_store()
elbo = TraceEnum_ELBO(max_plate_nesting=1)
svi = SVI(model, guide, Adam({"lr": 0.02}), elbo)
for step in range(num_steps):
    loss = svi.step(data)
```

Key rules:

1. Mark every target model-side discrete site with
   `infer={"enumerate": "parallel"}` or wrap the model/guide with
   `config_enumerate`.
2. If a model site is enumerated in the model, it should not appear in the
   guide. If it appears in the guide, that is guide-side enumeration instead.
3. Use `TraceEnum_ELBO(max_plate_nesting=N)` where `N` is the maximum number of
   nested vectorized `pyro.plate` contexts around enumerated or dependent
   observed sites. For one data plate, `N=1`.
4. Parallel-enumerated sample values acquire extra singleton/enum dimensions.
   All downstream indexing and distributions must broadcast correctly.
5. Use `Vindex(tensor)[...]` or explicit broadcasting rather than ordinary
   advanced indexing when indexing tensors by enumerated variables.
6. Model-side `infer={"enumerate": "sequential"}` is not implemented. Use
   guide-side sequential enumeration or rewrite the model.
7. Keep all model-enumerated sites sharing a common scalar `poutine.scale` if
   scaled dependent likelihood terms are present. Per-element likelihood masks
   are handled with `poutine.mask`.

## Parallel vs Sequential Enumeration

| Strategy | Best for | Limitations |
|---|---|---|
| `"parallel"` | Fast exact marginalization by adding enum tensor dimensions. Works well for mixtures, HMMs, finite-state time series, and small discrete structures. | Downstream code must be vectorized/broadcasting-safe. Cannot branch on an enumerated tensor value. Requires dim allocation. |
| `"sequential"` | Discrete choices that affect Python control flow or dynamic structure, mainly in guides and low-cardinality checks. | Runs the model/guide repeatedly and can be exponentially expensive. Model-side sequential enumeration is not implemented for `TraceEnum_ELBO`. |
| `num_samples=N` with `default="parallel"` | Local parallel Monte Carlo / TMC when exhaustive enumeration is too expensive or for continuous sites under TMC. | Approximate; TMC assumptions and gradient warnings matter. `default="sequential"` with `num_samples` is invalid. |

## Dimension Allocation: `max_plate_nesting` And `first_available_dim`

Pyro counts tensor dimensions from the right. Vectorized plates occupy the
rightmost available negative dims such as `-1`, `-2`, etc. Parallel enumeration
uses dimensions to the left of those plates.

- For `TraceEnum_ELBO(max_plate_nesting=N)`, Pyro starts guide enumeration at
  `first_available_dim = -1 - N`, then model enumeration uses dims further left.
- For standalone `infer_discrete`, supply the same formula manually:
  `first_available_dim = -1 - max_plate_nesting`.
- In a model with one `pyro.plate("data", ..., dim=-1)`, use
  `max_plate_nesting=1` and `first_available_dim=-2`.
- In a model with plates at `dim=-1` and `dim=-2`, use
  `max_plate_nesting=2` and `first_available_dim=-3`.
- `max_plate_nesting=float("inf")` lets Pyro guess plate nesting for some ELBOs,
  but parallel enumeration needs a finite value once enum dimensions are
  allocated. Prefer an explicit finite integer for enum-heavy code.
- `pyro.markov(range(T))` helps Pyro recycle enum dimensions in Markov models;
  without it, each time step may need a fresh enum dimension.

Diagnostic pattern:

```python
import pyro.poutine as poutine

tr = poutine.trace(poutine.enum(model, first_available_dim=-1 - max_plate_nesting)).get_trace(data)
tr.compute_log_prob()
print(tr.format_shapes())
for name, site in tr.iter_stochastic_nodes():
    print(name, site["infer"].get("_enumerate_dim"), tuple(site["value"].shape))
```

## Posterior Discrete States With `infer_discrete`

`TraceEnum_ELBO` marginalizes discrete values during learning; it does not by
itself return assignments. Use `infer_discrete` to get posterior samples or MAP
assignments after conditioning on observations.

```python
from pyro.infer import config_enumerate, infer_discrete
import pyro.poutine as poutine

# Sample from p(z | observations).
posterior_model = infer_discrete(
    config_enumerate(model),
    first_available_dim=-1 - max_plate_nesting,
    temperature=1,
)
trace = poutine.trace(posterior_model).get_trace(data)
z_sample = trace.nodes["z"]["value"]

# MAP / Viterbi-like decode.
map_model = infer_discrete(
    config_enumerate(model),
    first_available_dim=-1 - max_plate_nesting,
    temperature=0,
)
z_map = poutine.trace(map_model).get_trace(data).nodes["z"]["value"]
```

Caveats:

- `temperature` is currently `1` for posterior sampling or `0` for MAP; other
  values raise an error.
- If no sites are configured for enumeration, `infer_discrete` warns unless
  `strict_enumeration_warning=False`.
- The log probabilities in a trace of the `infer_discrete`-wrapped model are not
  a reliable posterior log probability. Use it for values/returns, not scoring.
- If a non-empty guide was trained, replay the guide/sample trace into the model
  or use `TraceEnum_ELBO.sample_posterior()` when its restrictions fit. For
  ordinary posterior predictive workflows, route to `../../mcmc-and-prediction/SKILL.md`.

## HMM And Time-Series Enumeration Patterns

For finite-state HMMs:

```python
def hmm(data, transition, locs):
    state = 0
    for t in pyro.markov(range(len(data))):
        state = pyro.sample(
            f"state_{t}",
            dist.Categorical(transition[state]),
            infer={"enumerate": "parallel"},
        )
        pyro.sample(f"obs_{t}", dist.Normal(locs[state], 1.0), obs=data[t])
```

Practical notes:

- `pyro.markov` marks local dependency scope and enables enum-dim recycling in
  Markov chains.
- `Trace.format_shapes()` should show enum dimensions alternating/reusing across
  time rather than growing unbounded when the Markov structure is simple.
- Use `Vindex` whenever indexing a transition or emission tensor by enumerated
  current/previous states and additional plate indices.
- HMM examples with `TraceTMC_ELBO`, JIT, and funsor are useful evidence but are
  not minimum-runtime guarantees. Distill their patterns rather than requiring
  their optional extras.

## Tensor Monte Carlo Caveats

`TraceTMC_ELBO` supports local parallel sampling and exhaustive enumeration via
`config_enumerate(..., num_samples=N, tmc=...)`:

```python
from pyro.infer import TraceTMC_ELBO, config_enumerate

tmc_model = config_enumerate(model, default="parallel", num_samples=10, tmc="diagonal")
elbo = TraceTMC_ELBO(max_plate_nesting=1)
loss = elbo.loss(tmc_model, guide, data)
```

Caveats from the Pyro 1.9.1 implementation and tests:

- `tmc` is usually `"diagonal"` or `"mixture"`; invalid strategies raise a
  `ValueError`.
- `default="sequential"` with `num_samples` is invalid; local sampling requires
  parallel-style sampling.
- Different `num_samples` values across guide sites can trigger a bias warning
  if the guide is not factorized.
- Model-side multiply sampled sites without guide sampling can produce incorrect
  gradient estimates; prefer exact enumeration or guide sampling when possible.
- JIT support for TMC is not available in the standard 1.9.1 `TraceTMC_ELBO`
  workflow. Do not claim a `JitTraceTMC_ELBO` path unless the active environment
  proves a different backend supplies it.

## Funsor Caveats

`funsor` is optional in the minimum environment. Treat all of the following as
optional/unverified unless `import funsor` and `import pyro.contrib.funsor`
succeed in the user's runtime:

- `pyro.contrib.funsor` backend and named-dimension handlers;
- funsor HMM examples and tests;
- `poutine.collapse`, which lazily samples/collapses sites by converting
  distributions and values to Funsors;
- contributed funsor implementations of enumeration, TMC, and vectorized Markov
  workflows.

If `poutine.collapse` is used and plates appear inside the collapsed context,
manually declare `max_plate_nesting` in the inference algorithm. It is not
compatible with automatic plate-nesting guessing.

## Reparameterization With `poutine.reparam`

Reparameterizers rewrite a sample site into auxiliary sample site(s) plus a
deterministic transform. They are used to improve posterior geometry, enable
log probabilities for otherwise difficult distributions, or prepare a model for
MCMC/SVI.

Basic pattern:

```python
import pyro.poutine as poutine
from pyro.infer.reparam import LocScaleReparam, AutoReparam

# Explicit site config.
model_reparam = poutine.reparam(model, config={"theta": LocScaleReparam(centered=0.0)})

# Callable or automatic strategy.
strategy = AutoReparam(centered=0.0)
model_reparam = poutine.reparam(model, config=strategy)
# or as decorator-like wrapper:
model_reparam = strategy(model)
```

Available public reparameterizers in this API family include:

| Reparam | Typical use | Important limits |
|---|---|---|
| `MinimalReparam()` | Apply only reparams needed to avoid errors, e.g. stable/projected normal cases. | Strategy behavior depends on distribution types. |
| `AutoReparam(centered=None)` | Recommended automatic mix: minimal, transform, loc-scale, Gumbel-softmax. | Behavior may change across Pyro releases; inspect `strategy.config` after a run if reproducibility matters. |
| `LocScaleReparam(centered=None, shape_params=None)` | Center/decenter latent location-scale distributions such as Normal/StudentT-like sites. | Latent variables only, unconstrained support, parameter names include `loc` and `scale`. `centered=0.0` is fully decentered; `1.0` preserves centered. |
| `TransformReparam()` | Move a `TransformedDistribution` latent into base distribution space. | Latent variables only. |
| `GumbelSoftmaxReparam()` | Reparameterize `RelaxedOneHotCategorical` latents. | Increases latent dimension by one per event; not for likelihoods. |
| `StableReparam`, `SymmetricStableReparam`, `LatentStableReparam` | Use stable distributions in likelihood-based inference where direct `log_prob` may be unavailable. | Choose latent vs likelihood-compatible variant according to site role and skew/symmetry. |
| `StudentTReparam()` | Auxiliary Gamma/Normal representation; useful with HMM reparameterization. | Introduces auxiliary variables. |
| `ProjectedNormalReparam()` | Projected normal latent variables. | Latent variables only. |
| `LinearHMMReparam(init=None, trans=None, obs=None)` | Reparameterize `LinearHMM` into a Gaussian-HMM-compatible form using component reparams. | Useful when `LinearHMM.log_prob` is undefined; carefully inspect shapes. |
| `DiscreteCosineReparam(dim=-1, smooth=0.0, experimental_allow_batch=False)` and `HaarReparam(dim=-1, flip=False, experimental_allow_batch=False)` | Frequency/wavelet transforms for time-like latent dimensions with long-range correlation. | `dim` must be negative. Batch-coupling option is experimental. |
| `UnitJacobianReparam(transform, suffix="transformed", experimental_allow_batch=False)` | Apply a unit-Jacobian transform. | Converts targeted batch dims to event dims if batch coupling is enabled. |
| `SplitReparam(sections, dim, support_fn=...)` | Split a tensor latent into pieces for different inference/reparam treatment. | Similar to `torch.split`; verify support and event dims. |
| `NeuTraReparam(guide)` | Use a trained `AutoContinuous` guide as neural transport for MCMC. | All sites share one instance; model needs static latent structure; train the guide first. |
| `StructuredReparam(guide)` | Use a trained `AutoStructured` guide for preconditioned MCMC. | Static structure and guide compatibility required. |
| `ConjugateReparam(guide)` | Replace prior with a conjugate-updated distribution where available. | Experimental; requires distributions implementing conjugate update behavior. |

Reparameterization checklist:

1. Apply the reparameterized model consistently to the actual inference object,
   not only to diagnostics.
2. Trace before and after reparameterization and inspect auxiliary site names,
   event dims, and `format_shapes()`.
3. Do not use latent-only reparameterizers for observed likelihood sites unless
   the class explicitly supports likelihoods.
4. If initialization, `condition`, or `replay` does not commute with a reparam,
   expect warnings or default initialization fallback.
5. Some reparameterizers examine model args/kwargs. Prefer
   `reparam_model = poutine.reparam(model, config=...)` over an inner `with`
   context if the reparam class needs access to call arguments.

## Selected `pyro.ops` Utilities For Inference Work

These are not a general tensor-utility catalog; they are high-value utilities
encountered in enumeration, HMM, prediction diagnostics, and inference code.

| Utility | Use in inference tasks | Notes |
|---|---|---|
| `pyro.ops.indexing.Vindex` / `vindex` | Broadcasting-safe indexing by enumerated discrete variables and plate indices. | Prefer for mixture/HMM parameters under parallel enumeration. |
| `pyro.ops.contract.einsum(equation, *operands, plates=..., backend=...)` | Plated sum-product / tensor variable elimination; underlies TMC-style contractions. | Backends include `pyro.ops.einsum.torch_log`, `torch_map`, `torch_sample`, `torch_marginal` for specialized adjoint algorithms. |
| `pyro.ops.einsum.contract` / `contract_expression` | Thin wrappers around `opt_einsum` with Pyro path caching options. | Use for ordinary optimized tensor contractions. |
| `pyro.ops.gaussian.Gaussian`, `gaussian_tensordot`, `sequential_gaussian_tensordot`, `sequential_gaussian_filter_sample` | Gaussian message passing and HMM/state-space inference internals. | Mostly advanced; route distribution constructor questions to `../../distributions-and-shapes/SKILL.md`. |
| `pyro.ops.gamma_gaussian.GammaGaussian`, `gamma_gaussian_tensordot` | Gamma-Gaussian conjugate/message passing internals. | Advanced and shape-sensitive. |
| `pyro.ops.stats.gelman_rubin`, `split_gelman_rubin`, `effective_sample_size`, `hpdi`, `quantile`, `waic`, `resample`, `weighed_quantile` | Posterior sample diagnostics/summaries after SVI/MCMC/predictive sampling. | Route MCMC diagnostics to `../../mcmc-and-prediction/SKILL.md` when the question is about chains/sampling. |
| `pyro.ops.streaming.*Stats` | Online/streamed statistics for dicts or tensors of samples. | Useful for memory-bounded posterior summaries. |
| `pyro.ops.tensor_utils.dct`, `idct`, `haar_transform`, `inverse_haar_transform` | Support DCT/Haar reparameterizers and time-series transforms. | Prefer public reparameterizers unless writing low-level transforms. |
| `pyro.ops.jit.trace` | Lazy `torch.jit.trace` wrapper that understands `pyro.param`. | Use only for static structure and after non-JIT code works. |

## Native Evidence Patterns To Recognize

Native Pyro evidence exercised these patterns:

- toy mixture enumeration: `config_enumerate`, `TraceEnum_ELBO(max_plate_nesting=1)`,
  `infer={"enumerate": "parallel"}`, and `Vindex` for enumerated indexing;
- HMM enumeration: `pyro.markov`, enum dimensions to the left of plates, optional
  `TraceTMC_ELBO`, and `Trace.format_shapes()` diagnostics;
- discrete posterior tests: `infer_discrete(..., temperature=0/1)` and
  `first_available_dim = -1 - max_plate_nesting`;
- poutine tests: trace/replay/condition/block/scale/mask/substitute ordering and
  trace node assertions;
- reparam tests: explicit `poutine.reparam(model, {"site": Reparam(...)})`,
  auxiliary-site shape checks, and initialization caveats;
- ops tests: plated einsum, Gaussian HMM contractions, posterior stats, and
  streaming summaries.
