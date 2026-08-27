# Cross-cutting troubleshooting

Read this reference when installation, import, device, environment, logging, or
checkpoint behavior is unclear. Then follow the nearest framework or
integration-specific troubleshooting reference.

## Install/import failures

- `ModuleNotFoundError: No module named 'torch'`, `jax`, or `warp`: install
  only the matching skrl extra and verify the framework independently. For JAX,
  install the intended jaxlib before `skrl[jax]`; for Warp install both
  `warp-lang` and `warp-nn`.
- `No module named gymnasium` or a simulator module: the base package and
  framework extra do not install every optional environment ecosystem. Install
  the environment's documented dependency in the same environment, or narrow
  the task to a supported Gymnasium smoke.
- A package imports from an unexpected checkout/version: run
  `python -c "import skrl; print(skrl.__version__, skrl.__file__)"`, check
  `python -m pip show skrl`, and compare with
  [`repo-provenance.md`](repo-provenance.md). Use a clean isolated environment
  when editable and released installs are mixed.
- Dependency resolution changes the framework build: inspect `pip check` and
  pin compatible framework/backend variants before reinstalling. Do not fix a
  required CUDA path by silently replacing it with CPU packages.

## Device/backend failures

- Invalid Torch device specifications are reported and may fall back to CPU by
  `config.torch.parse_device`; print the resolved value instead of assuming
  the requested device was honored.
- A JAX CUDA warning followed by `CpuDevice` means the installed jaxlib has no
  usable CUDA backend. Install a compatible CUDA jaxlib and validate
  `jax.devices()` before claiming accelerator support.
- Warp device enumeration is not proof of a skrl Warp kernel or simulator
  run. Check the explicit device, driver/toolkit and a bounded framework
  operation; keep CPU and CUDA results separate.
- When Torch and JAX share an NVIDIA process, JAX GPU memory preallocation can
  starve simulator/Torch allocations. For a documented JAX-plus-NVIDIA
  integration, reduce or disable JAX preallocation (for example with
  `XLA_PYTHON_CLIENT_MEM_FRACTION`) after checking the deployment's memory
  budget.

## Wrapper and space failures

- An unknown wrapper tag or class-detection error means the original object
  does not match the selected adapter. Use an explicit tag only when the
  object really comes from that API; do not force an Isaac Lab/PettingZoo tag
  on a Gymnasium object.
- A space conversion error usually indicates an unsupported space, nonstandard
  dtype, or unexpected shape. Inspect observation/action/state spaces before
  defining models and preserve the wrapper's batch/flattening convention.
- A four-result legacy Gym step and a five-result Gymnasium step have different
  termination semantics. Use the matching adapter and preserve terminated vs
  truncated rather than dropping a flag.

## Model/config/runner failures

- `agent.class`, `models`, `memory`, or `trainer` missing in a Runner config is
  a configuration-shape error. Validate the top-level mapping and component
  names before constructing a Runner.
- A PPO/IPPO/MAPPO role error means the model dictionary does not match the
  algorithm contract. Check policy/value roles, per-agent outer keys,
  centralized state requirements, and action distribution.
- JAX models that have no initialized state need `model.init_state_dict(role=...)`
  before model/agent construction. This is not fixed by calling Torch
  `.to(device)`.
- A checkpoint load warning or shape mismatch normally means the recreated
  architecture, role keys, preprocessors, optimizer arrangement, or possible
  agent IDs differ from the saved artifact. Recreate the original structure;
  do not treat a partial policy load as a validated resume.

## Output and run failures

An `auto` experiment interval writes TensorBoard/checkpoint artifacts during a
trainer run. Set `write_interval=0` and `checkpoint_interval=0` for read-only
construction checks. An evaluation workflow can still need an environment and
model architecture even when writes are disabled. Verify output directories,
checkpoint paths and permissions explicitly; never delete an existing runs
folder as a diagnostic shortcut.
