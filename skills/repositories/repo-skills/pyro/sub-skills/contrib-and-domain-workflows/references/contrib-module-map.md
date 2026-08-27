# Pyro Contrib Module Map

This reference maps `pyro.contrib` in the Pyro 1.9.1 API family. Contributed
code is useful but less stable than the core package: Pyro's own contrib README
and package docstring say these modules are under various stages of development
and make no backwards-compatibility guarantee. When answering a user, state that
risk for contrib-specific APIs and prefer core Pyro primitives/inference when a
stable core solution is sufficient.

## Stability And Optionality Rules

- **Core-stable handoff:** `pyro`, `pyro.distributions`, `pyro.infer`,
  `pyro.poutine`, `pyro.nn`, and `pyro.optim` mechanics belong to sibling
  sub-skills and are generally safer than `pyro.contrib` wrappers.
- **Contrib-stability warning:** any `pyro.contrib.*` API can change across Pyro
  releases. Pin Pyro and smoke-test important code when upgrading.
- **Minimum runtime expectation:** base Pyro plus CPU PyTorch should cover core
  modules and much of `pyro.contrib`; optional extras such as Funsor, Graphviz,
  Horovod, Lightning, torchvision, pandas, and scanpy are not guaranteed. Probe
  them in the active environment before use.
- **Do not overclaim extras:** example scripts often need plotting, data,
  torchvision, pandas, scanpy, scikit-learn, or distributed runtimes even when
  the underlying contrib module imports.

## Module Map

| Module | Maturity / stability | Best-fit tasks | Main entry points | Optional deps / caveats | Sibling handoffs |
|---|---|---|---|---|---|
| `pyro.contrib.minipyro` | Didactic minimal implementation; intentionally limited, not a production backend. | Teach effect handlers, param store, SVI, MiniPyro vs full Pyro, `pyro.generic` backend switching. | `sample`, `param`, `plate`, `trace`, `replay`, `block`, `seed`, `SVI`, `Trace_ELBO`, `JitTrace_ELBO`, `Adam`, `get_param_store`. | Depends on Pyro distributions and PyTorch. `plate` requires explicit `dim`; many full-Pyro features are not implemented. | Route full SVI mechanics to `../svi-and-autoguides/`; route effect-handler semantics to `../effect-handlers-and-enumeration/`. |
| `pyro.generic` / `pyroapi` | `pyro.generic` is deprecated shim; it warns that it moved to `pyroapi`. | Backend-agnostic examples that can run against `pyro` or `minipyro`; testing interface parity. | `pyro_backend`, `pyro`, `distributions`, `handlers`, `infer`, `optim`, `ops`. | `pyro-api` is a base dependency. Backends differ; handle `NotImplementedError` for MiniPyro. | Route ordinary Pyro implementation details to core siblings. |
| `pyro.contrib.gp` | Contrib API; substantial test coverage, but still subject to contrib compatibility warning. | Gaussian-process regression/classification, sparse/variational GP, GPLVM, kernels, likelihoods, Bayesian optimization support. | Models: `GPRegression`, `SparseGPRegression`, `VariationalGP`, `VariationalSparseGP`, `GPLVM`; kernels: `RBF`, `Matern32`, `Matern52`, `Periodic`, `Cosine`, `Linear`, `WhiteNoise`; likelihoods: `Gaussian`, `Binary`, `MultiClass`, `Poisson`; utility `train`. | Core GP module is CPU-safe. Deep-kernel/MNIST examples need torchvision, scikit-learn, matplotlib and can be long. GP Cholesky may need `jitter` and O(N^3) memory. | SVI/MCMC training choices to `../svi-and-autoguides/` or `../mcmc-and-prediction/`; shape/kernel tensor debugging to `../distributions-and-shapes/`. |
| `pyro.contrib.forecast` | Lightweight contrib framework; stable enough for documented examples but not a core API. | Hierarchical multivariate time-series forecasting, future joint posterior samples, GaussianHMM/LinearHMM-based temporal likelihoods, SVI/HMC forecasting. | `ForecastingModel`, `Forecaster`, `HMCForecaster`, `backtest`, `eval_mae`, `eval_rmse`, `eval_crps`; model methods use `self.time_plate` and `self.predict(...)`. | BART example may download/cache large ridership data unless replaced by fake data. Plotting is optional. Time dimension is special; do not put it in arbitrary plates. | HMM shapes to `../distributions-and-shapes/`; SVI/HMC details to inference siblings; reparameterizers to `../effect-handlers-and-enumeration/`. |
| `pyro.contrib.epidemiology` | Explicit under-development warning in docs. | Discrete-time discrete-count compartmental models, SIR/SEIR variants, regional epidemic models, SVI/HMC/prediction/forecasting. | `CompartmentalModel`; model classes including `SimpleSIRModel`, `SimpleSEIRModel`, `Overdispersed*`, `Superspreading*`, `HeterogeneousSIRModel`, `RegionalSIRModel`; distributions `binomial_dist`, `beta_binomial_dist`, `infection_dist`; fit methods on model objects. | Double precision is recommended by implementation warnings; examples can be long and have `--cuda`, `--plot`, `--jit` flags. Plotting can need matplotlib/seaborn. | MCMC/SVI tuning to inference siblings; enumeration/SMC/reparameterizer internals to `../effect-handlers-and-enumeration/`. |
| `pyro.contrib.tracking` | Contrib research module. | Multi-object tracking, marginal data association, extended Kalman filter, dynamic/measurement models, hashing for approximate sets. | `assignment.compute_marginals*`, `EKFState`, `EKFDistribution`, dynamic models `Ncp*`, `Ncv*`, `PositionMeasurement`, `LSH`, `ApproxSet`. | Mostly tensor/Pyro code in module tests; domain users must supply sensor data and units. EKF state needs consistent time/frame and covariance shapes. | Distribution and tensor-shape errors to `../distributions-and-shapes/`; poutine/inference composition to core siblings if fitting a full model. |
| `pyro.contrib.easyguide` | Contrib guide authoring helper. | Custom guides that are easier than raw guide code but more flexible than autoguides; grouping multiple sites; MAP, multivariate Normal, Delta choices. | `EasyGuide`, `easy_guide`, `self.group(...)`, `self.plate(...)`, `Group.map_estimate`, `Group.normal`, `Group.delta` methods. | Does not support sequential `pyro.plate`; guide initialization depends on prototype trace. | General guide and SVI logic to `../svi-and-autoguides/`; poutine trace issues to `../effect-handlers-and-enumeration/`. |
| `pyro.contrib.bnn` | Older contrib building block. | Bayesian neural network hidden layer distribution using local reparameterization trick. | `HiddenLayer(X, A_mean, A_scale, non_linearity=..., KL_factor=..., A_prior_scale=..., include_hidden_bias=...)`. | User must scale KL factor correctly for minibatches. Prefer modern `PyroModule`/autoguide patterns when possible. | SVI and module parameter patterns to `../svi-and-autoguides/` and `../modeling-basics/`. |
| `pyro.contrib.cevae` | Contrib implementation of Causal Effect VAE; self-contained but training-heavy. | Causal effect inference with hidden confounders, twin neural nets, counterfactual queries. | `CEVAE`, `Model`, `Guide`, `TraceCausalEffect_ELBO`, `FullyConnected`, distribution net classes. | Requires user-provided tensors and careful outcome/treatment feature schema. Training can be long; examples/tutorials are not quick smoke tests. | SVI/autoguide mechanics to `../svi-and-autoguides/`; data/schema validation belongs here before handoff. |
| `pyro.contrib.oed` | Experimental design contrib; research-oriented. | Bayesian optimal experimental design, expected information gain (EIG), average posterior entropy (APE), adaptive design search. | EIG estimators `nmc_eig`, `vi_eig`, `laplace_eig`, `donsker_varadhan_eig`, `posterior_eig`, `marginal_eig`, `lfire_eig`, `vnmc_eig`; `Search`. | Examples can be compute-heavy; BO examples use GP utilities. Requires clear `observation_labels`, `target_labels`, and design tensor semantics. | ELBO/SVI internals to `../svi-and-autoguides/`; enumeration if using `TraceEnum_ELBO` to `../effect-handlers-and-enumeration/`. |
| `pyro.contrib.timeseries` | Older contrib time-series model collection. | Temporal Gaussian processes, linear Gaussian state-space models, forecasting distributions. | `TimeSeriesModel`, `IndependentMaternGP`, `LinearlyCoupledMaternGP`, `DependentMaternGP`, `GenericLGSSM`, `GenericLGSSMWithGPNoiseModel`. | Example plotting is optional. Verify target shape `(T, obs_dim)` and forecast time deltas `dts`. | For forecasting framework use `pyro.contrib.forecast`; for HMM distribution details route to `../distributions-and-shapes/`. |
| `pyro.contrib.funsor` | Optional backend; only importable when `funsor[torch]` is installed. | Funsor-backed Pyro backend via `pyroapi`, named dimensions, `markov`, `vectorized_markov`, Funsor ELBO/TMC enumeration. | `pyro.contrib.funsor.sample`, `plate`, `markov`, `vectorized_markov`, `to_data`, `to_funsor`; backend name `contrib.funsor`. | `funsor[torch]==0.4.8` is Pyro's pinned extra. Use ordinary Pyro enumeration when Funsor is unavailable. | Enumeration mechanics to `../effect-handlers-and-enumeration/`; optional install/skip policy to optional integrations. |
| `pyro.contrib.mue` | Explicit under-development warning in docs. | Biological sequence models, MuE distributions, profile HMMs, missing/variable-length biosequence HMMs. | `ProfileHMM`, `FactorMuE`, `MissingDataDiscreteHMM`, `BiosequenceDataset`, state arrangers. | Examples use biosequence data, plotting, possible GPU/pinned-memory flags; not selected for minimum verification. Ask for data and runtime budget. | HMM shapes to `../distributions-and-shapes/`; SVI loops to `../svi-and-autoguides/`. |
| `pyro.contrib.zuko` | Thin adapter; requires user's zuko package for actual flows. | Wrap a Zuko distribution/flow as a Pyro distribution. | `ZukoToPyro(dist)`; caches `rsample_and_log_prob` when available. | `zuko` is not a Pyro extra in setup; user must install it separately. Tutorial flow examples also may use torchvision. | Flow event shapes to `../distributions-and-shapes/`; SVI flow guides to `../svi-and-autoguides/`. |
| `pyro.contrib.randomvariable` | Small experimental syntax helper. | Algebra on random variables via transformed distributions. | `RandomVariable(distribution)` plus arithmetic / transform-like magic operations. | Experimental convenience layer; prefer explicit `TransformedDistribution` for production clarity. | Transform/support issues to `../distributions-and-shapes/`. |
| `pyro.contrib.autoname` | Experimental effect-handler naming helper. | Generate unique, semantically meaningful names for sample sites, scope nested stochastic functions. | `autoname`, `sample`, `scope`, `name_count`, `named` containers. | Alters sample-site naming; can surprise guides/inference if names differ from expected. | Duplicate-name and poutine handler semantics to `../effect-handlers-and-enumeration/`; basic site naming to `../modeling-basics/`. |
| `pyro.contrib.conjugate` | Small contrib inference helper. | Specialized conjugate inference experiments. | `pyro.contrib.conjugate.infer` APIs. | Not part of root `pyro.contrib.__all__`; use only with direct evidence and tests. | Core inference questions to inference siblings. |
| `pyro.contrib.examples` | Dataset and helper utilities, not modeling APIs. | Load example datasets such as fake/BART, Nextstrain, finance, MultiMNIST, scANVI data helpers. | `load_fake_od`, `load_bart_od`, dataset utilities. | Many helpers download data or require torchvision, pandas, PIL, scanpy/scvi. Treat as reference-only unless user approves data/downloads and dependencies. | Domain workflow notes here; training mechanics to siblings. |

## Generic Backend / MiniPyro Decision

Use MiniPyro when the user wants a **teaching or debugging** view of Pyro's core
ideas: effect stack, trace/replay, param store, basic SVI, or a backend-agnostic
snippet using `pyroapi`. Do not use MiniPyro to answer whether a production Pyro
model supports advanced handlers, autoguides, enumeration, MCMC, prediction,
CUDA, or complex plate behavior.

Safe backend-agnostic pattern:

```python
from pyro.generic import distributions as dist
from pyro.generic import infer, optim, pyro, pyro_backend

with pyro_backend("pyro"):       # or "minipyro" for didactic limited backend
    pyro.get_param_store().clear()
    svi = infer.SVI(model, guide, optim.Adam({"lr": 0.02}), infer.Trace_ELBO())
    loss = svi.step(data)
```

If a MiniPyro backend raises `NotImplementedError`, treat that as a backend
limitation, not proof that full Pyro lacks the feature.

## Contrib vs Core SVI For Time Series

Choose `pyro.contrib.forecast` when the user needs the framework's assumptions:
explicit time plate, future joint samples, forecasting metrics/backtests,
Gaussian variable elimination over temporal structure, or `HMCForecaster` for a
forecasting model.

Choose a core `pyro` model plus SVI/MCMC when the user needs a custom dynamic
model that does not fit `ForecastingModel.model(zero_data, covariates)` or
`self.predict(noise_dist, prediction)`, when the data are tiny and a direct model
is clearer, or when contrib stability is unacceptable.

Choose Pyro HMM distributions (`GaussianHMM`, `DiscreteHMM`, `LinearHMM`, etc.)
without the forecasting framework when the main issue is scoring/sampling a
sequence distribution, not fitting a forecasting model.
