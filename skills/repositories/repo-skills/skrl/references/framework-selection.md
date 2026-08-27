# Framework selection and installation

Read this reference before installing skrl or choosing a framework-specific
sub-skill. It separates package extras, environment interfaces, and accelerator
claims.

## Package baseline

The public package requires Python 3.10 or newer and declares these common
dependencies: Gymnasium, packaging, TensorBoard, and tqdm. Framework extras are
independent:

| Need | Install | Public surface |
| --- | --- | --- |
| PyTorch | `python -m pip install "skrl[torch]"` | `skrl.agents.torch`, `models.torch`, `memories.torch`, `trainers.torch`, resources and wrappers |
| JAX | install the desired JAX/jaxlib build first; then `python -m pip install "skrl[jax]"` | `skrl.agents.jax`, Flax models, JAX memories/trainers/resources and wrappers |
| NVIDIA Warp | `python -m pip install "skrl[warp]"` | `skrl.agents.warp`, warp-nn models, Warp memories/trainers/resources and wrappers |
| All families | `python -m pip install "skrl[all]"` | Use only when a single environment truly needs all three |

The repository documentation specifically recommends installing JAX manually
before the skrl JAX extra so that the intended CPU or CUDA jaxlib is selected.
Do not install a CPU jaxlib and then call the result CUDA-ready.

## Choose the family

- Choose **Torch** when models use `torch.nn`, `torch.Tensor`, Torch
  optimizers, CUDA `torch.device`, or Torch distributed variables.
- Choose **JAX** when models use Flax modules, JAX arrays/PRNG keys, Optax, or
  JAX distributed launch. JAX model state initialization is explicit; see the
  JAX route.
- Choose **Warp** when the model uses `warp`/`warp-nn` operations or the task
  specifically names Warp DDPG, PPO, or SAC. Warp exposes a CPU device and can
  also expose CUDA devices, but a CPU probe is not a CUDA training check.

The framework-specific environment wrapper must match the family. Do not pass
Torch tensors to a JAX wrapper or use a Torch agent on a JAX wrapper merely
because both accept Gymnasium environments.

## Devices and verification

Start with an explicit CPU device for package/API diagnosis:

```python
from skrl import config
config.torch.device = "cpu"  # or config.jax.device/config.warp.device
```

Torch `config.torch.parse_device` validates an explicit device and falls back
to the available default when the specification is invalid. JAX resolves
through `jax.devices`; a CUDA request requires a CUDA-enabled jaxlib. Warp
resolves through its own device registry and may enumerate CPU and CUDA
entries. Always print the resolved device and perform a tiny operation before
starting a real run.

For CUDA, verify the framework-specific package and a tiny allocation on the
selected device. A visible NVIDIA GPU, a Warp CUDA listing, or a successful
package import alone is insufficient for a Torch/JAX/agent/simulator claim.
Use the host's compatible driver/toolkit and the framework's official wheel
selection. Do not mix incompatible CPU/GPU framework variants in one
inspection/runtime environment.

## Environment boundary

Install external integrations separately and validate them before wrapping:
Isaac Lab, ManiSkill, MuJoCo Playground, Gym legacy, Shimmy, PettingZoo, ROS,
robot middleware, and assets are not pulled by the core framework extras. Route
the resulting environment through
[`environment-integration`](../sub-skills/environment-integration/SKILL.md).
