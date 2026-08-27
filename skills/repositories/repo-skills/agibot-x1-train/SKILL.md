---
name: agibot-x1-train
description: "Guide agents through AgiBot X1 humanoid reinforcement-learning
  training, checkpoint playback, policy export, and MuJoCo sim2sim workflows
  with verified configuration contracts and explicit Isaac Gym limits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# AgiBot X1 training skill

Use this repo skill when a task involves the AgiBot X1 DH stand locomotion task,
`x1_dh_stand`, DH PPO, checkpoint discovery, interactive Isaac Gym playback,
TorchScript/ONNX policy export, or MuJoCo sim2sim validation.

## Route by intent

- **Train or modify the X1 DH PPO task:** read [training](sub-skills/training/SKILL.md).
- **Play a runner checkpoint in Isaac Gym:** read [playback](sub-skills/playback/SKILL.md).
- **Export a checkpoint to JIT or JIT to ONNX:** read [export](sub-skills/export/SKILL.md).
- **Validate an exported policy in MuJoCo:** read [sim2sim](sub-skills/sim2sim/SKILL.md).
- **Check whether this skill matches a repository revision:** read [provenance](references/repo-provenance.md).
- **Diagnose shared installation, backend, path, or artifact failures:** read [troubleshooting](references/troubleshooting.md).

Do not combine a runner checkpoint, JIT policy, and ONNX file interchangeably.
The normal handoff is:

```text
training checkpoint (.pt) -> export -> policy_dh.jit -> sim2sim
                                      -> ONNX (optional deployment artifact)
training checkpoint (.pt) -> playback (interactive Isaac Gym)
```

## Package and backend contract

This is a legacy Isaac Gym Preview 4 project rather than a CPU-only Python
library. The documented baseline is Python 3.8, PyTorch 1.13.1 with CUDA 11.7,
NumPy 1.23.x, Isaac Gym Preview 4, and the package's runtime dependencies. The
main task imports `isaacgym` through the environment, terrain, utility, and
registry chain. Isaac Gym Preview 4 is not available in the construction
runtime, so native CUDA/PhysX training, playback, source export, and the full
sim2sim script remain **BLOCKED_REQUIRED_BACKEND** until a compatible vendor
installation is supplied and verified. Never replace it with a fake module or
claim that a CPU import proves the simulator works.

MuJoCo 2.3.6 is the documented sim2sim dependency. MuJoCo XML/URDF and
model-side checks can be performed separately, but they do not substitute for
Isaac Gym task construction. Read the nearest sub-skill's backend boundary
before launching any viewer, simulator, or long-running job.

For a fresh supported installation, install Isaac Gym Preview 4 from its
vendor-distributed archive first, verify its own example, then install the
repository in editable mode. Do not copy private archive paths, credentials, or
machine-specific environment names into reports or reusable instructions.

A minimal package import check after all required dependencies are installed is:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -c "import isaacgym; import humanoid; import humanoid.envs"
```

If the second command fails with `ModuleNotFoundError: isaacgym`, stop all
native task execution and preserve the backend block. Use the bundled
sub-skill preflights for path, shape, XML, and artifact checks that do not
require importing the simulator.

## Cross-workflow operating rules

1. Pin `--task=x1_dh_stand`; it is the registered task covered by this graph.
2. Treat the X1 observation contract as fixed unless every dependent config,
   policy, exporter, checkpoint, and sim2sim assumption is updated together:
   66 history frames × 47 values = 3102 actor observations, 5 × 47 = 235 short
   history values, 3 × 73 = 219 privileged observations, and 12 actions.
3. Keep source-relative resource resolution intact. The X1 URDF, MJCF includes,
   and mesh tree must be available to the actual runtime; use preflight helpers
   to detect missing assets rather than inventing replacements.
4. Treat `logs/` paths and run/checkpoint names as explicit handoff data. The
   source uses `logs/`, while some README snippets use stale singular `log/`.
5. Start with one environment and a bounded preflight. Do not launch training,
   interactive playback, conversion, or a 100-second viewer loop as a smoke
   test.
6. Keep the hardware/backend verdict separate from CPU algorithm or serialized
   artifact checks. A successful static check is not a locomotion or robot-safety
   result.

## Bundled references and helpers

- [troubleshooting](references/troubleshooting.md) covers shared dependency,
  import, path, asset, checkpoint, and backend failures.
- [repo provenance](references/repo-provenance.md) records the source revision
  and evidence baseline for staleness checks.
- [routing metadata](references/repo-routing-metadata.json) is structured import
  metadata for the managed repository-skill router.

The four focused routes contain their own references and safe helpers. Helpers
are intentionally preflight-oriented: they do not download dependencies,
launch a viewer, start pygame, open a simulator, or run full training by
default. They must be run from arbitrary working directories with explicit
paths when a checkout or artifact location is needed.
