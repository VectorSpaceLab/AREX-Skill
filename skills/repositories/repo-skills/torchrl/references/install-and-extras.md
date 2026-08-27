# TorchRL Install and Extras

## When to read

Read this before installing TorchRL, choosing optional dependency extras, debugging imports, or deciding whether a task needs GPU/simulator/LLM/VLA dependencies.

## Verified base package facts

- Distribution name: `torchrl`.
- Import name: `torchrl`.
- Python requirement in package metadata: `>=3.10`.
- Core dependencies include `torch`, `tensordict`, `pyvers`, `hoptorch`, `numpy`, `packaging`, and `cloudpickle`.
- Console entry points: `rlrender` and `torchrl-render`, both backed by `torchrl.render.cli:main`.
- The source build can compile a TorchRL C++ extension. CUDA extension sources are used only when CUDA build prerequisites match the installed PyTorch CUDA runtime and `nvcc`; otherwise the CPU C++ extension path is used.

## Base install patterns

For ordinary package use:

```bash
python -m pip install torchrl
python - <<'PY'
import torch, tensordict, torchrl
print(torch.__version__)
print(tensordict.__version__)
print(torchrl.__version__)
PY
```

For a source checkout after the desired PyTorch build is already installed:

```bash
python -m pip install -e .
```

When using `uv` and you intentionally installed a specific PyTorch build beforehand, install local TorchRL with no dependency resolution so the framework wheel is not replaced:

```bash
uv pip install --no-deps -e .
```

## Narrow optional extras

Install only the extras needed by the selected workflow.

| Extra | Typical reason to install | Notes |
| --- | --- | --- |
| `atari` | Gymnasium Atari environments | May download/expect ALE assets depending on task. |
| `dm_control` | DeepMind Control Suite wrappers | Requires native simulator stack. |
| `gym_continuous` | Gymnasium continuous-control examples | Pulls MuJoCo-related dependencies. |
| `rendering`, `video` | `rlrender`, video/image outputs, codec workflows | Display, codec, and notebook dependencies can be platform-specific. |
| `replay_buffer` | CUDA-capable replay-buffer kernels or newer replay-buffer acceleration | Needs compatible PyTorch/backend; do not treat CPU replay as CUDA verification. |
| `offline-data` | Dataset/hub/offline RL loaders | Can involve network, datasets, pandas/HDF5/image stack. |
| `marl` | Multi-agent simulator integrations such as VMAS/PettingZoo/MeltingPot | Simulator packages are optional and version-sensitive. |
| `open_spiel`, `brax`, `mujoco_playground`, `mjlab`, `genesis` | Specific env wrapper families | Install only when the task names that backend. |
| `pilco` | PILCO/Botorch/GPyTorch workflows | Scientific/optimization stack; not needed for generic losses. |
| `llm` | Lightweight LLM data/wrapper components | Model/tokenizer downloads remain separate runtime concerns. |
| `llm-vllm`, `llm-sglang`, `llm-all` | LLM serving backends | Usually Linux + GPU + backend-specific model-serving constraints. |
| `grpo` | GRPO/RLHF recipes | Adds serving, PEFT, Ray, W&B, and acceleration packages; training-scale. |
| `vla` | LeRobot/vision-language-action workflows | Python-version and dataset/backend constraints may apply. |
| `checkpointing` | TorchSnapshot checkpoint support | Optional unless checkpoint conversion/restoration requires it. |
| `tests`, `utils`, `dev` | Maintainer testing/tooling | Avoid for runtime usage unless you are preparing a source contribution. |

## Entry-point probe

Use safe help checks before invoking rendering outputs:

```bash
rlrender --help
torchrl-render --help
```

`rlrender` accepts config/checkpoint/policy/env factories, output formats such as `ipynb`, `mp4`, `gif`, `frames`, `npz`, and `jsonl`, render backend selection, `--validate-only`, `--dry-run`, and key overrides. Rendering itself may require optional codecs, simulator display support, or factory importability.

## Install decision rules

1. Start with the smallest base environment that imports `torch`, `tensordict`, and `torchrl`.
2. Add an optional extra only when the requested API, example, dataset, simulator, service, or backend imports it.
3. Verify the framework backend separately. A CPU PyTorch wheel proves CPU workflows, not CUDA/ROCm/MPS kernels.
4. For source builds, install PyTorch first, then build TorchRL against that framework. If CUDA extension compilation is required, verify `nvcc`, compiler, driver, and PyTorch CUDA tag first.
5. If an optional backend fails, route to the owning sub-skill and record the missing dependency or hardware instead of broad-installing every extra.
