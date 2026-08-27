---
name: protomotions
description: "Use this skill for ProtoMotions 3 humanoid simulation,
  motion-learning, retargeting, simulator-backend, training, inference, and
  deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ProtoMotions

Use this repo skill when a task involves **ProtoMotions 3** (`protomotions`), a Python framework for GPU-accelerated humanoid and character simulation, motion imitation, retargeting, reinforcement-learning experiments, and G1 deployment workflows.

## Fast routing

- **Install/import/backend issue**: read `sub-skills/installation-and-backends/SKILL.md`, then `references/troubleshooting.md` if assets or simulator imports fail.
- **Simulator, robot, terrain, scene, or tutorial-style construction**: read `sub-skills/simulator-foundations/SKILL.md`.
- **Training, inference, experiment configs, checkpoints, domain randomization, SLURM, or GPC/PEFT**: read `sub-skills/training-and-experiments/SKILL.md`.
- **MotionLib, AMASS/PHUMA/SEED/Kimodo data conversion, PyRoki retargeting, contacts, FPS, or motion filters**: read `sub-skills/retargeting-and-motion-data/SKILL.md`.
- **ONNX export, standalone MuJoCo deployment, G1 real-robot integration, custom robots, MJCF/USD, or tracker input semantics**: read `sub-skills/deployment-and-robots/SKILL.md`.

## What to know before acting

1. ProtoMotions intentionally uses **separate environments per simulator backend**. Do not install all extras into one environment.
2. IsaacGym and IsaacLab must be imported **before** importing `torch`; use `protomotions.utils.simulator_imports.import_simulator_before_torch()` in custom scripts.
3. The wheel/package ships Python modules and most robot assets, but examples, checkpoints, MotionLib data, and some conversion helpers are source-checkout assets. A source checkout with Git LFS is required for packaged examples or pretrained artifacts.
4. SMPL/SMPL-H body-model assets are intentionally excluded from built distributions. Use a complete licensed asset tree and set `PROTOMOTIONS_ASSET_ROOT` when those assets are missing.
5. `resolved_configs.pt` and `resolved_configs_inference.pt` are the source of truth for trained runs; YAML sidecars are human-readable only.
6. Cross-simulator transfer is not automatic. It is expected mainly for policies explicitly trained with transfer-oriented domain randomization, especially the documented G1 deployment tracker.

## Minimal install and inspection checks

After selecting a backend environment, run:

```bash
protomotions info --json
protomotions train-agent --help
protomotions inference-agent --help
```

For a Python smoke without starting a simulator:

```python
from protomotions.robot_configs.factory import robot_config
from protomotions.simulator.factory import get_simulator_config_class
from protomotions.components.motion_lib import MotionLibConfig

print(robot_config("g1").number_of_actions)
print(get_simulator_config_class("mujoco").__name__)
print(MotionLibConfig().motion_file)
```

The bundled script `scripts/inspect_protomotions_install.py` performs the same checks and emits JSON.

## Repo-level references

- `references/quick-reference.md`: compact command, object, and file-artifact cheat sheet.
- `references/install-and-backends.md`: backend environment choices and simulator compatibility summary.
- `references/cli-and-config.md`: train/inference CLI conventions and resolved-config lifecycle.
- `references/troubleshooting.md`: cross-cutting failures for imports, assets, data, checkpoints, simulator backends, and deployment.
- `references/repo-provenance.md`: source commit, version, evidence paths, and verification baseline for this generated skill.
- `references/repo-routing-metadata.json`: structured scenario metadata used by repo-skill import tooling.

## Safety and scope boundaries

- Treat full training, simulator rollout, PyRoki retargeting, ONNX deployment, IsaacLab conversion, and real-robot control as hardware/data-dependent operations. Prefer parser/import/config checks before long runs.
- Do not run real-robot commands without explicit human authorization and an emergency-stop plan.
- Do not mutate a user's existing backend environment without permission; create a separate backend-specific environment when dependencies conflict.
- When using a package-only install, do not assume source-checkout examples or large Git LFS assets are present.
