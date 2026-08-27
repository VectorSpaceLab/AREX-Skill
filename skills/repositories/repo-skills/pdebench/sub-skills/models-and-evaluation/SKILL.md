---
name: models-and-evaluation
description: "Route PDEBench forward and inverse model configuration, safe model
  checks, metrics, checkpoints, and result analysis without reopening the source
  checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Models and evaluation

Use this sub-skill when a Researcher must choose, configure, inspect, or
adapt PDEBench baseline models and their evaluation outputs. It covers the
FNO, U-Net, PINN, and gradient/ProbRasterLatent/InitialConditionInterp inverse
paths. It does **not** download data, generate PDE data, visualize datasets,
or run a benchmark by default.

## Route by question

- Choose a forward model or check tensor/layout contracts:
  [model-overview.md](references/model-overview.md).
- Construct a Hydra override, select train/eval/checkpoint mode, or make a
  CPU/GPU decision: [configuration.md](references/configuration.md).
- Compute metrics, understand pickle/CSV artifacts, or compare plots:
  [metrics-and-results.md](references/metrics-and-results.md).
- Diagnose imports, backend selection, paths, shapes, checkpoints, memory, or
  result failures: [troubleshooting.md](references/troubleshooting.md).
- Run only the deterministic, no-epoch smoke check:
  [scripts/model_smoke.py](scripts/model_smoke.py).

## Operating rules

1. Establish the dataset filename, dimensionality, variable/channel count,
   initial context length, desired forward or inverse objective, and the
   intended output/checkpoint location before changing a config.
2. Keep PDEBench's data convention visible: arrays are generally
   `[batch, x1, ..., xd, time, variables]` at dataset boundaries, while FNO
   consumes a flattened time-variable context plus a coordinate grid and
   U-Net consumes channel-first tensors. Do not silently transpose data.
3. Use `if_training: false` for evaluation only when the matching checkpoint is
   already present. Use `continue_training: true` only with the matching
   optimizer-bearing checkpoint. A smoke check is not model training.
4. Treat full training, MCMC, PINN optimization, checkpoint recovery, and
   benchmark comparisons as user-authorized, data-dependent, potentially
   long-running operations. Do not fetch pretrained weights or datasets by
   default.
5. For PINN, select and verify the DeepXDE PyTorch backend before importing
   `pdebench.models.pinn.train`; for inverse MCMC, separately verify Pyro.
6. When a source implementation caveat is encountered, preserve the caveat in
   the run notes rather than silently “fixing” the model contract. Use the
   troubleshooting reference to decide whether a local, user-approved patch
   is needed.

## Evidence boundary

This graph distills the published README's “Baseline Models”, “Short
explanations on the config args”, and model configuration documentation,
plus observed contracts in the installed module family
`pdebench.models.train_models_forward`, `pdebench.models.train_models_inverse`,
the `fno`, `unet`, `pinn`, and `inverse` modules, `metrics`, the result-analysis
programs, and the published shell workflow examples. Those source artifacts
are provenance only; they are not bundled runtime files. Dataset downloading,
data generation, visualization, and vorticity are intentionally routed to
other sub-skills.

## Safe verification

Set `SKILL_ROOT` to the directory containing this sub-skill's `SKILL.md`, then
run the bundled smoke with the installed `pdebench` package:

```bash
python "$SKILL_ROOT/scripts/model_smoke.py" --help
python "$SKILL_ROOT/scripts/model_smoke.py"
```

The script constructs tiny FNO/U-Net modules on CPU and checks metric output;
it never opens a dataset, loads a checkpoint, starts an epoch, calls DeepXDE, or
invokes Pyro. Do not use a source checkout path as an import workaround. For
any real run, first apply the configuration and failure-recovery guidance in
the linked references.
