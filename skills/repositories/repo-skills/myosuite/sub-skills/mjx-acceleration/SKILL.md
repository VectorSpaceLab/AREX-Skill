---
name: "mjx-acceleration"
description: "Route optional MyoSuite JAX/MJX acceleration work: probe
  dependencies and devices, construct MJX environments, use JAX quaternion,
  fatigue, and reference-motion helpers, and keep CPU substitution and CUDA
  claims explicit."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MJX acceleration

Use this sub-skill only when the user explicitly asks for the optional JAX/MJX
or MJWarp route, JAX math parity, JAX fatigue/reference-motion helpers, or
backend/device diagnostics. For ordinary MyoSuite environments and MuJoCo
CPU workflows, route to the environments sub-skill instead. For policy
training recipes, route to training-integration.

## Non-negotiable boundary

- Base MyoSuite is a CPU-capable MuJoCo/Gymnasium package.
- MJX is optional; it is not proof that a CPU-only installation can provide
  acceleration.
- CUDA is a separate optional route. Never report a CUDA speedup without a
  CUDA-backed JAX device probe and a workload measurement.
- A CPU JAX probe can validate imports, shapes, transforms, and semantics, but
  it cannot validate CUDA kernels, GPU throughput, or a speedup claim.
- Do not install packages, initialize assets, download data, or run training
  from the bundled probe. Installation is an explicit user decision.

Read [compatibility.md](references/compatibility.md) before choosing an
installation or device route. Read [api-reference.md](references/api-reference.md)
for signatures and data contracts. Read [troubleshooting.md](references/troubleshooting.md)
when a probe, parity check, or environment construction fails.

## Route selection

1. Run the safe, import-only probe from this directory:

   ```bash
   python scripts/mjx_probe.py
   ```

2. If JAX/MJX is absent, choose one of these honest outcomes:
   - stay on the base CPU route and state that MJX is optional and unverified;
   - ask permission to install the `mjx` extra, then rerun the probe;
   - ask for a CUDA-capable environment and permission to install
     `mjx-cuda` when GPU acceleration is required.

3. If MJX is present, probe an environment without training:

   ```bash
   python scripts/mjx_probe.py --env-name MjxElbowPoseRandom-v0 --steps 1
   ```

4. For a CUDA claim, require both the optional dependencies and a device whose
   JAX platform is GPU/CUDA. Use `--require-cuda`; a CPU result is a backend
   block, not a substitute:

   ```bash
   python scripts/mjx_probe.py --require-cuda --env-name MjxElbowPoseRandom-v0
   ```

The probe returns JSON only with `--json`, exits nonzero for a requested
required backend that is unavailable, and otherwise leaves optional absence
as a clearly labelled result.

## Minimal MJX environment contract

The public constructor is `myosuite.envs.myo.mjx.make(name,
config_overrides=None)`. A normal JAX lifecycle is:

```python
import jax
import jax.numpy as jnp
from myosuite.envs.myo import mjx

env = mjx.make("MjxElbowPoseRandom-v0", config_overrides={"num_envs": 1})
state = env.reset(jax.random.PRNGKey(0))
next_state = env.step(state, jnp.zeros((env.action_size,), dtype=jnp.float32))
```

`reset` consumes a JAX PRNG key and returns a MuJoCo Playground-style `State`.
`step` returns a new state rather than mutating the old state. The state carries
MJX data, a dictionary observation, scalar reward/done values, metrics, and
information such as the RNG, target, and step count. Confirm action size and
observation keys from the concrete environment; do not assume Gymnasium's
five-value `step` contract here.

Supported factory names in the inspected implementation are
`MjxElbowPoseFixed-v0`, `MjxElbowPoseRandom-v0`, `MjxFingerPoseFixed-v0`,
`MjxFingerPoseRandom-v0`, `MjxHandReachFixed-v0`, and
`MjxHandReachRandom-v0`. Registering a base environment also exposes fatigue
variants with the `MjxFati` prefix. Registration is lazy through `make`; call
`make` before relying on a name being present in the local registry.

## JAX helper routes

- Quaternion/math parity: compare the NumPy helpers in
  `myosuite.utils.quat_math` with the JAX helpers in
  `myosuite.utils.quat_math_jax`. Check shape, finite values, rotation-matrix
  equivalence, and dtype before comparing numerical values.
- Fatigue: use `CumulativeFatigue.reset(key, ...)` to obtain a state dict with
  `MA`, `MR`, and `MF`, then pass that state to `compute_act(target_load,
  state)`. `get_effort` returns the norm of active-minus-target activation.
- Fatigue wrapper: configure `fatigue_config` with `fatigue_reset_vec`,
  `fatigue_reset_random`, and allowed observation keys `MA`, `MR`, `MF`.
  The wrapper stores fatigue state in MJX `userdata` and applies fatigue to
  muscle activations before stepping.
- Reference motion: use `ReferenceMotion` with a dict or a supported `.npz`/
  pickle input. It classifies one-frame, two-bound, and multi-frame data as
  fixed, random, and track references, respectively; `get_reference(time)`
  returns a `ReferenceStruct`.

## CPU substitution and evidence

CPU substitution is full for base MuJoCo environments and only partial for
this sub-skill. It can validate helper semantics and a CPU JAX execution, but
not GPU placement or acceleration. Preserve an explicit `optional-unverified`
status when the extra is not installed. Treat benchmark figures as context
only: throughput depends on model contacts, batch size, JAX implementation,
hardware, and compilation/warm-up costs.

## Handoff checklist

Before claiming success, record:

- package and optional-extra availability;
- `jax.devices()` and the selected platform;
- model/environment name, implementation, action shape, and one-step result;
- parity tolerance, dtype, and quaternion sign handling;
- whether fatigue/reference-motion helpers were actually exercised;
- whether the result is CPU semantic validation, CUDA execution, or an
  unverified optional route.

The bundled script is deliberately a probe, not a benchmark or installer. Keep
long API notes, compatibility rules, and recovery steps in the linked
references.
