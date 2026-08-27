---
name: export
description: "Route AgiBot X1 DH checkpoint-to-JIT export, JIT-to-ONNX
  conversion, artifact preflight, validation, and backend-aware failure
  recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# X1 DH policy export

Use this sub-skill only for the registered `x1_dh_stand` model conversion
pipeline and its serialized artifacts. Keep the two stages distinct:

1. **Checkpoint → JIT:** `model_<iteration>.pt` → `policy_dh.jit`.
2. **JIT → ONNX:** `policy_dh.jit` → `x1_policy.onnx`.

The ONNX stage never reopens a training checkpoint, and its `--checkpoint`
argument does not select one.

## Route by intent

| Intent | Route |
| --- | --- |
| Select a runner checkpoint and convert it to JIT | Stay here; use [export workflows](references/workflows.md#3-checkpoint--jit) |
| Convert an existing JIT policy to ONNX | Stay here; use [export workflows](references/workflows.md#4-jit--onnx) |
| Check paths, checkpoint structure, or a serialized artifact | Stay here; use [preflight_export.py](scripts/preflight_export.py) and the [artifact contract](references/artifact-contract.md) |
| Produce or resume a training checkpoint | Use [training](../training/SKILL.md) |
| Run a runner checkpoint interactively in Isaac Gym | Use [playback](../playback/SKILL.md) |
| Run an exported policy in MuJoCo | Use [sim2sim](../sim2sim/SKILL.md) after JIT validation |

Do not use this route to train, launch Isaac Gym playback, run MuJoCo, or claim
robot/simulation safety.

## Required backend boundary

Both repository export entry points import `humanoid.envs`; their parser/helper
import chain also requires **Isaac Gym Preview 4**. That backend is unavailable
in the verified construction environment. Therefore full source checkpoint →
JIT and JIT → ONNX execution remains:

**BLOCKED_REQUIRED_BACKEND: Isaac Gym Preview 4 unavailable**

Do not stub Isaac Gym, bypass task registration, or promote a bundled-helper
pass to full source-export verification. A compatible source environment must
provide the repository's documented Python 3.8, PyTorch 1.13.1/CUDA 11.7,
NumPy 1.23.x, editable project install, and verified Isaac Gym Preview 4.
ONNX conversion additionally needs a compatible `onnx` installation.

The bundled preflight deliberately avoids project and Isaac Gym imports. It can
perform path checks everywhere and can inspect trusted local artifacts only
when the corresponding already-installed model library is available.

## Safe operating sequence

1. Obtain an exact run/checkpoint handoff from [training](../training/SKILL.md#checkpoints-and-handoff).
   Prefer explicit run names and checkpoint numbers; do not let “latest” select
   an unrelated artifact.
2. From this sub-skill directory, inspect the helper interface:

   ```bash
   python scripts/preflight_export.py --help
   ```

3. Follow [export workflows](references/workflows.md) for stage-specific
   preflight, source commands, destination paths, and validation. Deserialize
   only trusted checkpoints; `torch.load` may execute pickle payloads.
4. Enforce the fixed X1 contract in [artifact contract](references/artifact-contract.md):
   input `(1, 3102)`, deterministic output `(1, 12)`, and exact artifact type
   for the requested stage.
5. Preserve the source script's printed input/output paths, explicit task, run,
   checkpoint or JIT timestamp, and package/backend versions in the handoff.
6. On failure, use [export troubleshooting](references/troubleshooting.md) and
   keep backend, missing-input, and failed-artifact states distinct.

## Non-negotiable artifact rules

- `x1_dh_stand` is the only verified task contract in this sub-skill.
- Checkpoint → JIT reconstructs `ActorCriticDH`, strictly loads
  `model_state_dict`, and scripts a CPU wrapper containing the actor, state
  estimator, and long-history encoder.
- JIT → ONNX loads a prior `policy_dh.jit`; select its timestamp with
  `--load_run`. The shared `--checkpoint` flag is ignored by that converter.
- Source outputs use `logs/`, not the README's stale singular `log/` spelling.
  JIT and ONNX go to different trees; see [artifact contract](references/artifact-contract.md).
- A CPU load/shape check validates serialization only. It does not verify
  training-time observation construction, Isaac Gym behavior, MuJoCo behavior,
  controller integration, or robot safety.
