# Cross-Cutting SpikingJelly Troubleshooting

## Install or import fails

Symptoms:
- `ModuleNotFoundError` for `spikingjelly`, `torch`, or a submodule
- `pip check` reports dependency conflicts
- A local file or directory shadows the package name

Actions:
1. Install PyTorch first, then install `spikingjelly`.
2. Check the import path with `python scripts/spikingjelly_env_report.py --json`.
3. Remove or rename local files that shadow `spikingjelly`, `torch`, or `nir`.
4. Re-run the environment report before debugging deeper package behavior.

## Wrong surface or namespace

Symptoms:
- A task about datasets, conversion, training, backends, or deployment is being handled in the wrong branch
- A user asks about `activation_based`, `datasets`, `triton`, `precision`, `train_classify`, or `nir_exchange` but the answer stays generic

Actions:
- Route to the matching sub-skill instead of widening the current one.
- Keep root-level guidance at the package map and installation layer.

## Optional dependency missing

Symptoms:
- CuPy, Triton, NIR, Lightning, transformers, TorchAO, Transformer Engine, or Megatron imports fail
- Optional examples or backend-specific smoke scripts cannot start

Actions:
- Install only the dependency required by the chosen sub-skill.
- Do not claim verification for optional stacks that are not installed in the current environment.

## Backend or hardware mismatch

Symptoms:
- CUDA, CuPy, or Triton work on one host but not another
- A GPU-only path is requested on a CPU-only machine
- An FP8 or vendor-specific path is missing the necessary hardware support

Actions:
- Treat the failure as an environment mismatch until the required backend is proven.
- Use the selected performance/training sub-skill for the backend-specific smoke and capability checks.

## Import-time config surprises

Symptoms:
- Package behavior changes after editing environment variables
- A logger appears disabled or a config value seems to be ignored

Actions:
- Assume some `SJ_*` and package-level settings are read at import time.
- Restart the interpreter after changing environment values.
- Keep logging, config, and state-reset guidance in `core-snn` if the issue is local to neuron behavior.
