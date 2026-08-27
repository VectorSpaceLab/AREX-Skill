# Optional Integrations And Extras

The minimum verified Pyro runtime covers CPU core package use. Many contrib and
domain examples rely on optional packages or backends. Use this reference to
state what is optional, how a user would enable it, and when to skip instead of
overclaiming support.

## Minimum vs Optional

Base `pyro-ppl` dependencies include PyTorch, numpy, opt-einsum, pyro-api, and
tqdm. The package defines optional extras for examples/tutorials, verification
support, development, profiling, Horovod, Lightning, and Funsor. Optional imports
may be absent in a deliberately minimal runtime; verify Funsor, Graphviz,
Horovod, Lightning, torchvision, pandas, and scanpy in the active environment
before using them.

Treat the following as **optional/unverified until the active environment proves
otherwise**:

- CUDA/GPU execution;
- Funsor backend;
- Graphviz rendering;
- Horovod distributed training;
- Lightning integration;
- torchvision/MNIST/image examples;
- pandas/seaborn/matplotlib/scikit-learn plotting and tabular/tutorial helpers;
- scanpy/scvi single-cell data workflow;
- zuko flows;
- network download helpers and `wget`.

## Quick Optional Import Probe

Use the root Pyro skill's environment check when available. For a manual probe in
an active project environment:

```python
import importlib.util
for name in ["pyro", "torch", "funsor", "graphviz", "horovod", "lightning", "torchvision", "pandas", "scanpy", "sklearn", "zuko", "wget"]:
    print(name, bool(importlib.util.find_spec(name)))
```

Do not interpret a missing optional package as a Pyro failure. Route the answer
to install/skip/fallback.

## Install Extras Map

| Capability | Install concept | Verify concept | Skip/fallback |
|---|---|---|---|
| Common examples/tutorial extras | `pip install "pyro-ppl[extras]"` or install only needed packages | import matplotlib/torchvision/pandas/sklearn/wget as needed | Use synthetic tensors and no plots/downloads. |
| Funsor backend | `pip install "pyro-ppl[funsor]"` (Pyro pins `funsor[torch]==0.4.8`) | `import funsor; import pyro.contrib.funsor; from pyroapi import pyro_backend; pyro_backend("contrib.funsor")` | Use ordinary Pyro `TraceEnum_ELBO` / `infer_discrete` when possible. |
| Horovod distributed SVI | `pip install "pyro-ppl[horovod]"` plus MPI/build requirements | `import horovod.torch as hvd; hvd.init()` in the distributed launcher | Run the same SVI model with `--no-horovod`/ordinary optimizer on CPU. |
| Lightning integration | `pip install "pyro-ppl[lightning]"` | `import lightning.pytorch as pl` and run a tiny CPU Trainer | Use the ELBO module + `torch.optim` pattern without Lightning. |
| Graphviz model rendering | `pip install graphviz` Python package and install Graphviz system executable if rendering files | `import graphviz`; call `pyro.render_model(...)` on a tiny model | Use `poutine.trace(...).format_shapes()` or textual trace inspection. |
| torchvision image examples | install torchvision version compatible with active torch | `import torchvision`; load a tiny dataset only with user approval | Use synthetic image tensors. |
| pandas/scikit-learn/seaborn/matplotlib tutorials | install only requested packages | import the exact package and run a no-display plot or data transform | Provide model code without plotting/dataframe preprocessing. |
| scanpy/scvi scANVI real data | install scanpy and scvi stack, including compiled/HDF5 deps | import scanpy/scvi and load user-provided or approved data | Use scANVI mock dataset or synthetic tensors. |
| zuko flows | `pip install zuko` separately; not a Pyro setup extra in this version | `import zuko; from pyro.contrib.zuko import ZukoToPyro` | Use Pyro-native transforms/flows or a simple Normal guide. |
| `wget` / network helpers | install `wget` Python package only if needed | import `wget`; verify URL/storage approvals | Ask user to provide local data or skip download-heavy example. |

Prefer targeted installs over `pyro-ppl[extras]` when the user only needs one
capability. Ask before broad installs in a managed or shared environment.

## Funsor Backend

`pyro.contrib.funsor` registers a `pyroapi` backend named `contrib.funsor` and
exports Funsor-aware primitives/handlers such as `plate`, `markov`,
`vectorized_markov`, `condition`, `do`, `to_data`, and `to_funsor`. It is used
by Funsor HMM and enumeration examples.

Safe usage skeleton after installation:

```python
import pyro.contrib.funsor  # registers backend
from pyroapi import pyro_backend

with pyro_backend("contrib.funsor"):
    # use pyroapi.pyro / pyroapi.infer / pyroapi.handlers surfaces
    ...
```

Fallback when missing:

- If the task is ordinary discrete enumeration, use core Pyro
  `TraceEnum_ELBO`, `config_enumerate`, and `infer_discrete` instead.
- If the task specifically requires named Funsor dimensions or Funsor TMC, ask
  the user to install the Funsor extra and rerun a smoke check.

## Horovod Distributed SVI

The Horovod integration uses `pyro.optim.HorovodOptimizer` to wrap a Pyro
optimizer. The distilled pattern keeps most model code ordinary and gates
distributed-specific code behind a Horovod flag:

- initialize Horovod inside the launched process;
- broadcast initialized model/guide parameters;
- use a distributed sampler for dataloaders;
- optionally set CUDA device per local rank;
- wrap `pyro.optim.Adam(...)` with `HorovodOptimizer(...)`.

Skip policy:

- Skip the distributed branch unless `horovod.torch` imports and the user has a
  launcher/runtime plan (`horovodrun`, MPI, number of workers, devices).
- A CPU non-Horovod run can still validate the model and SVI logic, but it does
  not verify gradient synchronization or distributed sampling.

## Lightning Integration

The Lightning example uses the ELBO-module pattern, not high-level `SVI.step()`:

```python
loss_fn = Trace_ELBO()(model, guide)  # returns a torch.nn.Module-like loss
# LightningModule.training_step calls loss_fn(*batch)
# configure_optimizers returns torch.optim.Adam(loss_fn.parameters(), lr=...)
```

Use this when the user wants Lightning's trainer, accelerator, logging, or
checkpointing. If Lightning is absent, route to the SVI sub-skill's PyTorch
optimizer pattern; it uses the same ELBO module idea without requiring
Lightning.

## Graphviz And Rendering

`pyro.render_model` is imported at top level from `pyro.infer.inspect`. Rendering
needs the Python `graphviz` package, and actual file rendering may also need the
Graphviz system binaries. Pyro raises an import error that says to install
`graphviz` when rendering is requested without the Python package.

Fallbacks:

- For model debugging, use `poutine.trace(model).get_trace(...).format_shapes()`.
- For dependency-free structure checks, inspect trace nodes and edges in text.
- Do not install Graphviz just to debug a shape error; textual trace output is
  usually enough.

## Plotting, Data, And Tutorial Extras

Many examples import plotting/data packages only when plotting or data loading is
requested, but some import them at module top level. Examples include:

- the scANVI example family imports matplotlib eagerly and imports scanpy/scvi
  for the real PBMC dataset path;
- VAE/CVAE/AIR tutorials can import torchvision, pandas, PIL, matplotlib, or
  seaborn;
- GP tutorials can import matplotlib, seaborn, and scikit-learn;
- mixed HMM and some tutorial helpers use pandas;
- sparse gamma and other examples may use network/download helpers such as
  `wget`.

Skip policy:

1. If the task is conceptual or debugging model code, replace real data with
   synthetic tensors and omit plotting.
2. If the task needs exact tutorial output, ask for permission to install extras,
   download data, and run long training.
3. If the user supplies local data, validate schema/shape before installing
   plotting packages.

## CUDA/GPU Flags

Pyro examples often expose `--cuda` or Lightning accelerator flags. CUDA is not
required for core correctness in the minimum scope.

Before promising GPU execution:

```python
import torch
print(torch.cuda.is_available(), torch.version.cuda)
```

Then ensure all tensors created inside models use the correct device:

```python
options = {"device": data.device, "dtype": data.dtype}
zero = torch.tensor(0.0, **options)
eye = torch.eye(dim, **options)
```

A CPU tiny run validates model shape and inference logic, but it is only partial
evidence for a CUDA workflow. Ask before using GPUs for long examples.

## Network Download Helpers

`pyro.contrib.examples` includes dataset helpers. Some can download caches or raw
data, then preprocess and store files. For example, full BART ridership loading
can require large downloads and preprocessing, while fake data helpers are safer
for smoke tests.

Rules:

- Never start a download-heavy example without user approval for network, time,
  and storage.
- Prefer user-provided local data or synthetic data.
- Make downloaded-data cache locations a user/project decision; do not hard-code
  private checkout paths in runtime guidance.

## Decision Table

| Situation | Response |
|---|---|
| Optional import missing but task has a core fallback | Explain missing optional dependency and use fallback. |
| Optional import missing and task specifically requires it | Ask to install the narrow extra or provide an environment with it. |
| User asks for exact example metrics | Ask for data/extras/time approval; state long-run nature. |
| User asks for model sketch/prototype | Use synthetic/mock data and no optional extras. |
| User asks for GPU/distributed run | Probe environment, ask for device/worker budget, then treat CPU-only as partial. |
| User asks to debug `pyro.render_model` | Install/probe Graphviz only if rendering is essential; otherwise use trace text. |
