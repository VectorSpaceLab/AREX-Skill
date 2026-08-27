# Domain Workflows And Safe Tiny Patterns

This reference distills Pyro domain example families into self-contained routing
and tiny/mock command concepts. It does not require the original example files or
tutorial notebooks at runtime. Use it to answer "which Pyro surface fits this
domain?", to avoid optional dependency overclaims, and to decide when to ask for
data, GPU, network access, or more time.

## How To Use Domain Evidence Safely

1. Identify the domain and the user's deliverable: model sketch, debugging help,
   runnable prototype, or faithful long tutorial reproduction.
2. Prefer a tiny synthetic/mock dataset unless the user explicitly provides real
   data and approves download/training time.
3. Separate **domain routing** from **core mechanics**. This sub-skill chooses
   the contributed module or example family; SVI/MCMC/shape/enumeration details
   belong to sibling sub-skills.
4. Treat example command concepts below as patterns, not runtime requirements.
   They are derived from versioned repository evidence and should be
   reimplemented in the user's working project or replaced by bundled root smoke
   scripts when those exist.
5. If a workflow needs optional extras, state that they are optional/unverified
   until the active environment proves availability.

## Forecasting And Time Series

### `pyro.contrib.forecast`

Best fit for hierarchical or multivariate forecasting where the model can be
written as a subclass of `ForecastingModel`:

- implement `model(self, zero_data, covariates)`;
- draw global parameters normally;
- draw time-dependent noise inside `self.time_plate`;
- call `self.predict(noise_dist, prediction)` exactly once;
- fit via `Forecaster(...)` for SVI or `HMCForecaster(...)` for HMC;
- call the fitted forecaster with extended covariates to obtain future samples.

Safe tiny concept:

```python
import torch, pyro
import pyro.distributions as dist
from pyro.contrib.forecast import ForecastingModel, Forecaster

class LocalLevel(ForecastingModel):
    def model(self, zero_data, covariates):
        scale = pyro.sample("scale", dist.LogNormal(zero_data.new_tensor(-1.0), 0.2))
        with self.time_plate:
            innovations = pyro.sample("innov", dist.Normal(0.0, scale))
        prediction = innovations.cumsum(-1).unsqueeze(-1) + zero_data
        self.predict(dist.Normal(0.0, 0.1), prediction)

data = torch.randn(8, 1)
covariates = torch.empty(8, 0)
pyro.clear_param_store()
forecaster = Forecaster(LocalLevel(), data, covariates, num_steps=2, log_every=1)
future_covariates = torch.empty(10, 0)  # train length + two future steps
samples = forecaster(data, future_covariates, num_samples=3)
assert samples.shape[-2:] == (2, 1)
```

Ask for more constraints before a real forecast: forecast horizon, covariate
schema, observation transform (e.g. log counts), evaluation metric, time budget,
and whether backtesting is required.

### `pyro.contrib.timeseries`

Best fit for older temporal GP and linear Gaussian state-space abstractions:
`IndependentMaternGP`, `LinearlyCoupledMaternGP`, `DependentMaternGP`,
`GenericLGSSM`, and `GenericLGSSMWithGPNoiseModel`. The base contract expects
real-valued targets shaped `(T, obs_dim)` and forecast deltas `dts` for future
times. Use this when the user asks specifically for contrib time-series GP/LGSSM
objects rather than the higher-level forecast framework.

Safe tiny command concept from source evidence: use a few steps and the built-in
`--test` style flag when adapting the time-series GP example, and disable
plotting unless matplotlib is confirmed:

```text
concept: train a contrib.timeseries GP for a handful of steps on synthetic data;
avoid --plot unless plotting dependencies are installed.
```

### BART forecasting example family

The documented BART ridership example demonstrates multivariate hourly count
forecasting with a weekly seasonal component and `GaussianHMM` noise. It can
fall back to a fake dataset helper, but the full data loader may download a
compressed cache or many raw CSVs and preprocess hundreds of MB to GB. For a
future agent, distill the seasonal/model structure rather than asking it to
retrieve BART data.

Skip or ask when: the user wants exact BART metrics, data downloads, or long
backtests. Ask for approval and storage/time budget first.

## Gaussian Processes

Use `pyro.contrib.gp` for GP regression/classification/GPLVM workflows. Common
objects:

```python
import torch, pyro
import pyro.contrib.gp as gp
from pyro.infer import Trace_ELBO

X = torch.linspace(0, 1, 8).unsqueeze(-1)
y = torch.sin(6 * X.squeeze(-1))
kernel = gp.kernels.RBF(input_dim=1, variance=torch.tensor(1.), lengthscale=torch.tensor(0.3))
model = gp.models.GPRegression(X, y, kernel, noise=torch.tensor(0.05))
pyro.clear_param_store()
gp.util.train(model, num_steps=2, loss_fn=Trace_ELBO().differentiable_loss)
loc, var = model(torch.tensor([[0.25], [0.75]]), full_cov=False)
```

This pattern is CPU-safe with base Pyro. For larger GP work, warn about
Cholesky/O(N^3) cost and the need for `jitter` when kernels are near-singular.

Deep kernel / MNIST GP examples are optional-extra-heavy. They use torchvision,
scikit-learn, and plotting, and should be skipped unless those dependencies and
runtime budget are approved. Use sparse GP classes for larger data before
suggesting a long deep-kernel training run.

## Epidemiology

Use `pyro.contrib.epidemiology` when the user wants stochastic discrete-time,
discrete-count compartmental SIR/SEIR-style models with black-box SVI/HMC,
prediction, and forecasting. The docs explicitly mark this module under
development. The implementation warns that `CompartmentalModel` can be unstable
below `torch.float64`; prefer double precision for serious runs.

Example family capabilities:

- SIR/SEIR generation, MCMC/SVI fitting, future `predict(forecast=...)`;
- regional coupling with `RegionalSIRModel`;
- overdispersion, superspreading, heterogeneous and unknown-start variants;
- optional `--cuda`, `--plot`, `--jit`, SMC particle, quantization, and Haar
  settings in the versioned evidence.

Safe tiny command concept for an adapted run:

```text
concept: generate synthetic SIR observations with duration around 3-7, run either
SVI for 1-2 steps or HMC with 1 warmup/1 sample, no plot, no CUDA, no long JIT.
```

Ask/skip policy:

- Ask for population, duration, reporting/response rate, and observed case time
  series before modeling real data.
- Ask before CUDA or plotting.
- Do not promise scientific-quality epidemiological forecasts from tiny smoke
  settings.

## Tracking / EKF / Data Association

Use `pyro.contrib.tracking` for multi-object tracking and data association, not
for generic time-series forecasting. Key surfaces:

- dynamic models: `Ncp`, `Ncv`, continuous/discrete variants;
- measurements: `PositionMeasurement` and custom differentiable measurements;
- state update: `EKFState(dynamic_model, mean, cov, time=... or frame_num=...)`;
- data association: `compute_marginals*` and marginal assignment distributions;
- approximate set/hashing helpers.

Safe tiny concept:

```python
import torch
from pyro.contrib.tracking.dynamic_models import NcpContinuous
from pyro.contrib.tracking.extended_kalman_filter import EKFState
from pyro.contrib.tracking.measurements import PositionMeasurement

model = NcpContinuous(dimension=2, sv2=0.1)
state = EKFState(model, mean=torch.zeros(2), cov=torch.eye(2), time=torch.tensor(0.0))
measurement = PositionMeasurement(mean=torch.tensor([1.0, -1.0]), cov=torch.eye(2), time=torch.tensor(1.0))
predicted = state.predict(dt=torch.tensor(1.0))
updated_state, (innovation_mean, innovation_cov) = predicted.update(measurement)
```

Check actual constructor signatures in the active installed package if writing
runnable code. Require consistent units, time/frame fields, state dimension, and
positive-definite covariances.

## HMM, Mixed HMM, Capture-Recapture, And RSA

These examples are mainly **enumeration and effect-handler domain evidence**.
Route model mechanics to `../effect-handlers-and-enumeration/` and HMM
distribution shapes to `../distributions-and-shapes/`.

### HMM examples

The core and Funsor HMM examples combine SVI with enumeration over discrete
latent states. Safe tiny command concept:

```text
concept: truncate sequence length to around 10, run one SVI step, small hidden
state dimension, no CUDA, no JIT, no Funsor unless installed.
```

Use ordinary Pyro `TraceEnum_ELBO` and `infer={"enumerate": "parallel"}` when
Funsor is unavailable. Use `pyro.contrib.funsor` only after the `funsor` extra is
installed and verified.

### Capture-recapture

The Cormack-Jolly-Seber examples model ecological capture histories with
continuous survival/recapture probabilities and enumerated discrete alive/dead
states. Source data includes small CSVs, but future runtime guidance should ask
the user to provide capture histories rather than depend on checkout data.

Safe tiny concept:

```text
concept: model 1, a tiny hand-constructed binary capture matrix, num_steps=1-2,
TraceEnum_ELBO, no TMC unless explicitly demonstrating approximate enumeration.
```

### Mixed HMM

The mixed HMM example fits seal movement data with random effects and uses pandas
for CSV preparation. Treat as reference-only unless the user provides a prepared
CSV/schema and approves pandas dependency and training time.

### RSA

RSA examples use custom search/trace-posterior utilities and discrete semantic
models. Treat them as tutorial/domain evidence for enumeration, search, and
marginals. Do not replicate the full tutorial; ask which utterance/meaning space
and inference approximation the user needs.

## scANVI And Single-Cell Workflows

The scANVI example demonstrates semi-supervised deep generative modeling of
transcriptomics data with `SVI` and `TraceEnum_ELBO`. It has a `mock` dataset
path suitable for CI-like smoke tests; the real PBMC path imports scanpy/scvi,
uses single-cell data processing, and optional plotting.

Safe tiny command concept:

```text
concept: dataset=mock, num_epochs=1, small batch_size, no CUDA, no plot.
```

Ask/skip policy:

- Ask for AnnData/scRNA schema, label encoding, gene subset, and train/validation
  split before real analysis.
- Require scanpy/scvi and plotting dependencies for PBMC/UMAP plots.
- Route training instability, ELBO choice, and autoguide questions to
  `../svi-and-autoguides/`; route discrete label enumeration to
  `../effect-handlers-and-enumeration/`.

## VAEs, CVAE, AIR, DMM, And Other Deep Examples

These examples are strong evidence for Pyro modeling patterns but are generally
long-training or optional-extra-heavy:

- VAE / semi-supervised VAE / CVAE examples often require torchvision, pandas,
  plotting, or MNIST data.
- AIR uses image data, visualization tooling, and many training flags.
- DMM uses sequential neural networks and long training defaults.
- `pyro.contrib.cevae` is a packaged contrib implementation for causal effect
  VAE, but still requires a clear tabular schema and training budget.

Safe response pattern:

1. Use distilled model structure and a tiny synthetic tensor shape.
2. Ask before downloading MNIST or real datasets.
3. Ask before GPU training.
4. Make any result a smoke/prototype, not a paper-quality reproduction.

## OED / Bayesian Optimal Experimental Design

Use `pyro.contrib.oed` when the user asks for expected information gain,
adaptive design, A/B test design, or Bayesian experimental design. Require:

- a model whose argument is the design tensor;
- observation site labels;
- target latent site labels;
- candidate design domain and constraints;
- estimator choice and budget.

Tiny concept:

```python
# Given a simple model(design) with sample sites "theta" and "y":
# eig = nmc_eig(model, design_grid, observation_labels=["y"], target_labels=["theta"], N=10, M=2)
```

Full OED examples can be slow because each design may run nested inference or GP
Bayesian optimization. Ask for estimator/budget before launching.

## MuE / Biological Sequence Models

Use `pyro.contrib.mue` only when the user has biological sequence data and wants
MuE/ProfileHMM-style generative sequence modeling. It is under development.
Require alphabet, sequence length assumptions, missing-data policy, train/test
split, and runtime budget. Examples import biosequence dataset loaders and often
plot; treat as optional/reference-only.

## Zuko Flow Workflows

`pyro.contrib.zuko.ZukoToPyro` wraps a Zuko distribution or flow as a Pyro
`TorchDistribution`. It is useful for flow guides and flow priors, but the
actual `zuko` package is user-supplied. Minimal shape concept:

```python
# after user installs zuko and constructs flow = zuko.flows.MAF(features=D)
from pyro.contrib.zuko import ZukoToPyro
flow_dist = ZukoToPyro(flow())
with pyro.plate("data", N):
    z = pyro.sample("z", flow_dist)
```

Check event shape and `.log_prob()` behavior before using it in SVI. Route flow
shape issues to `../distributions-and-shapes/` and SVI guide integration to
`../svi-and-autoguides/`.

## Optional Distributed SVI Families

- **Horovod example:** demonstrates `pyro.optim.HorovodOptimizer` wrapping a
  Pyro optimizer and uses a distributed dataloader/sampler. It has a
  `--no-horovod` fallback concept for ordinary CPU SVI, but the distributed
  branch requires Horovod/MPI runtime and possibly CUDA.
- **Lightning example:** demonstrates the ELBO module pattern with
  `lightning.pytorch.Trainer`, a `LightningModule`, and ordinary `torch.optim`.
  Requires the `lightning` extra and user-selected accelerator/devices.

For both, answer integration questions at the architecture level unless the
active environment proves the dependency. Route ELBO module and PyTorch optimizer
mechanics to `../svi-and-autoguides/`.

## When To Ask Before Proceeding

Ask for data/extras/GPU/time when any of the following is true:

- real dataset download or preprocessing is needed;
- the example imports scanpy, pandas, torchvision, scikit-learn, matplotlib,
  seaborn, Horovod, Lightning, zuko, or Funsor and the environment has not
  verified it;
- the requested training default is hundreds/thousands of epochs/steps or runs
  MCMC with many warmup/samples/chains;
- the user expects scientific metrics rather than a smoke/prototype;
- the workflow writes plots, checkpoints, benchmark files, or distributed logs.
