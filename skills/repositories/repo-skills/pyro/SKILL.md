---
name: pyro
description: "Use Pyro probabilistic programming APIs for models, distributions,
  SVI, MCMC, poutine, enumeration, and contrib workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pyro Repo Skill

Use this repo skill when the task involves the `pyro-ppl` package imported as
`pyro`: probabilistic models, distributions, stochastic variational inference,
HMC/NUTS/MCMC, posterior prediction, poutine effect handlers, discrete
enumeration, reparameterizers, `PyroModule`, or Pyro contributed modules.

This skill targets the Pyro 1.9.1 API family. It is self-contained for package
use; do not depend on a source checkout, original examples, original tests, or
notebooks at runtime.

## Install and Import Check

Pyro's distribution name is `pyro-ppl` and the import name is `pyro`:

```bash
python -m pip install pyro-ppl
python - <<'PY'
import pyro, torch
print(pyro.__version__)
print(torch.__version__, torch.cuda.is_available())
PY
```

For a safe diagnostic that also reports optional integrations, run
[scripts/check_pyro_environment.py](scripts/check_pyro_environment.py). Start
with `python scripts/check_pyro_environment.py --help`; use `--smoke` to run a
tiny CPU SVI check.

## Route by Task

- Basic stochastic functions, `pyro.sample`, `pyro.param`, observed sites,
  `pyro.plate`, parameter-store state, validation, RNG seeds, `PyroModule`,
  `PyroParam`, and `PyroSample`: read
  [sub-skills/modeling-basics/SKILL.md](sub-skills/modeling-basics/SKILL.md).
- Distribution selection, constraints/transforms, `.to_event()`, `Independent`,
  HMM/zero-inflated/stable/matching distributions, and event/batch/plate shape
  debugging: read
  [sub-skills/distributions-and-shapes/SKILL.md](sub-skills/distributions-and-shapes/SKILL.md).
- SVI training loops, ELBO choice, autoguides, Pyro optimizers, vanilla PyTorch
  optimizer loops, minibatching, JIT/vectorized particles, and SVI
  troubleshooting: read
  [sub-skills/svi-and-autoguides/SKILL.md](sub-skills/svi-and-autoguides/SKILL.md).
- HMC/NUTS/MCMC runs, initialization, warmup/sample/chain choices, diagnostics,
  `Predictive`, `WeighedPredictive`, and posterior/prior predictive shapes:
  read
  [sub-skills/mcmc-and-prediction/SKILL.md](sub-skills/mcmc-and-prediction/SKILL.md).
- Poutine handlers, trace/condition/replay/block/scale/mask/seed/substitute,
  discrete enumeration, `TraceEnum_ELBO`, `infer_discrete`, `config_enumerate`,
  reparameterizers, and inference-tied `pyro.ops`: read
  [sub-skills/effect-handlers-and-enumeration/SKILL.md](sub-skills/effect-handlers-and-enumeration/SKILL.md).
- `pyro.contrib`, MiniPyro/generic backend, forecasting, GP, epidemiology,
  tracking, easyguide, CEVAE, Funsor, Horovod, Lightning, domain examples, and
  optional dependency policy: read
  [sub-skills/contrib-and-domain-workflows/SKILL.md](sub-skills/contrib-and-domain-workflows/SKILL.md).

For a compact root API map and verified signature highlights, read
[references/api-cheatsheet.md](references/api-cheatsheet.md). For install/import,
backend, optional dependency, validation, and routing failures, read
[references/troubleshooting.md](references/troubleshooting.md). For staleness
checks against a repository checkout, read
[references/repo-provenance.md](references/repo-provenance.md).

## Fast Decision Rules

1. If the user has an error, ask first for the Pyro version, PyTorch version,
   CPU/CUDA backend, and a minimal model/guide snippet unless already present.
2. Turn on validation while debugging: `pyro.enable_validation(True)`.
3. Clear parameter state between independent experiments:
   `pyro.clear_param_store()`.
4. For any shape or plate problem, trace the model and inspect
   `trace.format_shapes()` before changing model structure.
5. Do not use HMC/NUTS directly on discrete latent variables. Enumerate,
   marginalize, or use another inference strategy.
6. Treat CUDA, Funsor, Horovod, Lightning, Graphviz, torchvision, pandas,
   scanpy, and long example/tutorial dependencies as optional until the user's
   active environment proves support.
7. Prefer tiny synthetic tensors and this skill's bundled smoke scripts before
   attempting long training, downloads, plotting, or GPU-specific runs.

## What Not to Use This Skill For

- Generic PyTorch training that does not use Pyro primitives or distributions.
- PyMC, NumPyro, Bean Machine, Stan, or TensorFlow Probability code unless the
  task is explicitly translating concepts to Pyro.
- Full scientific reproduction of every Pyro tutorial/example; use this skill
  to implement or debug the package workflow, then request task-specific data,
  runtime, and budget.
- Maintainer release, benchmark, profiling, Docker, or documentation-build work
  unless the user explicitly asks to edit the Pyro repository.
